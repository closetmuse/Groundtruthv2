"""
GroundTruth V2 — GREEN classification audit
Surfaces false-negative candidates: signals the scorer put in GREEN that
may have been mis-classified. Two filters:
  1. TIER1_SOURCES (F1/F2) — primary-source journalism should rarely be GREEN
  2. KEYWORD_WATCHLIST — high-value terms that warrant review at any score

Run daily after the capture to get a short digest of "worth a second look."

Usage:
    python -m infra.audit_green                 # last 4 days
    python -m infra.audit_green --days 7        # last 7 days
    python -m infra.audit_green --save          # also write to outputs/
"""

import os
import sys
import sqlite3
import json
from datetime import date, timedelta

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "groundtruth.db")

# F-tags that mean primary-source journalism or official regulatory filing.
# These should almost never be in GREEN when they report a material event.
TIER1_F_TAGS = {"F1", "F2", "F3"}

# High-value terms — if any appear in a GREEN signal, it warrants review
# regardless of source tier. Kept focused on deal-transmission mechanisms
# and binary-event triggers. Edit this list as the watch frame evolves.
KEYWORD_WATCHLIST = [
    # Named deals / sponsors on the pipeline
    "venture global", " vg ", "cp2 ", "plaquemines", "delfin",
    "commonwealth lng", "sabine pass", "cheniere", "corpus christi",
    "nextdecade", "cameron lng",
    # LNG arbitrage and export-auth mechanisms
    "jkm ", " ttf ", "waha basis", "feedgas",
    "doe export", "non-fta", "lng moratori", "export authoriz",
    "pre-filing waiver", "draft environmental impact",
    # Power axis mechanisms
    "feoc", "obbba", "levelten", "ppa price", "record ppa",
    "curtailment", "negative price hour", "peak discount",
    "large load interconnect", "interconnection queue",
    "cost allocation", "queue reform",
    # DC axis mechanisms
    "hyperscaler", "anthropic", "openai", "mythos",
    "ai capex", "ai revenue", "arr ",
    "coreweave", "gpu financing", "behind-the-meter",
    "data center peril", "dc cat bond",
    # Financing mechanisms (today's watch thread)
    "securitisation", "securitization", "private credit",
    "bdc ", "blue owl", "wahba",
    # Binary events Sri tracks
    "fomc", "rate decision", "commission meeting",
    "docket", "nopr", "final rule",
]


def load_recent_signals(days: int) -> list[dict]:
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT signal_id, source_name, headline, summary, c_tags, f_tags,
                        alert_level, weighted_score, raw_score, created_at,
                        affected_deals
                 FROM gs_signals WHERE created_at >= ?
                 ORDER BY created_at DESC""", (cutoff,))
    cols = ["signal_id", "source_name", "headline", "summary", "c_tags",
            "f_tags", "alert_level", "weighted_score", "raw_score",
            "created_at", "affected_deals"]
    rows = [dict(zip(cols, r)) for r in c.fetchall()]
    conn.close()
    return rows


def is_tier1(sig: dict) -> bool:
    try:
        f_tags = set(json.loads(sig["f_tags"] or "[]"))
    except Exception:
        return False
    return bool(f_tags & TIER1_F_TAGS)


def matched_keywords(sig: dict) -> list[str]:
    text = ((sig["headline"] or "") + " " + (sig["summary"] or "")).lower()
    return [kw for kw in KEYWORD_WATCHLIST if kw in text]


def categorize_green(sig: dict) -> str:
    """Classify a GREEN signal by its likely failure mode."""
    w = sig["weighted_score"] or 0
    if not sig["c_tags"] and not sig["f_tags"]:
        return "CLASSIFIER-DROP"   # c_tags=None means infra-relevance gate killed it
    if w >= 40:
        return "NEAR-AMBER"         # just below threshold, boundary case
    if w >= 20:
        return "MID-GREEN"          # moderate score, probably correct
    return "LOW-GREEN"              # noise


def run_audit(days: int = 4) -> dict:
    signals = load_recent_signals(days)
    greens = [s for s in signals if s["alert_level"] == "GREEN"]

    tier1_greens = [s for s in greens if is_tier1(s)]
    keyword_greens = []
    for s in greens:
        hits = matched_keywords(s)
        if hits:
            keyword_greens.append((s, hits))

    # Cross-section — highest priority
    both = []
    kw_lookup = {s["signal_id"]: hits for s, hits in keyword_greens}
    for s in tier1_greens:
        if s["signal_id"] in kw_lookup:
            both.append((s, kw_lookup[s["signal_id"]]))

    return {
        "days": days,
        "total_signals": len(signals),
        "total_green": len(greens),
        "tier1_green": tier1_greens,
        "keyword_green": keyword_greens,
        "both": both,
    }


def format_report(audit: dict) -> str:
    lines = []
    total = audit["total_signals"]
    green = audit["total_green"]
    lines.append(f"GREEN AUDIT — last {audit['days']} days "
                 f"({green}/{total} signals in GREEN, "
                 f"{green/total*100:.0f}% of tape)")
    lines.append("=" * 80)
    lines.append("")

    # Highest priority: F1/F2 source AND keyword match
    lines.append(f"HIGH PRIORITY — Tier-1 source with watchlist keyword "
                 f"({len(audit['both'])} signals)")
    lines.append("-" * 80)
    if not audit["both"]:
        lines.append("  (none)")
    for s, hits in sorted(audit["both"],
                          key=lambda x: -(x[0]["weighted_score"] or 0)):
        cat = categorize_green(s)
        lines.append(f"  [{cat:14s}] {s['signal_id']}  "
                     f"weighted={s['weighted_score']:.1f}  "
                     f"[{s['source_name']}]")
        lines.append(f"      {s['headline'][:100]}")
        lines.append(f"      keyword hits: {hits[:5]}")
        lines.append("")

    # Secondary: F1/F2 source, no keyword match
    tier1_only = [s for s in audit["tier1_green"]
                  if s["signal_id"] not in
                  {x[0]["signal_id"] for x in audit["both"]}]
    lines.append(f"TIER-1 SOURCE GREENS — F1/F2 signals in GREEN, no watchlist hit "
                 f"({len(tier1_only)} signals, top 15 by score)")
    lines.append("-" * 80)
    tier1_only_sorted = sorted(tier1_only,
                               key=lambda s: -(s["weighted_score"] or 0))
    for s in tier1_only_sorted[:15]:
        cat = categorize_green(s)
        lines.append(f"  [{cat:14s}] {s['signal_id']}  "
                     f"weighted={s['weighted_score']:.1f}  "
                     f"[{s['source_name'][:18]}]  {s['headline'][:80]}")
    if len(tier1_only_sorted) > 15:
        lines.append(f"  ... and {len(tier1_only_sorted) - 15} more")
    lines.append("")

    # Secondary: keyword match, non-tier-1 source
    kw_only = [(s, hits) for s, hits in audit["keyword_green"]
               if s["signal_id"] not in
               {x[0]["signal_id"] for x in audit["both"]}]
    lines.append(f"WATCHLIST KEYWORD GREENS — non-tier-1 source "
                 f"({len(kw_only)} signals, top 15 by score)")
    lines.append("-" * 80)
    kw_only_sorted = sorted(kw_only,
                            key=lambda x: -(x[0]["weighted_score"] or 0))
    for s, hits in kw_only_sorted[:15]:
        cat = categorize_green(s)
        lines.append(f"  [{cat:14s}] {s['signal_id']}  "
                     f"weighted={s['weighted_score']:.1f}  "
                     f"[{s['source_name'][:18]}]  {s['headline'][:80]}")
        lines.append(f"      hits: {hits[:3]}")
    if len(kw_only_sorted) > 15:
        lines.append(f"  ... and {len(kw_only_sorted) - 15} more")
    lines.append("")

    # Summary stats
    lines.append("SUMMARY")
    lines.append("-" * 80)
    lines.append(f"  Total GREEN signals:              {green}")
    lines.append(f"  Tier-1 source in GREEN:           {len(audit['tier1_green'])}")
    lines.append(f"  Watchlist keyword in GREEN:       {len(audit['keyword_green'])}")
    lines.append(f"  Cross-section (highest priority): {len(audit['both'])}")
    lines.append("")
    lines.append("If HIGH-PRIORITY list is non-empty, eyeball each — likely "
                 "false-negative or classifier gap.")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    days = 4
    save = False
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    if "--save" in sys.argv:
        save = True

    audit = run_audit(days=days)
    report = format_report(audit)
    print(report)

    if save:
        out = os.path.join(PROJECT_ROOT, "outputs",
                           f"green_audit_{date.today().isoformat()}.txt")
        with open(out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nSaved to {out}")
