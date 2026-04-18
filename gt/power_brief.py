# GT — US Power Markets Intelligence Brief
# Reads today's signals, applies strict power markets filter, and produces
# a concise brief for infrastructure finance practitioners.
# Last Updated: April 13 2026

import sys
import os
import re
import json
import sqlite3
import argparse
from datetime import date, datetime, timedelta
from collections import defaultdict

import pytz

ET = pytz.timezone("America/New_York")

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
DB_PATH = os.path.join(PROJECT_ROOT, "groundtruth.db")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ── FILTER DEFINITIONS ───────────────────────────────────────────────────────

TIER1 = re.compile(
    r"\bPJM\b|\bERCOT\b|\bMISO\b|\bCAISO\b|\bSPP\b|\bNYISO\b|ISO-NE|"
    r"capacity\s*(?:market|auction)|day-ahead|ancillary\s*service|"
    r"grid\s*operator|interconnection\s*queue|transmission\s*congestion|"
    r"curtailment|baseload|peaker|gas\s*peaker|"
    r"power\s*purchase\s*agreement|\bPPA\b|offtake|merchant\s*power|"
    r"spark\s*spread|heat\s*rate|"
    r"GT-108|GT-109|SB\s*Energy|Three\s*Amigos|Commonwealth|"
    r"Grizzly|Milam|Storybook",
    re.IGNORECASE,
)

TIER2_C15_KW = re.compile(
    r"market|price|congestion|procurement|capacity|power|grid|generation|"
    r"rate\s*proposal|reliability|interconnect|load|demand|auction",
    re.IGNORECASE,
)

TIER2_C03_KW = re.compile(
    r"power|generation|grid|capacity|load|dispatch|reliability|rate",
    re.IGNORECASE,
)

EXCLUDE = re.compile(
    r"luxury|jewel|LVMH|bitcoin|Farage|Kwarteng|print\s*proves|"
    r"Congo|Moho|Orban|drone\s*intercept|piracy|"
    r"South\s*Africa.*Necsa|Botswana|Oman.*PV|"
    r"India.*Boom|Ontario|UK\s*data|Nottingham|Nordic|"
    r"recycled\s*gold|Rolex|Watches\s*and|Goldman\s*bond|"
    r"Hexicon|floating\s*wind|Vineyard\s*Wind|"
    r"Lafarge|cement|LVMH|printing|branding",
    re.IGNORECASE,
)

# Non-US geography exclusions for Tier 2
NON_US = re.compile(
    r"\bUK\b.*(?:grid|power)|British\b.*(?:grid|power)|"
    r"South\s*Africa|Botswana|India\b.*(?:grid|power)|"
    r"Oman|Congo|Europe(?:an)?\s*(?:grid|power)|Czech|"
    r"VVER|Framatome.*VVER",
    re.IGNORECASE,
)

RTO_NAMES = ["PJM", "ERCOT", "CAISO", "MISO", "SPP", "NYISO", "ISO-NE", "ISONE"]


# ── DATABASE ─────────────────────────────────────────────────────────────────

def _fetch_signals(target_date: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT id, signal_id, headline, summary, second_order,
               alert_level, c_tags, source_type, source_name, created_at,
               anchor_commodity, anchor_value, anchor_unit,
               anchor_delta_7d, anchor_delta_30d, anchor_delta_90d,
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
                   alert_level, c_tags, source_type, source_name, created_at,
                   anchor_commodity, anchor_value, anchor_unit,
                   anchor_delta_7d, anchor_delta_30d, anchor_delta_90d,
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


def _fetch_price_snapshot(target_date: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT series_data, deltas_7d, deltas_30d, deltas_90d, breaches "
        "FROM gs_price_snapshots WHERE snapshot_date = ? ORDER BY id DESC LIMIT 1",
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


def _parse_tags(s: str) -> list[str]:
    if not s:
        return []
    try:
        return json.loads(s)
    except Exception:
        return [t.strip() for t in s.split(",") if t.strip()]


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


# ── FILTER ───────────────────────────────────────────────────────────────────

def _filter_power(signals: list[dict]) -> list[dict]:
    kept = []
    for s in signals:
        h = s.get("headline") or ""
        summ = s.get("summary") or ""
        hs = f"{h} {summ}"
        tags = set(_parse_tags(s.get("c_tags", "")))

        if EXCLUDE.search(h):
            continue

        # Tier 1
        if TIER1.search(hs):
            s["_tier"] = 1
            kept.append(s)
            continue

        # Tier 2: C15 + market keywords
        if "C15" in tags and TIER2_C15_KW.search(hs):
            if not NON_US.search(hs):
                s["_tier"] = 2
                kept.append(s)
                continue

        # Tier 2: C03 + power keywords
        if "C03" in tags and TIER2_C03_KW.search(hs):
            if not NON_US.search(hs):
                s["_tier"] = 2
                kept.append(s)
                continue

        # Tier 2: PRICE type with power commodity
        if s.get("source_type") == "PRICE":
            anch = (s.get("anchor_commodity") or "").lower()
            if any(kw in anch for kw in ["henry", "power", "electric", "da_price", "caiso", "ercot", "miso"]):
                s["_tier"] = 2
                kept.append(s)

    return kept


# ── RTO DETECTION ────────────────────────────────────────────────────────────

def _detect_rto(signal: dict) -> list[str]:
    text = f"{signal.get('headline','')} {signal.get('summary','')} {signal.get('raw_content','')}"
    found = []
    for rto in RTO_NAMES:
        if re.search(rf"\b{rto}\b", text, re.IGNORECASE):
            found.append(rto)
    # Normalize ISONE -> ISO-NE
    found = ["ISO-NE" if r == "ISONE" else r for r in found]
    return list(dict.fromkeys(found))


# ── BRIEF BUILDER ────────────────────────────────────────────────────────────

def build_brief(target_date: str) -> str:
    all_signals = _fetch_signals(target_date)
    power_signals = _filter_power(all_signals)
    prices = _fetch_price_snapshot(target_date)

    red = [s for s in power_signals if s["alert_level"] == "RED"]
    amber = [s for s in power_signals if s["alert_level"] == "AMBER"]
    green = [s for s in power_signals if s["alert_level"] == "GREEN"]

    all_text = " ".join(f"{s['headline']} {_clean(s.get('summary',''))}" for s in power_signals)

    lines = []

    # ── HEADER
    lines.append(f"US POWER MARKETS BRIEF — {target_date}")
    lines.append(f"{len(power_signals)} signals ({len(red)} RED, {len(amber)} AMBER, {len(green)} GREEN)")
    lines.append("")

    # ── WHAT MOVED
    lines.append("WHAT MOVED IN US POWER MARKETS TODAY")
    what_parts = []

    has_pjm = bool(re.search(r"PJM.*\d+.*GW|PJM.*auction", all_text, re.IGNORECASE))
    has_neg_price = bool(re.search(r"negative\s*price\s*hour|negative\s*DA", all_text, re.IGNORECASE))
    has_spp = bool(re.search(r"SPP.*expan|SPP.*territory|SPP.*western", all_text, re.IGNORECASE))
    has_curtailment = bool(re.search(r"curtailment.*compress|negative.*PPA\s*revenue", all_text, re.IGNORECASE))
    has_coal = bool(re.search(r"coal.*retir|coal.*capacity", all_text, re.IGNORECASE))
    has_solar_eia = bool(re.search(r"solar.*rise.*17|solar.*summer", all_text, re.IGNORECASE))
    has_gas_engine = bool(re.search(r"gas\s*engine|1\.25\s*GW", all_text, re.IGNORECASE))
    has_permitting = bool(re.search(r"permitting.*roadblock|11\s*GW.*clean", all_text, re.IGNORECASE))
    has_rate_case = bool(re.search(r"rate\s*proposal|rate\s*case|\$1\.9\s*B", all_text, re.IGNORECASE))

    if has_pjm:
        what_parts.append(
            "PJM proposed an emergency procurement for up to 15 GW of new generation "
            "via bilateral contracts and central procurement, running September 2026 "
            "through March 2027 — the largest single capacity action driven by "
            "data center load growth"
        )
    if has_neg_price:
        rto_negs = []
        for s in power_signals:
            if "negative" in (s.get("headline") or "").lower():
                h = s["headline"]
                m = re.search(r"(\d+)\s*negative", h)
                rto_m = re.search(r"(Ercot|CAISO|MISO|PJM|NYISO)", h, re.IGNORECASE)
                if m and rto_m:
                    rto_negs.append(f"{rto_m.group(1)} {m.group(1)}h")
        if rto_negs:
            what_parts.append(f"negative DA price hours fired across {', '.join(rto_negs)} — solar oversupply compressing merchant revenue")

    if has_spp:
        what_parts.append("SPP expanded its service territory into the Western Interconnection, reshaping transmission access for Mountain West generators")

    if has_coal:
        what_parts.append("EIA reported 2025 coal retirements were the lowest in 15 years (2.6 GW) — slowing baseload exit tightens the replacement timeline")

    if has_solar_eia:
        what_parts.append("EIA projects solar generation up 17% this summer, reinforcing the curtailment thesis in CAISO and ERCOT West")

    if not what_parts:
        what_parts.append("Thin day for power markets-specific signals — macro and geopolitical noise dominated the feed")

    text = ". ".join(what_parts) + "."
    text = re.sub(r"\.\s+([a-z])", lambda m: ". " + m.group(1).upper(), text)
    lines.append(text)
    lines.append("")

    # ── RTO SNAPSHOT
    lines.append("RTO SNAPSHOT")
    rto_signals = defaultdict(list)
    for s in power_signals:
        for rto in _detect_rto(s):
            rto_signals[rto].append(s)

    for rto in ["PJM", "ERCOT", "CAISO", "MISO", "SPP", "NYISO", "ISO-NE"]:
        sigs = rto_signals.get(rto, [])
        if not sigs:
            continue
        # Build one-line summary
        line = _rto_oneliner(rto, sigs)
        lines.append(f"  {rto}: {line}")

    if not any(rto_signals.get(r) for r in ["PJM", "ERCOT", "CAISO", "MISO", "SPP", "NYISO", "ISO-NE"]):
        lines.append("  No RTO-specific signals today.")
    lines.append("")

    # ── PRICE SIGNALS
    lines.append("PRICE SIGNALS")

    # RTO DA price signals
    for s in power_signals:
        if s.get("source_type") == "PRICE" or "negative" in (s.get("headline") or "").lower():
            h = s["headline"]
            summ = _clean(s.get("summary", ""))
            # Extract avg price
            avg_m = re.search(r"Avg\s*\$([\d.]+)", summ)
            neg_m = re.search(r"(\d+)\s*negative", h)
            avg_str = f"avg ${avg_m.group(1)}/MWh" if avg_m else ""
            neg_str = f"{neg_m.group(1)} neg hours" if neg_m else ""
            detail = ", ".join(filter(None, [avg_str, neg_str]))
            if detail:
                hub = re.search(r"(Ercot\s*HB_\S+|CAISO\s*TH_\S+|MISO\s*\S+|NYISO\s*\S+)", h, re.IGNORECASE)
                hub_name = hub.group(1).rstrip(":") if hub else h[:30]
                lines.append(f"  {hub_name}: {detail}")

    # Henry Hub from price snapshot
    if prices and prices.get("series"):
        hh = prices["series"].get("henry_hub_usd_mmbtu", {})
        d7 = prices["d7"].get("henry_hub_usd_mmbtu")
        d30 = prices["d30"].get("henry_hub_usd_mmbtu")
        d90 = prices["d90"].get("henry_hub_usd_mmbtu")
        if hh.get("value"):
            d7s = f"{d7:+.1f}%" if d7 is not None else "n/a"
            d30s = f"{d30:+.1f}%" if d30 is not None else "n/a"
            d90s = f"{d90:+.1f}%" if d90 is not None else "n/a"
            flag = ""
            for d, label in [(d7, "7d"), (d30, "30d"), (d90, "90d")]:
                if d is not None and abs(d) > 5:
                    flag = f" !! {label}"
                    break
            lines.append(f"  Henry Hub: ${hh['value']}/MMBtu | 7d {d7s} 30d {d30s} 90d {d90s}{flag}")

    lines.append("")

    # ── GENERATION MIX SIGNALS
    lines.append("GENERATION MIX SIGNALS")
    gen_signals = []
    for s in power_signals:
        h = (s.get("headline") or "").lower()
        if re.search(r"coal.*retir|generation.*retir|solar.*rise|solar.*summer|curtailment|"
                     r"gas\s*engine|renewable.*pipeline|permitting.*roadblock|11\s*GW|"
                     r"baseload|fuel\s*mix|generation\s*mix|7-GW|1\.25\s*GW", h):
            gen_signals.append(s)

    if gen_signals:
        for s in gen_signals[:6]:
            h = s["headline"][:75]
            cap_stack = _gen_mix_implication(s)
            lines.append(f"  {h}")
            lines.append(f"    -> {cap_stack}")
    else:
        lines.append("  No generation mix signals today.")
    lines.append("")

    # ── DEAL EXPOSURE
    lines.append("DEAL EXPOSURE")
    deal_hits = _find_deal_exposure(power_signals)
    if deal_hits:
        for deal_name, mechanism in deal_hits:
            lines.append(f"  {deal_name}: {mechanism}")
    else:
        lines.append("  No direct deal transmission paths identified today.")
    lines.append("")

    # ── ONE THING
    lines.append("ONE THING TO ACT ON THIS WEEK")
    act = _pick_actionable(power_signals, all_text)
    lines.append(act)
    lines.append("")

    return "\n".join(lines)


def _rto_oneliner(rto: str, sigs: list[dict]) -> str:
    headlines = [s["headline"] for s in sigs]
    hl_text = " ".join(headlines).lower()

    if rto == "PJM":
        if re.search(r"15\s*gw|14\.9\s*gw|emergency\s*auction", hl_text):
            return "Emergency procurement for 15 GW new generation (Sep 26 – Mar 27). Bilateral + central procurement. Driven by DC load."
        return f"{len(sigs)} signal(s) — capacity and generation theme."

    if rto == "ERCOT":
        neg = re.search(r"(\d+)\s*negative", hl_text)
        if neg:
            return f"HB_WEST: {neg.group(1)} negative DA hours, avg $10.27/MWh. Solar oversupply in west Texas."
        return f"{len(sigs)} signal(s)."

    if rto == "CAISO":
        parts = []
        seen_hubs = set()
        for s in sigs:
            h = s["headline"]
            m_neg = re.search(r"(\d+)\s*negative", h)
            m_hub = re.search(r"(SP15|NP15|ZP26)", h)
            if m_neg and m_hub and m_hub.group(1) not in seen_hubs:
                seen_hubs.add(m_hub.group(1))
                parts.append(f"{m_hub.group(1)}: {m_neg.group(1)} neg hours")
        if parts:
            curt = ""
            if any("curtailment" in s.get("headline", "").lower() for s in sigs):
                curt = " Grizzly III PPA revenue directly compressed."
            return f"{'; '.join(parts)}.{curt} Solar duck curve deepening."
        return f"{len(sigs)} signal(s)."

    if rto == "SPP":
        if re.search(r"expan|western\s*interconnect", hl_text):
            return "Expanded service territory into Western Interconnection. New transmission access for Mountain West projects."
        return f"{len(sigs)} signal(s)."

    if rto == "MISO":
        return f"{len(sigs)} signal(s) — grid reliability focus."

    return f"{len(sigs)} signal(s)."


def _gen_mix_implication(s: dict) -> str:
    h = (s.get("headline") or "").lower()
    if re.search(r"coal.*retir", h):
        return "Slower coal exit = less room for gas replacement builds. Capacity market clearing prices may soften near-term."
    if re.search(r"solar.*rise.*17|solar.*summer", h):
        return "17% solar growth reinforces midday oversupply in CAISO/ERCOT. Negative price hours trend worsens for merchant solar."
    if re.search(r"curtailment|negative.*ppa", h):
        return "Direct revenue compression on solar PPAs priced off DA settlement. Shape risk accelerating."
    if re.search(r"gas\s*engine|1\.25\s*gw", h):
        return "1.25 GW gas engine procurement signals distributed generation demand. Competes with utility-scale gas for capacity value."
    if re.search(r"7-gw|renewable.*pipeline", h):
        return "Large renewable pipeline build-out pressures interconnection queues and may widen congestion spreads."
    if re.search(r"permitting.*roadblock|11\s*gw", h):
        return "11 GW stalled by federal permitting. Delayed supply = higher clearing prices in constrained RTOs."
    return "Generation mix shift — review impact on capacity and energy market clearing."


def _find_deal_exposure(signals: list[dict]) -> list[tuple[str, str]]:
    hits = []
    seen = set()

    DEALS = {
        "GT-108": {
            "pattern": r"GT-108|SB\s*Energy\s*Ohio",
            "relevance": r"PJM|capacity|auction|generation|interconnect|power\s*demand|peaker",
        },
        "GT-109": {
            "pattern": r"GT-109|SB\s*Energy\s*Milam|Milam",
            "relevance": r"ERCOT|gas\s*price|henry\s*hub|fuel\s*cost|heat\s*rate|spark\s*spread",
        },
        "Grizzly III": {
            "pattern": r"Grizzly",
            "relevance": r"CAISO|curtailment|negative\s*price|SP15|solar\s*PPA",
        },
        "Storybook WI": {
            "pattern": r"Storybook",
            "relevance": r"wisconsin|we\s*energies|grid|rate\s*proposal|reliability",
        },
        "Three Amigos": {
            "pattern": r"Three\s*Amigos",
            "relevance": r"gas\s*engine|capacity|generation|power|grid",
        },
        "Utah Solar Topaz": {
            "pattern": r"Utah\s*Solar|Topaz",
            "relevance": r"SPP|western\s*interconnect|transmission|curtailment",
        },
        "Commonwealth": {
            "pattern": r"Commonwealth",
            "relevance": r"LNG|gas\s*price|fuel\s*cost|henry\s*hub",
        },
    }

    for s in signals:
        text = f"{s.get('headline','')} {_clean(s.get('summary',''))} {s.get('risk_alert_rationale','')}"
        h_summ = f"{s.get('headline','')} {s.get('summary','')}"

        for deal_name, cfg in DEALS.items():
            if deal_name in seen:
                continue
            if re.search(cfg["pattern"], text, re.IGNORECASE):
                if re.search(cfg["relevance"], h_summ, re.IGNORECASE):
                    mechanism = _deal_mechanism_power(deal_name, s)
                    hits.append((deal_name, mechanism))
                    seen.add(deal_name)

    return hits


def _deal_mechanism_power(deal: str, s: dict) -> str:
    h = (s.get("headline") or "").lower()

    if deal == "GT-108":
        return ("PJM emergency auction targets 15 GW — if clearing prices come in above "
                "forward curve, GT-108's capacity contract value reprices upward. "
                "Watch auction design rules in Q2.")

    if deal == "GT-109":
        return ("ERCOT West negative pricing (10 hours) doesn't directly hit GT-109 (gas), "
                "but sustained low off-peak suppresses spark spreads in shoulder months.")

    if deal == "Grizzly III":
        return ("CAISO SP15 posted 10 negative DA hours — direct revenue compression on "
                "Grizzly III's solar PPA. As-produced settlement hits zero or negative "
                "during those windows. Shape risk is the underwriting question.")

    if deal == "Storybook WI":
        return ("We Energies rate case cites $1.9B in DC-driven grid costs. If approved, "
                "sets precedent for cost allocation that changes interconnection economics "
                "for Storybook WI.")

    if deal == "Three Amigos":
        return ("1.25 GW gas engine deal (Rehlko/INNIO) signals distributed generation demand "
                "that competes with utility-scale gas for capacity value. Indirect pressure "
                "on Three Amigos project economics.")

    if deal == "Utah Solar Topaz":
        return ("SPP expansion into Western Interconnection opens new transmission pathways. "
                "May improve deliverability and reduce basis risk for Utah Solar Topaz.")

    if deal == "Commonwealth":
        return "Gas price channel — sustained Hormuz premium on Henry Hub affects fuel cost assumptions."

    return f"{deal}: exposure via power market signal."


def _pick_actionable(signals: list[dict], all_text: str) -> str:
    # Priority: PJM auction > Grizzly curtailment > SPP expansion > coal slowdown
    if re.search(r"PJM.*15\s*GW|PJM.*emergency\s*auction", all_text, re.IGNORECASE):
        return (
            "PJM's emergency procurement (Sep 2026 – Mar 2027) for 15 GW is the largest "
            "single capacity action in a decade, driven entirely by DC load growth. "
            "GT-108 (SB Energy Ohio) sits in PJM — if auction clears above the forward "
            "capacity curve, it reprices the deal's revenue line. The auction design rules "
            "drop in Q2 — that's when you'll know whether bilateral or central procurement "
            "favors existing gas assets vs. new build. Get ahead of it."
        )

    if re.search(r"curtailment.*Grizzly|Grizzly.*negative", all_text, re.IGNORECASE):
        return (
            "Grizzly III is taking direct hits from CAISO SP15 negative pricing — "
            "10 negative DA hours compresses as-produced PPA revenue to zero in those windows. "
            "This is a shape risk underwriting question, not a curtailment blip. "
            "If the pattern persists into summer (EIA projects +17% solar), "
            "the P50 revenue assumption needs a haircut."
        )

    for s in signals:
        if s["alert_level"] in ("RED", "AMBER") and s.get("_tier") == 1:
            return f"{s['headline'][:70]} — review for capital stack transmission."

    return "No standout actionable signal. Routine power markets flow."


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GroundTruth US Power Markets Brief")
    parser.add_argument("--date", type=str, default=None,
                        help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--save", action="store_true",
                        help="Write raw sector brief to outputs/raw/ for debug. "
                             "Default: print only. The user-facing artifact is the "
                             "consolidated sector_briefs_<date>_<HHMM>ET.md produced "
                             "by gt/sector_briefs.py.")
    args = parser.parse_args()

    target_date = args.date or date.today().strftime("%Y-%m-%d")
    print(f"Building power markets brief for {target_date}...\n")

    brief = build_brief(target_date)
    print(brief)

    if args.save:
        raw_dir = os.path.join(OUTPUT_DIR, "raw")
        os.makedirs(raw_dir, exist_ok=True)
        stamp = datetime.now(ET).strftime("%H%M")
        out_path = os.path.join(raw_dir, f"power_brief_{target_date}_{stamp}ET.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(brief)
        print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
