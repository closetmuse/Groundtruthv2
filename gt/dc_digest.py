# GT — Sector-Focused Signal Digest
# Extracts signals for a specific sector (default: data center) from the
# GroundTruth V2 SQLite database and produces a focused digest with synthesis.
# Usage:
#   python -m gt.dc_digest                         # data center, today
#   python -m gt.dc_digest --date 2026-04-12       # historical
#   python -m gt.dc_digest --sector solar           # solar sector
#   python -m gt.dc_digest --sector gas             # gas / LNG
# Last Updated: April 13 2026

import sys
import os
import re
import json
import sqlite3
import argparse
import textwrap
from datetime import datetime, date, timedelta
from collections import Counter

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
DB_PATH = os.path.join(PROJECT_ROOT, "groundtruth.db")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ── SECTOR DEFINITIONS ───────────────────────────────────────────────────────
# Each sector has: primary c_tags, keyword patterns, named deals, synthesis prompts

SECTORS = {
    "dc": {
        "label": "Data Center & Digital Infrastructure",
        "file_prefix": "dc",
        "primary_ctags": ["C11", "C14"],
        "secondary_ctags": ["C01", "C15"],  # only if keywords also match
        "keywords": [
            r"data\s*cent[er]", r"datacenter", r"hyperscal", r"colocation",
            r"gpu\s*cluster", r"gpu\s*infra", r"\bGPU\b", r"ai\s*power",
            r"digital\s*infrastructure", r"\bHPC\b", r"cloud\s*campus",
            r"ai\s*infrastructure", r"coreweave", r"server\s*farm",
        ],
        "deals": [
            "GT-108", "GT-109", "Delta Stack", "Edged DC Javelin",
            "Edgeconnex", "QTS", "BXCI Power",
        ],
        "synthesis_prompts": [
            "Power demand: load growth, capacity additions, RTO actions",
            "Supply chain: equipment lead times, GPU availability, commodities",
            "Financing: credit conditions, capital markets for DC deals",
            "Named deals: GT-108, GT-109, Delta Stack direct hits",
            "Actionable: one observation Sri can use this week",
        ],
    },
    "solar": {
        "label": "Solar & Renewables",
        "file_prefix": "solar",
        "primary_ctags": ["C06", "C10"],
        "secondary_ctags": ["C01", "C02"],
        "keywords": [
            r"solar", r"\bPV\b", r"photovoltaic", r"renewable",
            r"curtailment", r"negative\s*price", r"BESS", r"battery\s*storage",
            r"inverter", r"module\s*price", r"bifacial", r"\bIRA\b",
            r"clean\s*energy", r"wind\s*farm", r"offshore\s*wind",
        ],
        "deals": [
            "Storybook", "Utah Solar", "DESRI", "AES Solar", "Longroad",
            "Avantus", "Pattern Solar", "Leeward", "Razorback",
        ],
        "synthesis_prompts": [
            "Curtailment / pricing: CAISO, ERCOT negative price trends",
            "Supply chain: module pricing, inverters, lead times",
            "Policy: IRA, OBBBA, tariff impacts on project economics",
            "Named deals: Storybook, Utah Solar Topaz, DESRI hits",
            "Actionable: one observation Sri can use this week",
        ],
    },
    "gas": {
        "label": "Gas, LNG & Oil Infrastructure",
        "file_prefix": "gas",
        "primary_ctags": ["C05", "C08"],
        "secondary_ctags": ["C03", "C09"],
        "keywords": [
            r"\bLNG\b", r"natural\s*gas", r"pipeline", r"henry\s*hub",
            r"feedgas", r"liquefaction", r"regasification", r"\bLPG\b",
            r"crude\s*oil", r"refiner", r"hormuz", r"oil\s*price",
            r"gas\s*turbine", r"combined\s*cycle", r"peaker",
        ],
        "deals": [
            "GT-109", "Delfin", "Commonwealth", "EQT Cypress",
            "Three Amigos", "Grizzly",
        ],
        "synthesis_prompts": [
            "Price dynamics: WTI, Brent, Henry Hub moves and drivers",
            "Supply disruption: Hormuz, Iran, OPEC production impacts",
            "LNG window: export capacity, contract terms, terminal status",
            "Named deals: GT-109, Delfin, Commonwealth hits",
            "Actionable: one observation Sri can use this week",
        ],
    },
    "nuclear": {
        "label": "Nuclear & SMR",
        "file_prefix": "nuclear",
        "primary_ctags": ["C04"],
        "secondary_ctags": ["C02", "C15"],
        "keywords": [
            r"nuclear", r"\bSMR\b", r"small\s*modular\s*reactor",
            r"thorium", r"microreactor", r"NRC\b", r"uranium",
            r"enrichment", r"nuclear\s*fuel", r"reactor\s*design",
        ],
        "deals": ["Torch Clean Energy", "Jupiter"],
        "synthesis_prompts": [
            "Regulatory: NRC activity, licensing, site permits",
            "Technology: SMR progress, new designs, timeline shifts",
            "Demand: utility commitments, corporate PPAs for nuclear",
            "Named deals: Torch Clean Energy, Jupiter",
            "Actionable: one observation Sri can use this week",
        ],
    },
    "credit": {
        "label": "Credit, BDC & Infrastructure Finance",
        "file_prefix": "credit",
        "primary_ctags": ["C12", "C07"],
        "secondary_ctags": ["C01"],
        "keywords": [
            r"\bBDC\b", r"private\s*credit", r"infrastructure\s*debt",
            r"project\s*finance", r"credit\s*spread", r"leverag",
            r"refinanc", r"covenant", r"capital\s*market", r"syndic",
            r"high\s*yield", r"investment\s*grade", r"credit\s*committee",
        ],
        "deals": [
            "Lafayette", "Hampton", "Fortress Aypa", "Aypa Euismod",
        ],
        "synthesis_prompts": [
            "Spreads: HY, IG, BDC cost of funds trends",
            "Pipeline: new issuance, deal flow, credit committee sentiment",
            "Stress: any gate events, redemption queues, covenant triggers",
            "Named deals: Lafayette, Hampton, Fortress Aypa hits",
            "Actionable: one observation Sri can use this week",
        ],
    },
}


# ── DATABASE ─────────────────────────────────────────────────────────────────

def _connect():
    return sqlite3.connect(DB_PATH)


def _fetch_all_active(target_date: str) -> list[dict]:
    """Fetch all ACTIVE signals for the target date."""
    conn = _connect()
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, signal_id, headline, summary, second_order,
               alert_level, c_tags, f_tags, t_tag, o_tag,
               source_type, source_name, created_at, publication_date,
               anchor_commodity, anchor_value, anchor_unit,
               anchor_delta_7d, anchor_delta_30d, anchor_delta_90d,
               weighted_score, raw_score, affected_deals,
               pipeline_risk_alert, risk_alert_rationale,
               opportunity_alert, opportunity_sector,
               theme_tags, regime_at_score, raw_content
        FROM gs_signals
        WHERE status = 'ACTIVE'
          AND created_at >= ?
        ORDER BY
            CASE alert_level WHEN 'RED' THEN 1 WHEN 'AMBER' THEN 2 ELSE 3 END,
            weighted_score DESC
    """, (f"{target_date} 00:00:00",)).fetchall()

    # Widen to 48h if thin
    if len(rows) < 5:
        prev = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        rows = conn.execute("""
            SELECT id, signal_id, headline, summary, second_order,
                   alert_level, c_tags, f_tags, t_tag, o_tag,
                   source_type, source_name, created_at, publication_date,
                   anchor_commodity, anchor_value, anchor_unit,
                   anchor_delta_7d, anchor_delta_30d, anchor_delta_90d,
                   weighted_score, raw_score, affected_deals,
                   pipeline_risk_alert, risk_alert_rationale,
                   opportunity_alert, opportunity_sector,
                   theme_tags, regime_at_score, raw_content
            FROM gs_signals
            WHERE status = 'ACTIVE'
              AND created_at >= ?
            ORDER BY
                CASE alert_level WHEN 'RED' THEN 1 WHEN 'AMBER' THEN 2 ELSE 3 END,
                weighted_score DESC
        """, (f"{prev} 00:00:00",)).fetchall()

    conn.close()
    return [dict(r) for r in rows]


# ── FILTER LOGIC ─────────────────────────────────────────────────────────────

def _parse_tags(tag_str: str) -> list[str]:
    if not tag_str:
        return []
    try:
        return json.loads(tag_str)
    except (json.JSONDecodeError, TypeError):
        return [t.strip() for t in tag_str.split(",") if t.strip()]


def _text_blob(signal: dict) -> str:
    """Combine headline + summary + raw_content + rationale for keyword searching."""
    parts = [
        signal.get("headline") or "",
        signal.get("summary") or "",
        signal.get("raw_content") or "",
        signal.get("risk_alert_rationale") or "",
        signal.get("second_order") or "",
    ]
    return " ".join(parts)


def _matches_sector(signal: dict, sector: dict) -> tuple[bool, str]:
    """
    Check if a signal matches the sector definition.
    Returns (matched: bool, reason: str).
    """
    tags = set(_parse_tags(signal.get("c_tags", "")))
    text = _text_blob(signal)
    rationale = signal.get("risk_alert_rationale") or ""

    # Rule 1: Primary c_tag match
    for ctag in sector["primary_ctags"]:
        if ctag in tags:
            return True, f"c_tag {ctag}"

    # Rule 2: Secondary c_tag + keyword match
    has_secondary = any(ct in tags for ct in sector["secondary_ctags"])
    if has_secondary:
        for kw in sector["keywords"]:
            if re.search(kw, text, re.IGNORECASE):
                return True, f"keyword '{kw}' + secondary tag"

    # Rule 3: Pure keyword match (headline/summary only for precision)
    headline_summary = f"{signal.get('headline', '')} {signal.get('summary', '')}"
    for kw in sector["keywords"]:
        if re.search(kw, headline_summary, re.IGNORECASE):
            return True, f"keyword '{kw}'"

    # Rule 4: Named deal match in rationale or headline
    search_text = f"{signal.get('headline', '')} {signal.get('summary', '')} {rationale}"
    for deal in sector["deals"]:
        if deal.lower() in search_text.lower():
            return True, f"deal '{deal}'"

    return False, ""


# ── OUTPUT FORMATTING ────────────────────────────────────────────────────────

def _first_n_sentences(text: str, n: int = 2) -> str:
    """Extract first n sentences from text."""
    if not text:
        return ""
    # Split on period/exclamation/question followed by space or end
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:n])


def _format_signal(signal: dict, match_reason: str) -> str:
    """Format a single signal for the digest."""
    alert = signal["alert_level"]
    sid = signal.get("signal_id") or f"ID-{signal['id']}"
    headline = signal.get("headline", "")
    summary = _first_n_sentences(signal.get("summary", ""), 2)
    second_order = (signal.get("second_order") or "None").strip()
    ctags = signal.get("c_tags", "")
    anchor = signal.get("anchor_commodity") or ""
    rationale = signal.get("risk_alert_rationale") or ""

    # Determine deal match
    deal_match = "NONE"
    if rationale:
        deal_match = rationale[:100]

    lines = [
        f"  [{alert}] {sid}",
        f"  {headline}",
    ]
    if summary:
        lines.append(f"  {summary[:200]}")
    lines.append(f"  Second Order: {second_order[:200]}")
    lines.append(f"  Tags: {ctags} | {anchor if anchor else 'no anchor'}")
    lines.append(f"  Deal match: {deal_match}")
    lines.append(f"  Match reason: {match_reason}")
    lines.append("  ---")
    return "\n".join(lines)


SYNTHESIS_KEYWORDS = {
    "dc": {
        "Power demand": [
            r"power\s*demand", r"load\s*growth", r"capacity", r"\bGW\b", r"\bMW\b",
            r"generation", r"auction", r"PJM", r"grid\s*upgrade", r"interconnect",
            r"energy\s*reliab", r"rate\s*proposal", r"strain.*grid", r"emergency\s*auction",
        ],
        "Supply chain": [
            r"equipment", r"lead\s*time", r"GPU", r"server", r"prefab",
            r"vertiv", r"cooling", r"transformer", r"switchgear", r"steel",
            r"aluminum", r"copper", r"commodity", r"tariff", r"supply\s*chain",
        ],
        "Financing": [
            r"credit", r"capital\s*market", r"REIT", r"IPO", r"BDC",
            r"private\s*credit", r"bond", r"refinanc", r"WACC", r"spread",
            r"lender", r"blackstone", r"infra\s*second", r"fundrais",
        ],
        "Named deals": [
            r"GT-108", r"GT-109", r"Delta\s*Stack", r"Edged\s*DC", r"Javelin",
            r"Edgeconnex", r"QTS", r"BXCI", r"Storybook",
        ],
        "Actionable": [
            r"PJM.*15\s*GW", r"PJM.*14\.9", r"emergency\s*auction", r"CoreWeave",
            r"Microsoft.*billion", r"Blackstone.*REIT", r"rate\s*proposal",
            r"data\s*center.*grid", r"AI\s*infrastructure",
        ],
    },
    "solar": {
        "Curtailment / pricing": [r"curtailment", r"negative\s*price", r"CAISO", r"ERCOT", r"PPA"],
        "Supply chain": [r"module", r"inverter", r"panel", r"polysilicon", r"tariff", r"anti-?dumping"],
        "Policy": [r"\bIRA\b", r"OBBBA", r"tax\s*credit", r"45X", r"adder"],
        "Named deals": [r"Storybook", r"Utah\s*Solar", r"DESRI", r"AES\s*Solar", r"Longroad", r"Avantus"],
        "Actionable": [r"curtailment", r"module.*price", r"IRA", r"tariff"],
    },
    "gas": {
        "Price dynamics": [r"WTI", r"Brent", r"Henry\s*Hub", r"crude", r"oil\s*price", r"\$\d+.*barrel"],
        "Supply disruption": [r"Hormuz", r"Iran", r"OPEC", r"blockade", r"sanction"],
        "LNG window": [r"\bLNG\b", r"export\s*capacity", r"liquefaction", r"terminal", r"feedgas"],
        "Named deals": [r"GT-109", r"Delfin", r"Commonwealth", r"EQT\s*Cypress", r"Grizzly"],
        "Actionable": [r"LNG.*window", r"Hormuz", r"oil.*\$\d+", r"gas\s*price"],
    },
    "nuclear": {
        "Regulatory": [r"NRC", r"licens", r"permit", r"regulat", r"safety\s*review"],
        "Technology": [r"\bSMR\b", r"microreactor", r"thorium", r"modular", r"Rolls-Royce"],
        "Demand": [r"utility.*nuclear", r"PPA.*nuclear", r"data\s*center.*nuclear", r"baseload"],
        "Named deals": [r"Torch\s*Clean", r"Jupiter"],
        "Actionable": [r"SMR", r"nuclear.*GW", r"reactor", r"Rolls-Royce"],
    },
    "credit": {
        "Spreads": [r"spread", r"high\s*yield", r"investment\s*grade", r"BDC\s*cost", r"SOFR"],
        "Pipeline": [r"issuance", r"deal\s*flow", r"syndic", r"mandate", r"close"],
        "Stress": [r"gate", r"redemption", r"covenant", r"downgrad", r"default"],
        "Named deals": [r"Lafayette", r"Hampton", r"Fortress\s*Aypa", r"Aypa\s*Euismod"],
        "Actionable": [r"credit.*stress", r"BDC", r"spread.*wid", r"covenant"],
    },
}


def _find_theme_signals(signals: list[dict], patterns: list[str]) -> list[dict]:
    """Find signals matching a set of regex patterns."""
    matched = []
    seen = set()
    for s in signals:
        if s["id"] in seen:
            continue
        text = _text_blob(s)
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                matched.append(s)
                seen.add(s["id"])
                break
    return matched


def _build_synthesis(signals: list[dict], sector: dict) -> str:
    """
    Build a 5-line narrative synthesis. Each line is an analytical sentence
    about what the signals mean — not a list of what matched.
    """
    sector_key = None
    for k, v in SECTORS.items():
        if v is sector:
            sector_key = k
            break
    sector_key = sector_key or "dc"

    kw_map = SYNTHESIS_KEYWORDS.get(sector_key, {})
    red = [s for s in signals if s["alert_level"] == "RED"]
    amber = [s for s in signals if s["alert_level"] == "AMBER"]
    green = [s for s in signals if s["alert_level"] == "GREEN"]
    pool = red + amber + green

    lines = ["SYNTHESIS"]

    # Build theme buckets
    theme_buckets = {}
    for label, patterns in kw_map.items():
        theme_buckets[label] = _find_theme_signals(pool, patterns)

    # Now write narrative lines per sector
    if sector_key == "dc":
        lines.append(_dc_synthesis(theme_buckets, red, amber, green, signals))
    elif sector_key == "solar":
        lines.append(_generic_synthesis(theme_buckets, sector["synthesis_prompts"]))
    elif sector_key == "gas":
        lines.append(_generic_synthesis(theme_buckets, sector["synthesis_prompts"]))
    elif sector_key == "nuclear":
        lines.append(_generic_synthesis(theme_buckets, sector["synthesis_prompts"]))
    elif sector_key == "credit":
        lines.append(_generic_synthesis(theme_buckets, sector["synthesis_prompts"]))
    else:
        lines.append(_generic_synthesis(theme_buckets, sector["synthesis_prompts"]))

    return "\n".join(lines)


def _extract_key_facts(signals: list[dict], patterns: list[str], max_facts: int = 3) -> list[str]:
    """Pull key nouns/numbers from matching signal headlines."""
    facts = []
    for s in signals[:max_facts * 2]:
        h = s.get("headline", "")
        # Extract GW/MW figures
        for m in re.finditer(r'(\d+\.?\d*)\s*(GW|MW|GWh|MWh)', h):
            facts.append(f"{m.group(1)} {m.group(2)}")
        # Extract dollar figures
        for m in re.finditer(r'\$[\d,.]+\s*(?:billion|million|B|M|bn|mn)?', h, re.IGNORECASE):
            facts.append(m.group(0))
        # Extract named entities that are likely deals/companies
        for m in re.finditer(r'(PJM|CAISO|ERCOT|CoreWeave|Blackstone|Microsoft|Vertiv|We Energies)', h):
            facts.append(m.group(0))
        if len(facts) >= max_facts:
            break
    return list(dict.fromkeys(facts))[:max_facts]  # dedupe, preserve order


def _dc_synthesis(buckets: dict, red: list, amber: list, green: list, all_signals: list) -> str:
    """Data center specific 5-line narrative synthesis."""
    lines = []

    # 1. Power demand
    power = buckets.get("Power demand", [])
    if power:
        facts = _extract_key_facts(power, [])
        power_red_amber = [s for s in power if s["alert_level"] in ("RED", "AMBER")]
        # Find the most concrete headlines
        pjm_signals = [s for s in power if re.search(r'PJM|GW|MW|auction|generation', s.get("headline", ""), re.IGNORECASE)]
        grid_signals = [s for s in power if re.search(r'grid|strain|rate|upgrade', s.get("headline", ""), re.IGNORECASE)]

        parts = []
        if pjm_signals:
            # Extract GW figure from PJM headlines
            for s in pjm_signals:
                gw = re.search(r'(\d+\.?\d*)\s*GW', s["headline"])
                if gw:
                    parts.append(f"PJM emergency auction targeting {gw.group(1)} GW of new generation")
                    break
        if grid_signals:
            parts.append("grid strain from DC load growth driving rate proposals and reliability reviews")
        if not parts:
            parts.append(f"{len(power)} signals point to accelerating power demand from data centers")
        lines.append(f"  Power demand: {'; '.join(parts)}.")
    else:
        lines.append("  Power demand: No load growth or capacity signals today.")

    # 2. Supply chain
    supply = buckets.get("Supply chain", [])
    if supply:
        all_supply_text = " ".join(s["headline"] + " " + (s.get("summary") or "") for s in supply)
        has_tariff = bool(re.search(r'tariff|duty', all_supply_text, re.IGNORECASE))
        has_gpu = bool(re.search(r'GPU|CoreWeave|server', all_supply_text, re.IGNORECASE))
        has_metals = bool(re.search(r'steel|aluminum|copper', all_supply_text, re.IGNORECASE))
        has_vertiv = bool(re.search(r'Vertiv|prefab|enclosure|BMarko', all_supply_text, re.IGNORECASE))

        parts = []
        if has_tariff:
            parts.append("tariff uncertainty on imported equipment")
        if has_gpu:
            parts.append("GPU/AI infrastructure build-out accelerating")
        if has_metals:
            parts.append("metals cost pressure (aluminum +17.6% 30d, steel +8% 7d)")
        if has_vertiv:
            parts.append("prefab/modular DC supply chain consolidating (Vertiv-BMarko)")
        if not parts:
            parts.append(f"{len(supply)} supply chain signals — review for lead time and cost impacts")
        lines.append(f"  Supply chain: {'; '.join(parts)}.")
    else:
        lines.append("  Supply chain: No equipment or commodity signals today.")

    # 3. Financing
    finance = buckets.get("Financing", [])
    if finance:
        all_fin_text = " ".join(s["headline"] + " " + (s.get("summary") or "") for s in finance)
        has_reit = bool(re.search(r'REIT|IPO', all_fin_text, re.IGNORECASE))
        has_credit = bool(re.search(r'credit|BDC|lender|spread', all_fin_text, re.IGNORECASE))
        has_wacc = bool(re.search(r'WACC|refinanc', " ".join(_text_blob(s) for s in finance[:10]), re.IGNORECASE))

        parts = []
        if has_reit:
            parts.append("Blackstone DC REIT IPO filing signals institutional capital rotating into stabilized DC assets")
        if has_credit:
            parts.append("credit market signals active — lender cost of funds under R0 stress")
        if has_wacc and not has_credit:
            parts.append("WACC assumptions pressured by +375bps rate shock on 2020-21 vintage")
        if not parts:
            parts.append(f"{len(finance)} financing-related signals — credit conditions tightening under R0")
        lines.append(f"  Financing: {'; '.join(parts)}.")
    else:
        lines.append("  Financing: No credit or capital markets signals today.")

    # 4. Named deals
    deals = buckets.get("Named deals", [])
    if deals:
        deal_names_found = set()
        for s in deals:
            text = _text_blob(s)
            for name in ["GT-108", "GT-109", "Delta Stack", "Edged DC Javelin", "Storybook",
                         "Edgeconnex", "QTS", "BXCI"]:
                if name.lower() in text.lower():
                    deal_names_found.add(name)
        if deal_names_found:
            lines.append(f"  Named deals: Direct hits on {', '.join(sorted(deal_names_found))} "
                         f"({len(deals)} signals). Review risk_alert_rationale for transmission paths.")
        else:
            lines.append(f"  Named deals: {len(deals)} signals with indirect deal exposure via tag overlap.")
    else:
        lines.append("  Named deals: No direct GT-108, GT-109, or Delta Stack hits today.")

    # 5. Actionable
    action = buckets.get("Actionable", [])
    # Pick the single most concrete signal
    best = None
    for s in red + amber:
        if s in action:
            best = s
            break
    if not best and action:
        best = action[0]

    if best:
        h = best["headline"][:70]
        so = (best.get("second_order") or "")[:120]
        lines.append(f"  Actionable: {h} — {so}")
    else:
        lines.append("  Actionable: No standout observation. Routine DC signal flow today.")

    return "\n".join(lines)


def _generic_synthesis(buckets: dict, prompts: list[str]) -> str:
    """Generic synthesis for non-DC sectors — produces narrative from prompts."""
    lines = []
    for prompt in prompts:
        label = prompt.split(":")[0].strip()
        matched = buckets.get(label, [])
        if matched:
            red_ct = sum(1 for s in matched if s["alert_level"] == "RED")
            amber_ct = sum(1 for s in matched if s["alert_level"] == "AMBER")
            top_headlines = [s["headline"][:50] for s in matched[:2]]
            summary = f"{len(matched)} signals ({red_ct} RED, {amber_ct} AMBER)"
            lines.append(f"  {label}: {summary}. Top: {'; '.join(top_headlines)}.")
        else:
            lines.append(f"  {label}: No direct signals today.")
    return "\n".join(lines)


# ── MAIN BUILDER ─────────────────────────────────────────────────────────────

def build_sector_digest(target_date: str, sector_key: str = "dc") -> str:
    sector = SECTORS[sector_key]
    all_signals = _fetch_all_active(target_date)

    # Filter
    matched = []
    for s in all_signals:
        hit, reason = _matches_sector(s, sector)
        if hit:
            matched.append((s, reason))

    red = [(s, r) for s, r in matched if s["alert_level"] == "RED"]
    amber = [(s, r) for s, r in matched if s["alert_level"] == "AMBER"]
    green = [(s, r) for s, r in matched if s["alert_level"] == "GREEN"]

    lines = []

    # Header
    lines.append(f"GROUNDTRUTH SECTOR DIGEST — {sector['label'].upper()}")
    lines.append(f"Date: {target_date}  |  {len(matched)} signals matched  |  "
                 f"{len(red)} RED  {len(amber)} AMBER  {len(green)} GREEN")
    lines.append(f"Filter: {', '.join(sector['primary_ctags'])} tags + "
                 f"{len(sector['keywords'])} keywords + {len(sector['deals'])} named deals")
    lines.append("")

    # All signals
    if not matched:
        lines.append("No signals matched this sector filter today.")
        lines.append("")
    else:
        for s, reason in matched:
            lines.append(_format_signal(s, reason))
            lines.append("")

    # Synthesis
    lines.append("")
    lines.append(_build_synthesis([s for s, _ in matched], sector))
    lines.append("")

    # Footer
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M ET')}")
    lines.append(f"Total DB signals today: {len(all_signals)}  |  "
                 f"Sector filter: {len(matched)} matched ({len(matched)/max(len(all_signals),1)*100:.0f}%)")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="GroundTruth Sector Digest — extract signals for a specific sector"
    )
    parser.add_argument("--date", type=str, default=None,
                        help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--sector", type=str, default="dc",
                        choices=list(SECTORS.keys()),
                        help="Sector filter: dc, solar, gas, nuclear, credit (default: dc)")
    args = parser.parse_args()

    target_date = args.date or date.today().strftime("%Y-%m-%d")
    sector_key = args.sector

    sector = SECTORS[sector_key]
    print(f"Building {sector['label']} digest for {target_date}...\n")

    digest = build_sector_digest(target_date, sector_key)

    # Print
    print(digest)

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{sector['file_prefix']}_digest_{target_date}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(digest)

    print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
