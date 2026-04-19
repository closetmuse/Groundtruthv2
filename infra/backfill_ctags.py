"""
GroundTruth V2 — infra/backfill_ctags.py

Additive C-tag backfill for stored signals. Applies the current classifier
(gs/classify.py) to signals already in the DB and UNIONs newly-matched tags
with their existing c_tags. Never removes existing tags. Never modifies
alert_level or weighted_score — the contemporaneous record of what scored
when is preserved.

Why this exists:
    The 2026-04-19 classifier fix #2 added C16 (Struct), C17 (Siting-State),
    C18 (RatingMethod) plus a word-boundary abbreviation matcher. Existing
    DB signals from before that date lack the new tags, so cluster queries
    (e.g. "show me all C16 signals from the past 7 days") miss them. This
    script backfills the tags additively so clustering works without
    rewriting the contemporaneous scoring record.

What it touches:
    - c_tags           — UNIONed with newly-classified tags
    - classifier_model — appended with "|backfill:<date>"
    - (optional --rescore) — also writes weighted_score/alert_level, with
                             original preserved in verification_note. Off by
                             default to keep the historical scoring intact.

Usage:
    python infra/backfill_ctags.py --dry-run                 # default scope: last 14 days
    python infra/backfill_ctags.py --days 30 --dry-run
    python infra/backfill_ctags.py --commit                  # write tag-only changes
    python infra/backfill_ctags.py --commit --rescore        # tag + rescore (preserves originals)

Idempotency:
    Re-running is safe. UNION is an idempotent operation, and the classifier
    is deterministic, so a second pass with identical code produces no diffs.
"""

import argparse
import json
import sqlite3
import sys
from datetime import date, timedelta

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = PROJECT_ROOT + r"\groundtruth.db"
BACKFILL_TAG = "backfill:2026-04-19-fix2"


def _parse_tags(raw) -> list:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def run_backfill(days: int, commit: bool, rescore: bool) -> dict:
    from gs.classify import classify_item
    from ge.scorer import score_signal
    from core.schema import Signal

    cutoff = (date.today() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT signal_id, source_type, status, headline, summary, source_name,
               c_tags, f_tags, t_tag, created_at, affected_deals,
               weighted_score, alert_level, classifier_model, verification_note,
               publication_date
        FROM gs_signals
        WHERE date(created_at) >= ?
          AND status != 'FILTERED'
    """, (cutoff,))
    rows = c.fetchall()

    tag_changes = []     # (signal_id, added_tags, before, after, headline)
    rescore_changes = [] # (signal_id, before_alert, after_alert, before_wt, after_wt, headline)
    unchanged = 0
    total = len(rows)

    # Precompute the union tags for every signal ONCE, up front.
    # Previously this was nested inside the per-signal scoring loop making
    # the work O(n^2). Now O(n) classify calls + O(n) scoring passes.
    print(f"Pre-classifying {total} signals...")
    per_sid = {}  # signal_id -> (row, union_tags, added_tags)
    for r in rows:
        sid = r[0]
        existing = _parse_tags(r[6])
        reclassified = classify_item({
            "headline": r[3] or "",
            "summary": r[4] or "",
            "source_name": r[5] or "",
            "publication_date": r[15] or "",
            "c_tags": [],
        })
        new_tags = _parse_tags(reclassified.get("c_tags"))
        union = sorted(set(existing) | set(new_tags))
        added = sorted(set(new_tags) - set(existing))
        per_sid[sid] = (r, union, added)

    # Build sibling Signal list ONCE from precomputed unions.
    all_siblings = [
        Signal(
            signal_id=r[0], source_type=r[1], status=r[2],
            headline=r[3] or "", summary=r[4] or "", source_name=r[5] or "",
            c_tags=json.dumps(per_sid[r[0]][1]),
            f_tags=r[7] or "[]", t_tag=r[8] or "T2", created_at=r[9],
            affected_deals=r[10] or "[]",
        )
        for r in rows
    ]
    print(f"Scoring {total} signals against precomputed siblings...")

    for r in rows:
        sid = r[0]
        _, union, added = per_sid[sid]
        (_, stype, status, hl, summ, src, ctags_raw, ftags, ttag,
         created, deals, wt_score, alert, model, vnote, pubdate) = r

        existing = _parse_tags(ctags_raw)
        tag_diff = bool(added)

        if tag_diff and commit:
            existing_model = (model or "").strip()
            if BACKFILL_TAG not in existing_model:
                new_model = (existing_model + "|" + BACKFILL_TAG).strip("|")
            else:
                new_model = existing_model
            c.execute(
                "UPDATE gs_signals SET c_tags=?, classifier_model=? WHERE signal_id=?",
                (json.dumps(union), new_model, sid),
            )

        if tag_diff:
            tag_changes.append((sid, added, existing, union, (hl or "")[:70]))
        else:
            unchanged += 1

        if tag_diff or rescore:
            sig = Signal(
                signal_id=sid, source_type=stype, status=status,
                headline=hl or "", summary=summ or "", source_name=src or "",
                c_tags=json.dumps(union), f_tags=ftags or "[]",
                t_tag=ttag or "T2", created_at=created,
                affected_deals=deals or "[]",
            )
            scored = score_signal(sig, current_regime="R0",
                                  recent_signals=all_siblings)
            new_alert = str(scored.alert_level).split(".")[-1]
            new_wt = scored.weighted_score
            old_alert = alert or "GREEN"
            old_wt = wt_score or 0.0

            if new_alert != old_alert or abs(new_wt - old_wt) > 0.5:
                rescore_changes.append(
                    (sid, old_alert, new_alert, old_wt, new_wt, (hl or "")[:70])
                )
                if commit and rescore:
                    provenance = (
                        f"[{BACKFILL_TAG}] orig_alert={old_alert} "
                        f"orig_weighted={old_wt:.1f}; "
                    )
                    new_vnote = provenance + (vnote or "")
                    c.execute("""
                        UPDATE gs_signals
                           SET alert_level=?, weighted_score=?, verification_note=?
                         WHERE signal_id=?
                    """, (new_alert, new_wt, new_vnote, sid))

    if commit:
        conn.commit()
    conn.close()

    return {
        "total":             total,
        "tag_changes":       tag_changes,
        "rescore_changes":   rescore_changes,
        "unchanged":         unchanged,
        "committed":         commit,
        "rescore_persisted": commit and rescore,
    }


def main():
    ap = argparse.ArgumentParser(description="Additive c_tag backfill")
    ap.add_argument("--days", type=int, default=14,
                    help="Backfill window in days (default 14)")
    ap.add_argument("--commit", action="store_true",
                    help="Actually write changes (default dry-run)")
    ap.add_argument("--rescore", action="store_true",
                    help="Also persist rescored alert_level / weighted_score "
                         "(originals preserved in verification_note). "
                         "Off by default — rescore preview always shown.")
    ap.add_argument("--limit-print", type=int, default=30,
                    help="Max rows to print per table (default 30)")
    args = ap.parse_args()

    mode = "COMMIT" if args.commit else "DRY-RUN"
    mode_rescore = "+ RESCORE PERSIST" if (args.commit and args.rescore) else ""
    print("=" * 70)
    print(f"  backfill_ctags.py — {mode} {mode_rescore}")
    print(f"  Window: last {args.days} days")
    print("=" * 70)

    r = run_backfill(args.days, args.commit, args.rescore)

    print(f"\nScanned: {r['total']} signals")
    print(f"Tag diffs: {len(r['tag_changes'])}")
    print(f"Unchanged: {r['unchanged']}")
    if r['tag_changes']:
        print(f"\n--- tag additions (showing up to {args.limit_print}) ---")
        for sid, added, before, after, hl in r['tag_changes'][:args.limit_print]:
            print(f"  {sid}  +{added}  ({len(before)}->{len(after)} tags)")
            print(f"    {hl}")
        if len(r['tag_changes']) > args.limit_print:
            print(f"  ... and {len(r['tag_changes']) - args.limit_print} more")

    print(f"\nRescore preview (not persisted unless --rescore): "
          f"{len(r['rescore_changes'])} would shift")
    if r['rescore_changes']:
        print(f"\n--- alert-level shifts under v2.3.0 (showing up to {args.limit_print}) ---")
        for sid, oa, na, ow, nw, hl in r['rescore_changes'][:args.limit_print]:
            arrow = "UP" if nw > ow else "DOWN"
            print(f"  {sid}  [{oa}->{na}]  {ow:.1f}->{nw:.1f} {arrow}")
            print(f"    {hl}")
        if len(r['rescore_changes']) > args.limit_print:
            print(f"  ... and {len(r['rescore_changes']) - args.limit_print} more")

    print()
    if not args.commit:
        print("DRY-RUN — no changes persisted. Re-run with --commit to write.")
    elif not args.rescore:
        print("COMMITTED tag-only changes. Historical alert_level preserved.")
        print("To also persist rescored alert_level, re-run with --commit --rescore.")
    else:
        print("COMMITTED tag + rescore. Original alert_level preserved in "
              "verification_note as 'orig_alert=X orig_weighted=Y'.")


if __name__ == "__main__":
    main()
