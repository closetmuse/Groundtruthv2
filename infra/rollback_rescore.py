"""
GroundTruth V2 — infra/rollback_rescore.py

Selective rollback of the 2026-04-19 rescore-persist pass.

Context: backfill_ctags.py --commit --rescore overwrote alert_level and
weighted_score on every signal whose rescored output differed, including
hundreds of non-structural signals whose score shifted only because the
novelty component saw a larger sibling context (701 signals over 7 days
instead of the ~50-100 daily batch used at original classify time). That
was a methodology inconsistency — live scoring uses daily novelty; the
on-disk briefs captured those live scores.

This script restores alert_level / weighted_score to their originals for
every touched signal EXCEPT those the v2.3.0 structural lane was actually
designed to elevate — signals with C16 (Struct), C17 (Siting-State), or
C18 (RatingMethod) in c_tags. Those retain the new elevation.

Tag additions (c_tags backfill) are NOT rolled back. They're still
additive/correct. Only the rescored alert_level+weighted_score are reverted
where the structural lane didn't apply.

Usage:
    python infra/rollback_rescore.py              # dry-run (default)
    python infra/rollback_rescore.py --commit     # write the rollback
"""

import argparse
import json
import re
import sqlite3
import sys

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
DB_PATH = PROJECT_ROOT + r"\groundtruth.db"
BACKFILL_TAG = "backfill:2026-04-19-fix2"
STRUCTURAL_TAGS = {"C16", "C17", "C18"}

# verification_note format written by backfill_ctags.py rescore pass:
#   "[backfill:2026-04-19-fix2] orig_alert=X orig_weighted=Y.Z; <rest>"
PROVENANCE_RE = re.compile(
    r"^\[" + re.escape(BACKFILL_TAG) + r"\] "
    r"orig_alert=([A-Za-z_.]+) "
    r"orig_weighted=([0-9.]+); "
)


def run_rollback(commit: bool) -> dict:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    c = conn.cursor()
    c.execute(
        "SELECT signal_id, c_tags, alert_level, weighted_score, verification_note, headline "
        "FROM gs_signals "
        "WHERE verification_note LIKE ?",
        (f"[{BACKFILL_TAG}]%",),
    )
    rows = c.fetchall()

    reverted = []   # (sid, cur_alert, orig_alert, cur_wt, orig_wt, headline)
    kept = []       # (sid, alert, wt, structural_tags_present, headline)
    malformed = []

    for sid, ctags_raw, cur_alert, cur_wt, vnote, hl in rows:
        try:
            tags = set(json.loads(ctags_raw or "[]"))
        except Exception:
            tags = set()
        struct_overlap = tags & STRUCTURAL_TAGS

        m = PROVENANCE_RE.match(vnote or "")
        if not m:
            malformed.append((sid, vnote[:80]))
            continue

        orig_alert = m.group(1)
        # Normalize AlertLevel.X -> X if present
        if "." in orig_alert:
            orig_alert = orig_alert.split(".")[-1]
        orig_wt = float(m.group(2))
        rest = vnote[m.end():]

        if struct_overlap:
            kept.append((sid, cur_alert, cur_wt, sorted(struct_overlap), (hl or "")[:60]))
        else:
            reverted.append((sid, cur_alert, orig_alert, cur_wt, orig_wt, (hl or "")[:60]))
            if commit:
                c.execute(
                    "UPDATE gs_signals "
                    "   SET alert_level=?, weighted_score=?, verification_note=? "
                    " WHERE signal_id=?",
                    (orig_alert, orig_wt, rest, sid),
                )

    if commit:
        conn.commit()
    conn.close()
    return {
        "total_touched": len(rows),
        "reverted":      reverted,
        "kept":          kept,
        "malformed":     malformed,
        "committed":     commit,
    }


def main():
    ap = argparse.ArgumentParser(description="Selective rollback of 2026-04-19 rescore")
    ap.add_argument("--commit", action="store_true",
                    help="Actually write the rollback (default dry-run)")
    ap.add_argument("--limit-print", type=int, default=20)
    args = ap.parse_args()

    mode = "COMMIT" if args.commit else "DRY-RUN"
    print("=" * 70)
    print(f"  rollback_rescore.py — {mode}")
    print("=" * 70)

    r = run_rollback(args.commit)
    print(f"\nTotal signals carrying {BACKFILL_TAG} rescore provenance: {r['total_touched']}")
    print(f"  KEPT rescored (have C16/C17/C18): {len(r['kept'])}")
    print(f"  REVERTED to originals (no structural tag): {len(r['reverted'])}")
    if r['malformed']:
        print(f"  Malformed verification_note entries (skipped): {len(r['malformed'])}")

    if r['kept']:
        print(f"\n--- KEPT (v2.3.0 elevation stands) — showing up to {args.limit_print} ---")
        for sid, al, wt, struct, hl in r['kept'][:args.limit_print]:
            print(f"  {sid}  {al} wt={wt:.1f}  tags={struct}")
            print(f"    {hl}")
        if len(r['kept']) > args.limit_print:
            print(f"  ... and {len(r['kept']) - args.limit_print} more")

    if r['reverted']:
        print(f"\n--- REVERTED — showing up to {args.limit_print} ---")
        for sid, ca, oa, cw, ow, hl in r['reverted'][:args.limit_print]:
            print(f"  {sid}  [{ca}->{oa}]  {cw:.1f}->{ow:.1f}")
            print(f"    {hl}")
        if len(r['reverted']) > args.limit_print:
            print(f"  ... and {len(r['reverted']) - args.limit_print} more")

    print()
    if not args.commit:
        print("DRY-RUN. Re-run with --commit to write the rollback.")
    else:
        print("COMMITTED. Reverted signals restored to original alert_level / "
              "weighted_score. Kept signals retain v2.3.0 elevation.")


if __name__ == "__main__":
    main()
