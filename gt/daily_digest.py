# GT — Daily News Digest Generator
# Reads today's ACTIVE signals from the GroundTruth V2 SQLite database
# and produces a structured digest for email or terminal display.
# Last Updated: April 13 2026

import sys
import os
import json
import sqlite3
import argparse
from datetime import datetime, date, timedelta
from collections import Counter

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
DB_PATH = os.path.join(PROJECT_ROOT, "groundtruth.db")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ── C-TAG LABELS ─────────────────────────────────────────────────────────────

CTAG_NAMES = {
    "C01": "Macro/Rates", "C02": "Regulatory", "C03": "Geopolitical",
    "C04": "Nuclear", "C05": "Oil & Gas", "C06": "Renewables/Grid",
    "C07": "Banking/Finance", "C08": "Commodities", "C09": "Construction",
    "C10": "BESS/Storage", "C11": "Data Centers", "C12": "Credit/BDC",
    "C13": "Emerging Markets", "C14": "Digital Infra", "C15": "Utilities/Tx",
}

REGIME_NAMES = {
    "R0": "Compound Stress", "R1": "Stagflation",
    "R2": "Rate Shock", "R3": "Demand Shock", "R4": "Stable Growth",
}


# ── DATABASE QUERIES ─────────────────────────────────────────────────────────

def _connect():
    return sqlite3.connect(DB_PATH)


def _fetch_signals(target_date: str) -> list[dict]:
    """Fetch ACTIVE signals for the target date. Falls back to 48h window."""
    conn = _connect()
    conn.row_factory = sqlite3.Row

    query = """
        SELECT id, signal_id, headline, summary, second_order,
               alert_level, c_tags, f_tags, t_tag, o_tag,
               source_type, source_name, created_at, publication_date,
               anchor_commodity, anchor_value, anchor_unit,
               anchor_delta_7d, anchor_delta_30d, anchor_delta_90d,
               weighted_score, raw_score, affected_deals,
               pipeline_risk_alert, risk_alert_rationale,
               opportunity_alert, opportunity_sector,
               theme_tags, regime_at_score
        FROM gs_signals
        WHERE status = 'ACTIVE'
          AND created_at >= ?
        ORDER BY
            CASE alert_level WHEN 'RED' THEN 1 WHEN 'AMBER' THEN 2 ELSE 3 END,
            weighted_score DESC
    """

    rows = conn.execute(query, (f"{target_date} 00:00:00",)).fetchall()

    # If thin results, widen to 48h
    if len(rows) < 5:
        prev = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        rows = conn.execute(query, (f"{prev} 00:00:00",)).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def _fetch_regime(target_date: str) -> str:
    """Get the regime code from the latest fetch run."""
    conn = _connect()
    row = conn.execute(
        "SELECT regime_code FROM gs_fetch_runs WHERE started_at >= ? ORDER BY started_at DESC LIMIT 1",
        (f"{target_date} 00:00:00",)
    ).fetchone()
    conn.close()
    return row[0] if row else "R0"


def _fetch_price_snapshot(target_date: str) -> dict:
    """Get the latest price snapshot for the date."""
    conn = _connect()
    row = conn.execute(
        "SELECT series_data, deltas_7d, deltas_30d, deltas_90d, breaches FROM gs_price_snapshots WHERE snapshot_date = ? ORDER BY id DESC LIMIT 1",
        (target_date,)
    ).fetchone()
    conn.close()
    if not row:
        return {}
    return {
        "series": json.loads(row[0]) if row[0] else {},
        "d7": json.loads(row[1]) if row[1] else {},
        "d30": json.loads(row[2]) if row[2] else {},
        "d90": json.loads(row[3]) if row[3] else {},
        "breaches": json.loads(row[4]) if row[4] else [],
    }


def _fetch_binary_events() -> list[dict]:
    """Get open binary events."""
    conn = _connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM gt_binary_events WHERE status = 'OPEN'").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── DIGEST BUILDER ───────────────────────────────────────────────────────────

def _parse_tags(tag_str: str) -> list[str]:
    if not tag_str:
        return []
    try:
        return json.loads(tag_str)
    except (json.JSONDecodeError, TypeError):
        return [t.strip() for t in tag_str.split(",") if t.strip()]


def build_digest(target_date: str) -> str:
    signals = _fetch_signals(target_date)
    regime_code = _fetch_regime(target_date)
    prices = _fetch_price_snapshot(target_date)
    binary_events = _fetch_binary_events()

    red = [s for s in signals if s["alert_level"] == "RED"]
    amber = [s for s in signals if s["alert_level"] == "AMBER"]
    green = [s for s in signals if s["alert_level"] == "GREEN"]

    regime_label = REGIME_NAMES.get(regime_code.split()[0] if regime_code else "R0", regime_code)

    lines = []

    # ── HEADER
    lines.append(f"GROUNDTRUTH DAILY DIGEST — {target_date}")
    lines.append(f"{len(signals)} signals | {len(red)} RED | {len(amber)} AMBER | {len(green)} GREEN")
    lines.append("")

    # ── 1. REGIME PULSE
    lines.append("REGIME PULSE")

    # Collect dominant c_tags
    all_ctags = []
    for s in signals:
        all_ctags.extend(_parse_tags(s.get("c_tags", "")))
    ctag_counts = Counter(all_ctags)
    top_sectors = ctag_counts.most_common(3)
    sector_str = ", ".join(f"{CTAG_NAMES.get(t, t)}" for t, _ in top_sectors)

    regime_display = regime_code if regime_code else "R0"
    lines.append(
        f"Active regime: {regime_display}. "
        f"Today's signal flow dominated by {sector_str}. "
        f"{len(red)} RED alerts flagged — "
        f"{'elevated stress across multiple vectors' if len(red) >= 3 else 'concentrated risk pockets'}."
    )
    if binary_events:
        be_str = ", ".join(
            f"{e.get('event_name') or e.get('event_id', 'TBD')} ({e.get('deadline', '?')})"
            for e in binary_events[:3]
        )
        lines.append(f"Pending binary events: {be_str}.")
    lines.append("")

    # ── 2. TOP SIGNALS BY ALERT LEVEL
    lines.append("TOP SIGNALS BY ALERT LEVEL")
    lines.append("")

    if red:
        lines.append(f"  RED ({len(red)})")
        for s in red[:5]:
            so = (s.get("second_order") or "No second-order analysis").strip()
            lines.append(f"  * {s['headline'][:90]}")
            lines.append(f"    {so[:150]}")
        lines.append("")

    if amber:
        lines.append(f"  AMBER ({len(amber)})")
        for s in amber[:8]:
            so = (s.get("second_order") or "").strip()
            watch = so[:100] if so else s.get("summary", "")[:100]
            lines.append(f"  - {s['headline'][:85]}  |  {watch}")
        if len(amber) > 8:
            lines.append(f"  ... and {len(amber) - 8} more AMBER signals")
        lines.append("")

    if green:
        # Grouped summary
        green_sources = Counter(s.get("source_name", "?") for s in green)
        top_green = green_sources.most_common(3)
        src_str = ", ".join(f"{n} ({c})" for n, c in top_green)
        green_ctags = []
        for s in green:
            green_ctags.extend(_parse_tags(s.get("c_tags", "")))
        green_sectors = Counter(green_ctags).most_common(3)
        gsec_str = ", ".join(CTAG_NAMES.get(t, t) for t, _ in green_sectors)
        lines.append(f"  GREEN ({len(green)})")
        lines.append(f"  Routine flow across {gsec_str}. Top sources: {src_str}.")
        lines.append("")

    # ── 3. SECTOR BREAKDOWN
    lines.append("SECTOR BREAKDOWN")
    red_amber_ctags = []
    for s in red + amber:
        red_amber_ctags.extend(_parse_tags(s.get("c_tags", "")))
    ra_counts = Counter(red_amber_ctags)

    hot_zones = []
    for tag, count in ra_counts.most_common(8):
        label = CTAG_NAMES.get(tag, tag)
        marker = " ** HOT ZONE **" if count >= 3 else ""
        lines.append(f"  {tag} {label}: {count} RED/AMBER signals{marker}")
        if count >= 3:
            hot_zones.append(label)
    lines.append("")

    # ── 4. DEAL WATCH HITS
    lines.append("DEAL WATCH HITS")
    deal_hits = []
    for s in signals:
        deals = s.get("affected_deals") or ""
        if deals and deals.strip() and deals.strip() != "[]":
            deal_hits.append(s)
        # Also check pipeline_risk_alert
        if s.get("pipeline_risk_alert") and s.get("risk_alert_rationale"):
            deal_hits.append(s)

    if deal_hits:
        seen = set()
        for s in deal_hits:
            key = s["id"]
            if key in seen:
                continue
            seen.add(key)
            rationale = (s.get("risk_alert_rationale") or s.get("affected_deals") or "")[:80]
            lines.append(f"  [{s['alert_level']}] {s['headline'][:70]}  |  {rationale}")
    else:
        lines.append("  No direct deal name matches today. Tier 2 matching pending geography data.")
    lines.append("")

    # ── 5. PRICE MOVES
    lines.append("PRICE MOVES")
    if prices and prices.get("series"):
        KEY_SERIES = [
            "wti_usd_bbl", "brent_usd_bbl", "henry_hub_usd_mmbtu",
            "ust_10y_pct", "sofr_pct", "bbb_oas_bps", "hy_spread_bps",
            "aluminum_usd_mt", "copper_usd_mt",
            "steel_hrc_usd_st", "steel_hrc_index",
        ]
        d7 = prices.get("d7", {})
        d30 = prices.get("d30", {})
        d90 = prices.get("d90", {})

        for key in KEY_SERIES:
            info = prices["series"].get(key, {})
            if not info:
                continue
            val = info.get("value")
            unit = info.get("unit", "")
            delta7 = d7.get(key)
            delta30 = d30.get(key)
            delta90 = d90.get(key)
            if val is None:
                continue

            flag = ""
            for d, label in [(delta7, "7d"), (delta30, "30d"), (delta90, "90d")]:
                if d is not None and abs(d) > 5:
                    flag = f" !! {label} move"
                    break

            d7s = f"{delta7:+.1f}%" if delta7 is not None else "n/a"
            d30s = f"{delta30:+.1f}%" if delta30 is not None else "n/a"
            d90s = f"{delta90:+.1f}%" if delta90 is not None else "n/a"

            lines.append(f"  {key}: {val} {unit}  |  7d {d7s}  30d {d30s}  90d {d90s}{flag}")

        if prices.get("breaches"):
            lines.append(f"  Threshold breaches: {', '.join(str(b) for b in prices['breaches'][:5])}")
    else:
        lines.append("  No price snapshot available for this date.")
    lines.append("")

    # ── 6. ONE NON-OBVIOUS THING
    lines.append("ONE NON-OBVIOUS THING")

    # Pick the signal with the richest second_order that has infra-relevant c_tags
    # Prefer RED, then AMBER with deal hits, then highest weighted_score
    INFRA_CTAGS = {"C02", "C05", "C06", "C08", "C09", "C11", "C12", "C15"}
    best_so = None
    best_score = 0
    best_headline = ""
    for s in red + amber[:20]:
        so = (s.get("second_order") or "").strip()
        if not so or len(so) < 40:
            continue
        tags = set(_parse_tags(s.get("c_tags", "")))
        infra_overlap = len(tags & INFRA_CTAGS)
        has_deal = bool(s.get("pipeline_risk_alert"))
        score = (
            len(so)
            + (100 if s["alert_level"] == "RED" else 0)
            + (infra_overlap * 30)
            + (50 if has_deal else 0)
        )
        if score > best_score:
            best_score = score
            best_so = so
            best_headline = s["headline"]

    if best_so:
        lines.append(f"  From: {best_headline[:80]}")
        lines.append(f"  {best_so[:300]}")
    else:
        lines.append("  Insufficient second-order data for today's signals.")
    lines.append("")

    # ── FOOTER
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M ET')}  |  Regime: {regime_display}")
    lines.append(f"Signals DB: {len(signals)} active  |  Binary events: {len(binary_events)} open")

    return "\n".join(lines)


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GroundTruth Daily Digest")
    parser.add_argument("--date", type=str, default=None,
                        help="Target date YYYY-MM-DD (default: today)")
    args = parser.parse_args()

    target_date = args.date or date.today().strftime("%Y-%m-%d")

    print(f"Building digest for {target_date}...\n")

    digest = build_digest(target_date)

    # Print to terminal
    print(digest)

    # Save to file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"digest_{target_date}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(digest)

    print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
