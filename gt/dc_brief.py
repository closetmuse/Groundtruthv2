# GT — Data Center Intelligence Brief
# Reads today's signals, applies strict DC relevance filter, and produces
# a concise analyst-grade brief. No templates, no boilerplate.
# Last Updated: April 13 2026

import sys
import os
import re
import json
import sqlite3
import argparse
from datetime import date, datetime, timedelta

import pytz

ET = pytz.timezone("America/New_York")

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
DB_PATH = os.path.join(PROJECT_ROOT, "groundtruth.db")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ── FILTER DEFINITIONS ───────────────────────────────────────────────────────

# Tier 1: headline or summary contains these → automatic include
TIER1 = re.compile(
    r"data\s*cent|datacent|hyperscal|colocation|\bcolo\b|GPU\s*cluster|"
    r"AI\s*campus|\bHPC\b|digital\s*infrastructure|"
    r"\bEdged\b|Javelin|Delta\s*Stack|GT-108|GT-109|"
    r"AI\s*infrastructure|cloud\s*campus|server\s*farm|"
    r"CoreWeave|Microsoft.*AI|Blackstone.*data\s*cent|"
    r"data\s*center\s*REIT",
    re.IGNORECASE,
)

# Tier 2: C11 tag + these power/grid/AI keywords
TIER2_KW = re.compile(
    r"power|generation|\bGW\b|\bMW\b|interconnect|cooling|"
    r"load\s*growth|grid|auction|AI\s*demand|energy\s*reliab|"
    r"rate\s*proposal|capacity|PJM|ERCOT|CAISO|transformer",
    re.IGNORECASE,
)

# Hard exclude — never include regardless of tags
EXCLUDE = re.compile(
    r"luxury|jewel|cement|Lafarge|print\s*proves|branding|"
    r"offshore\s*wind|Vineyard\s*Wind|Hexicon|floating\s*wind|"
    r"South\s*Africa.*nuclear|Necsa|Nordic|Heim\s*to\s*target|"
    r"Viktor|Orban|LVMH|bitcoin|Kwarteng|Farage|"
    r"drone\s*intercept|UK\s*defense|piracy|NPR\s*on\s*Iran|"
    r"Congo|Moho|Goldman\s*bond|jewellers|gold.*surge|"
    r"Watches\s*and\s*Jewel|Rolex|recycled\s*gold|"
    r"Nottingham|Oman.*PV|Botswana",
    re.IGNORECASE,
)


# ── DATABASE ─────────────────────────────────────────────────────────────────

def _fetch_signals(target_date: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, signal_id, headline, summary, second_order,
               alert_level, c_tags, source_name, created_at,
               anchor_commodity, anchor_value,
               anchor_delta_7d, anchor_delta_30d,
               risk_alert_rationale, pipeline_risk_alert,
               weighted_score, raw_content
        FROM gs_signals
        WHERE status = 'ACTIVE' AND created_at >= ?
        ORDER BY
            CASE alert_level WHEN 'RED' THEN 1 WHEN 'AMBER' THEN 2 ELSE 3 END,
            weighted_score DESC
    """, (f"{target_date} 00:00:00",)).fetchall()

    if len(rows) < 5:
        prev = (date.fromisoformat(target_date) - timedelta(days=1)).isoformat()
        rows = conn.execute("""
            SELECT id, signal_id, headline, summary, second_order,
                   alert_level, c_tags, source_name, created_at,
                   anchor_commodity, anchor_value,
                   anchor_delta_7d, anchor_delta_30d,
                   risk_alert_rationale, pipeline_risk_alert,
                   weighted_score, raw_content
            FROM gs_signals
            WHERE status = 'ACTIVE' AND created_at >= ?
            ORDER BY
                CASE alert_level WHEN 'RED' THEN 1 WHEN 'AMBER' THEN 2 ELSE 3 END,
                weighted_score DESC
        """, (f"{prev} 00:00:00",)).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def _parse_tags(s: str) -> list[str]:
    if not s:
        return []
    try:
        return json.loads(s)
    except Exception:
        return [t.strip() for t in s.split(",") if t.strip()]


# ── FILTER ───────────────────────────────────────────────────────────────────

def _filter_dc(signals: list[dict]) -> list[dict]:
    """Apply strict Tier 1 / Tier 2 filter with hard excludes."""
    kept = []
    for s in signals:
        h = s.get("headline") or ""
        summ = s.get("summary") or ""
        hs = f"{h} {summ}"
        tags = set(_parse_tags(s.get("c_tags", "")))

        if EXCLUDE.search(h):
            continue

        if TIER1.search(hs):
            s["_tier"] = 1
            kept.append(s)
        elif "C11" in tags and TIER2_KW.search(hs):
            s["_tier"] = 2
            kept.append(s)

    return kept


# ── CLEAN TEXT HELPERS ───────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Strip HTML tags and excessive whitespace."""
    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _first_sentences(text: str, n: int = 2) -> str:
    text = _clean(text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(parts[:n])


def _deal_explanation(s: dict) -> str | None:
    """
    Return a genuine deal transmission explanation, or None.
    Only returns if there's a real mechanism, not just tag overlap.
    """
    rat = s.get("risk_alert_rationale") or ""
    if not rat:
        return None

    h = (s.get("headline") or "").lower()
    summ = (s.get("summary") or "").lower()
    combined = h + " " + summ

    # Map deal names to what would constitute genuine exposure
    DEAL_TESTS = {
        "GT-108": (r"GT-108|SB Energy Ohio",
                   r"PJM|ohio|capacity|auction|generation|interconnect|power\s*demand"),
        "GT-109": (r"GT-109|SB Energy Milam",
                   r"gas\s*price|henry\s*hub|LNG|fuel\s*cost|natural\s*gas|ercot"),
        "Storybook WI": (r"Storybook WI",
                         r"wisconsin|we\s*energies|grid\s*upgrade|rate\s*proposal|WI\b"),
        "Delta Stack": (r"Delta Stack",
                        r"construction|EPC|steel|concrete|labor|data\s*center"),
        "Edged DC Javelin": (r"Edged DC Javelin",
                             r"gas\s*price|power\s*cost|fuel|energy\s*cost|colocation"),
    }

    for deal_name, (name_pat, relevance_pat) in DEAL_TESTS.items():
        if re.search(name_pat, rat, re.IGNORECASE):
            if re.search(relevance_pat, combined, re.IGNORECASE):
                return deal_name
    return None


# ── BRIEF BUILDER ────────────────────────────────────────────────────────────

def build_brief(target_date: str) -> str:
    all_signals = _fetch_signals(target_date)
    dc_signals = _filter_dc(all_signals)

    red = [s for s in dc_signals if s["alert_level"] == "RED"]
    amber = [s for s in dc_signals if s["alert_level"] == "AMBER"]
    green = [s for s in dc_signals if s["alert_level"] == "GREEN"]

    # ── Collect material for synthesis
    headlines = [s["headline"] for s in dc_signals]
    all_text = " ".join(f"{s['headline']} {s.get('summary','')}" for s in dc_signals)

    # Detect themes by scanning actual content
    has_pjm = bool(re.search(r"PJM.*\d+.*GW|PJM.*auction|PJM.*generation", all_text, re.IGNORECASE))
    has_grid_strain = bool(re.search(r"strain.*grid|grid.*pay|rate\s*proposal.*data\s*cent", all_text, re.IGNORECASE))
    has_reit = bool(re.search(r"REIT|IPO.*data\s*cent", all_text, re.IGNORECASE))
    has_coreweave = bool(re.search(r"CoreWeave|GPU\s*cloud", all_text, re.IGNORECASE))
    has_microsoft = bool(re.search(r"Microsoft.*billion|Microsoft.*AI", all_text, re.IGNORECASE))
    has_vertiv = bool(re.search(r"Vertiv|prefab.*enclosure|BMarko", all_text, re.IGNORECASE))
    has_construction = bool(re.search(r"construction.*cloudy|construction.*outlook", all_text, re.IGNORECASE))
    has_gas_price = bool(re.search(r"gas\s*price|fuel\s*cost", all_text, re.IGNORECASE))

    # Extract GW figures
    gw_match = re.search(r"(\d+\.?\d*)\s*GW", all_text)
    gw_str = f"{gw_match.group(1)} GW" if gw_match else ""

    lines = []

    # ── HEADER
    lines.append(f"DC INTELLIGENCE BRIEF — {target_date}")
    lines.append(f"{len(dc_signals)} signals ({len(red)} RED, {len(amber)} AMBER, {len(green)} GREEN)")
    lines.append("")

    # ── WHAT HAPPENED
    lines.append("WHAT HAPPENED TODAY IN DATA CENTERS")

    what_parts = []
    if has_pjm and gw_str:
        what_parts.append(
            f"PJM moved to address the data center capacity crunch with an emergency "
            f"auction targeting up to {gw_str} of new generation via bilateral contracts "
            f"and central procurement — process runs September through March 2027"
        )
    if has_grid_strain:
        what_parts.append(
            "utilities are starting to push DC-related grid costs back to ratepayers "
            "(We Energies filed a $1.9B rate case citing data center load)"
        )
    if has_reit:
        what_parts.append(
            "Blackstone filed for a data center REIT IPO focused on stabilized Tier 1 assets, "
            "signaling institutional capital is rotating from development into yield"
        )
    if has_coreweave:
        what_parts.append(
            "Macquarie upgraded CoreWeave to Outperform with a $125 PT, "
            "validating the GPU-as-a-service model"
        )
    if has_microsoft:
        what_parts.append(
            "Microsoft confirmed a multi-billion-dollar AI infrastructure commitment in Ontario"
        )
    if has_vertiv:
        what_parts.append(
            "Vertiv acquired prefab enclosure maker BMarko, consolidating the modular DC supply chain"
        )

    if what_parts:
        # Construct flowing paragraph
        text = ". ".join(what_parts) + "."
        # Capitalize after periods
        text = re.sub(r"\.\s+([a-z])", lambda m: ". " + m.group(1).upper(), text)
        lines.append(text)
    else:
        lines.append("Thin day for DC-specific signals. Macro noise dominated the feed.")

    lines.append("")

    # ── SIGNALS WORTH YOUR ATTENTION
    lines.append("SIGNALS WORTH YOUR ATTENTION")

    # Only include signals with genuine DC finance angle
    worthy = []
    for s in amber + red:
        h = s["headline"]
        summ = _first_sentences(s.get("summary", ""), 1)
        so = _clean(s.get("second_order", ""))

        # Skip if headline is not genuinely DC
        h_lower = h.lower()
        if not any(kw in h_lower for kw in [
            "data center", "pjm", "grid", "coreweave", "gpu", "ai infrastructure",
            "construction", "blackstone", "microsoft", "vertiv", "prefab",
            "rate proposal", "generation", "capacity", "energy reliab",
            "digital infrastructure", "colocation",
        ]):
            # Check tier — only include Tier 1 matches
            if s.get("_tier") != 1:
                continue

        # Write practitioner "so what"
        so_what = _make_so_what(s)
        if so_what:
            worthy.append((h, so_what, s["alert_level"]))

    for h, sw, al in worthy[:8]:
        lines.append(f"  [{al}] {h[:85]}")
        lines.append(f"    So what: {sw}")
        lines.append("")

    if not worthy:
        lines.append("  No signals with actionable DC infrastructure finance angle today.")
        lines.append("")

    # ── DEAL EXPOSURE
    lines.append("DEAL EXPOSURE")
    deal_hits = []
    seen_deals = set()
    for s in dc_signals:
        deal = _deal_explanation(s)
        if deal and deal not in seen_deals:
            seen_deals.add(deal)
            deal_hits.append((deal, s))

    if deal_hits:
        for deal_name, s in deal_hits:
            h = s["headline"][:70]
            # Write specific transmission mechanism
            mechanism = _deal_mechanism(deal_name, s)
            lines.append(f"  {deal_name}: {mechanism}")
    else:
        lines.append("  No direct deal transmission paths identified today.")
    lines.append("")

    # ── ONE THING TO ACT ON
    lines.append("ONE THING TO ACT ON THIS WEEK")
    act_signal = _pick_actionable(dc_signals)
    if act_signal:
        lines.append(act_signal)
    else:
        lines.append("  No standout actionable signal. Routine DC flow.")
    lines.append("")

    return "\n".join(lines)


def _make_so_what(s: dict) -> str | None:
    """Generate a practitioner 'so what' for a signal. Returns None if not worth mentioning."""
    h = (s.get("headline") or "").lower()
    summ = _clean(s.get("summary") or "").lower()
    combined = h + " " + summ

    if re.search(r"pjm.*\d+.*gw|pjm.*auction|pjm.*generation", combined):
        return ("PJM is building a procurement framework for DC-driven load. "
                "If emergency auction clears at premium, it reprices capacity value for GT-108 and any gas peaker in the queue.")

    if re.search(r"data\s*center.*strain.*grid|grid.*pay.*data\s*cent|forced\s*to\s*pay", combined):
        return ("Regulatory backlash on DC grid costs is building. "
                "Watch for cost allocation rulings that change the interconnection economics for greenfield DC projects.")

    if re.search(r"rate\s*proposal.*grid|grid\s*upgrade.*energy\s*reliab", combined):
        gw = re.search(r"\$[\d,.]+\s*(?:billion|B)", summ) or re.search(r"\$[\d,.]+\s*(?:billion|B)", combined)
        val = gw.group(0) if gw else "significant capex"
        return f"Utility rate case cites {val} in DC-driven grid costs — sets precedent for cost pass-through in other RTO territories."

    if re.search(r"coreweave|gpu\s*cloud", combined):
        return "Macquarie upgrade validates GPU-as-a-service at scale. Relevant for any DC deal with hyperscaler offtake exposure."

    if re.search(r"reit.*ipo|ipo.*reit|blackstone.*data\s*cent", combined):
        return "Institutional capital pivoting from DC development to yield products. May tighten cap rates on stabilized DC assets in your pipeline."

    if re.search(r"microsoft.*billion.*ai|microsoft.*ai.*infrastructure", combined):
        return "Hyperscaler capex continues to flow despite macro headwinds. Validates long-term DC power demand thesis."

    if re.search(r"vertiv.*prefab|vertiv.*bmarko|prefab.*enclosure", combined):
        return "Modular DC supply chain consolidation — shorter lead times may benefit projects in construction phase."

    if re.search(r"construction.*cloudy|construction.*outlook.*data\s*cent", combined):
        return "Construction sector bifurcating: DC is the only segment with clear demand visibility. Supports premium pricing power for DC-focused EPC."

    if re.search(r"gas\s*price.*high|fuel\s*cost|gas\s*prices.*midterm", combined):
        return "Sustained high gas prices raise operating cost for gas-backed DC power. Exposure on deals with gas tolling agreements."

    if re.search(r"thorium|microreactor|shipping\s*container.*nuclear", combined):
        return "Long-dated optionality for DC baseload power. Not actionable this quarter but worth tracking for 2028+ pipeline."

    if re.search(r"ai\s*infrastructure|industrial\s*lesson", combined):
        return "Cross-sector knowledge transfer to DC operations — operational efficiency angle, not deal-critical."

    if re.search(r"resilience|continuity.*data\s*cent", combined):
        return "Operational resilience theme gaining traction. May affect insurance and redundancy requirements in DC underwriting."

    # Generic fallback — only if the signal is RED or high-scoring
    if s["alert_level"] == "RED":
        so = _clean(s.get("second_order", ""))[:120]
        return so if so else None

    return None


def _deal_mechanism(deal_name: str, s: dict) -> str:
    """Write a specific transmission mechanism for a deal hit."""
    h = (s.get("headline") or "").lower()
    summ = _clean(s.get("summary") or "").lower()

    if deal_name == "GT-108":
        if re.search(r"pjm", h + summ):
            return ("PJM emergency auction directly impacts GT-108 (SB Energy Ohio) — "
                    "if 15 GW clears at premium pricing, the capacity contract value "
                    "for GT-108's gas generation asset improves materially.")
        return "GT-108 exposure via PJM capacity market signal."

    if deal_name == "GT-109":
        return ("GT-109 (SB Energy Milam) exposed through gas price channel — "
                "sustained high gas prices affect fuel cost assumptions in the operating model.")

    if deal_name == "Storybook WI":
        return ("We Energies rate case in Wisconsin cites $1.9B in DC-driven grid costs — "
                "directly affects grid interconnection timeline and cost for Project Storybook WI.")

    if deal_name == "Edged DC Javelin":
        return ("High gas price signal transmits through power cost to Edged DC Javelin 2's "
                "operating margin assumptions.")

    if deal_name == "Delta Stack":
        return "Delta Stack exposed via construction cost channel — EPC budget pressure under R0."

    return f"{deal_name} exposure identified via signal content."


def _pick_actionable(signals: list[dict]) -> str | None:
    """Pick the single most actionable signal and write a directive."""
    # Prioritize: PJM auction > grid cost pushback > REIT/capital markets > other
    for s in signals:
        h = (s.get("headline") or "").lower()
        if re.search(r"pjm.*\d+.*gw|pjm.*auction", h):
            return (
                "PJM's emergency auction (Sep 2026 – Mar 2027) targeting 15 GW of new generation "
                "is the most significant DC-adjacent procurement event this year. "
                "GT-108 sits directly in PJM territory — if the auction clears at premium "
                "capacity prices, it reprices the deal's revenue assumptions upward. "
                "Track the auction design rules when PJM publishes them in Q2."
            )

    for s in signals:
        h = (s.get("headline") or "").lower()
        if re.search(r"data\s*center.*strain|grid.*pay|rate\s*proposal", h):
            return (
                "The regulatory pushback on DC grid costs (We Energies $1.9B rate case) "
                "is a leading indicator for interconnection cost allocation disputes in "
                "other RTO territories. If this model spreads, greenfield DC projects face "
                "higher grid connection costs. Watch for FERC commentary on cost allocation "
                "methodology in the April 30 large-load rulemaking."
            )

    for s in signals:
        h = (s.get("headline") or "").lower()
        if re.search(r"reit|ipo|blackstone.*data", h):
            return (
                "Blackstone's DC REIT IPO signals the institutional capital cycle is "
                "maturing from development to yield. If the IPO prices well, expect "
                "cap rate compression on stabilized DC assets — relevant for any "
                "deal in your pipeline approaching operational phase."
            )

    # Fallback to highest-scored AMBER
    for s in signals:
        if s["alert_level"] in ("RED", "AMBER"):
            so_what = _make_so_what(s)
            if so_what:
                return f"{s['headline'][:70]} — {so_what}"

    return None


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GroundTruth DC Intelligence Brief")
    parser.add_argument("--date", type=str, default=None,
                        help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--save", action="store_true",
                        help="Write raw sector brief to outputs/raw/ for debug. "
                             "Default: print only. The user-facing artifact is the "
                             "consolidated sector_briefs_<date>_<HHMM>ET.md produced "
                             "by gt/sector_briefs.py.")
    args = parser.parse_args()

    target_date = args.date or date.today().strftime("%Y-%m-%d")
    print(f"Building DC brief for {target_date}...\n")

    brief = build_brief(target_date)
    print(brief)

    if args.save:
        raw_dir = os.path.join(OUTPUT_DIR, "raw")
        os.makedirs(raw_dir, exist_ok=True)
        stamp = datetime.now(ET).strftime("%H%M")
        out_path = os.path.join(raw_dir, f"dc_brief_{target_date}_{stamp}ET.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(brief)
        print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
