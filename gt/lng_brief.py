# GT — US LNG & Natural Gas Intelligence Brief
# Reads today's signals, applies strict LNG/gas filter, and produces
# a concise brief for infrastructure finance practitioners.
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

TIER1 = re.compile(
    r"\bLNG\b|liquefied\s*natural\s*gas|natural\s*gas|Henry\s*Hub|"
    r"gas\s*pipeline|feedgas|regasification|\bFSRU\b|"
    r"Golden\s*Pass|Sabine\s*Pass|Corpus\s*Christi|Freeport|"
    r"Calcasieu|Plaquemines|Delfin|Commonwealth\s*LNG|Port\s*Arthur\s*LNG|"
    r"Cove\s*Point|"
    r"QatarEnergy|North\s*Field|force\s*majeure|"
    r"Hormuz|Strait\s*of\s*Hormuz|\bIran\b|Gulf\s*shipping|"
    r"LNG\s*tanker|LNG\s*carrier|\bcargo\b|spot\s*LNG|\bJKM\b|\bTTF\b|"
    r"gas\s*export|gas\s*import|gas\s*storage|Waha|Permian\s*gas|"
    r"GT-109|SB\s*Energy\s*Milam|Project\s*Delfin|Project\s*Commonwealth",
    re.IGNORECASE,
)

TIER2_C05_KW = re.compile(
    r"supply|export|pipeline|feedgas|pricing|gas|LNG|shipping|terminal|"
    r"crude|oil\s*price|barrel|blockade|energy\s*crisis|fuel\s*crunch",
    re.IGNORECASE,
)

TIER2_C08_KW = re.compile(
    r"energy|gas|LNG|shipping|oil|crude|barrel|blockade|Hormuz|Iran|"
    r"fuel|reserve|IEA|OPEC",
    re.IGNORECASE,
)

EXCLUDE = re.compile(
    r"luxury|jewel|LVMH|bitcoin|Farage|Kwarteng|print\s*proves|"
    r"jewellers|Rolex|Watches\s*and|recycled\s*gold|Goldman\s*bond|"
    r"Hexicon|Vineyard\s*Wind|Lafarge|cement|branding|"
    r"Botswana|Oman.*PV|India.*Boom|Nottingham|Nordic|Heim\s*to\s*target|"
    r"drone\s*intercept|Orban|CoreWeave|REIT\s*IPO|"
    r"data\s*center\s*REIT|prefab\s*enclosure|Vertiv|"
    r"PJM.*generation|PJM.*auction|microreactor|thorium|"
    r"Framatome.*VVER|Finland.*nuclear\s*waste|"
    r"student\s*housing|Rolls-Royce\s*SMR|"
    r"solar\s*generation.*summer|curtailment\s*exposure",
    re.IGNORECASE,
)

# Second-pass: exclude if headline is clearly non-gas
NON_GAS_HEADLINE = re.compile(
    r"^(?:.*?(?:data\s*center|REIT|IPO|solar\s*integration|"
    r"microgrid|distribution\s*grid|aerial\s*cable|"
    r"5G\s*in\s*oil|Mortenson|Linea\s*Energy|"
    r"asset\s*management\s*takes|infra\s*secondaries|"
    r"renewable\s*energy\s*has\s*a|"
    r"construction.*economic\s*outlook|"
    r"utility\s*tech\s*adoption))$",
    re.IGNORECASE,
)


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


def _blob(s: dict) -> str:
    return f"{s.get('headline','')} {s.get('summary','')} {s.get('raw_content','')} {s.get('risk_alert_rationale','')}"


# ── FILTER ───────────────────────────────────────────────────────────────────

def _filter_lng(signals: list[dict]) -> list[dict]:
    kept = []
    for s in signals:
        h = s.get("headline") or ""
        summ = s.get("summary") or ""
        hs = f"{h} {summ}"
        tags = set(_parse_tags(s.get("c_tags", "")))

        if EXCLUDE.search(h):
            continue
        if NON_GAS_HEADLINE.search(h):
            continue

        if TIER1.search(hs):
            s["_tier"] = 1
            kept.append(s)
        elif "C05" in tags and TIER2_C05_KW.search(hs):
            s["_tier"] = 2
            kept.append(s)
        elif "C08" in tags and TIER2_C08_KW.search(hs):
            s["_tier"] = 2
            kept.append(s)

    return kept


# ── BRIEF BUILDER ────────────────────────────────────────────────────────────

def build_brief(target_date: str) -> str:
    all_signals = _fetch_signals(target_date)
    lng_signals = _filter_lng(all_signals)
    prices = _fetch_price_snapshot(target_date)

    red = [s for s in lng_signals if s["alert_level"] == "RED"]
    amber = [s for s in lng_signals if s["alert_level"] == "AMBER"]
    green = [s for s in lng_signals if s["alert_level"] == "GREEN"]

    all_text = " ".join(_clean(s.get("headline", "") + " " + (s.get("summary", "") or "")) for s in lng_signals)

    lines = []

    # ── HEADER
    lines.append(f"US LNG & NATURAL GAS BRIEF — {target_date}")
    lines.append(f"{len(lng_signals)} signals ({len(red)} RED, {len(amber)} AMBER, {len(green)} GREEN)")
    lines.append("")

    # ── WHAT MOVED
    lines.append("WHAT MOVED IN US LNG AND GAS TODAY")
    lines.append(_build_what_moved(lng_signals, all_text))
    lines.append("")

    # ── HORMUZ STATUS
    lines.append("HORMUZ STATUS")
    lines.append(_build_hormuz(lng_signals))
    lines.append("")

    # ── US EXPORT TERMINAL SNAPSHOT
    lines.append("US EXPORT TERMINAL SNAPSHOT")
    terminal_lines = _build_terminals(lng_signals)
    if terminal_lines:
        for tl in terminal_lines:
            lines.append(f"  {tl}")
    else:
        lines.append("  No terminal-specific signals today. Golden Pass T1 online since March 30.")
    lines.append("")

    # ── PRICE SIGNALS
    lines.append("PRICE SIGNALS")
    lines.append(_build_prices(prices))
    lines.append("")

    # ── SUPPLY CHAIN AND SHIPPING
    lines.append("SUPPLY CHAIN AND SHIPPING")
    lines.append(_build_shipping(lng_signals))
    lines.append("")

    # ── DEAL EXPOSURE
    lines.append("DEAL EXPOSURE")
    deal_lines = _build_deals(lng_signals)
    if deal_lines:
        for dl in deal_lines:
            lines.append(f"  {dl}")
    else:
        lines.append("  No direct deal transmission paths identified today.")
    lines.append("")

    # ── VL WATCH
    lines.append("VERIFICATION LATENCY WATCH")
    lines.append(_build_vl_watch(lng_signals))
    lines.append("")

    # ── ONE THING
    lines.append("ONE THING TO ACT ON THIS WEEK")
    lines.append(_build_actionable(lng_signals, all_text))
    lines.append("")

    return "\n".join(lines)


def _build_what_moved(signals: list[dict], all_text: str) -> str:
    parts = []

    if re.search(r"last\s*(?:Hormuz|prewar)\s*tanker|supply\s*crunch\s*intensif", all_text, re.IGNORECASE):
        parts.append(
            "The last pre-blockade tankers from the Gulf are reaching refineries now — "
            "once those cargoes unload, the physical supply gap from Hormuz closure becomes real"
        )

    if re.search(r"Permian.*takeaway|Waha", all_text, re.IGNORECASE):
        parts.append(
            "Permian gas takeaway constraints persist at 22 Bcf/d with Waha basis deeply negative, "
            "but new pipeline capacity is finally approaching FID"
        )

    if re.search(r"Port\s*Arthur.*construction|Port\s*Arthur.*advance", all_text, re.IGNORECASE):
        parts.append("Port Arthur LNG terminal construction advancing on schedule")

    if re.search(r"Cove\s*Point.*re-export", all_text, re.IGNORECASE):
        parts.append(
            "Cove Point LNG seeking regulatory approval for re-exports — a play to arbitrage "
            "the Hormuz premium by redirecting imported cargoes"
        )

    if re.search(r"Eni.*Russian\s*LNG|suspend.*ban.*Russian\s*LNG", all_text, re.IGNORECASE):
        parts.append(
            "Eni CEO called for suspending the EU's planned Jan 2027 ban on Russian LNG, "
            "citing Hormuz disruption — if Brussels blinks, it undercuts the US export premium thesis"
        )

    if re.search(r"LNG\s*shock.*Asia|Asia.*import.*plung", all_text, re.IGNORECASE):
        parts.append(
            "Asian LNG imports have plunged to Covid-era lows as Gulf supply is trapped behind the blockade, "
            "with JKM spot prices soaring"
        )

    if re.search(r"IEA.*reserve|ready\s*to\s*act", all_text, re.IGNORECASE):
        parts.append("IEA signaling readiness for additional strategic reserve releases")

    if not parts:
        parts.append("Thin day for LNG-specific signals — macro and geopolitical noise dominated")

    text = ". ".join(parts) + "."
    text = re.sub(r"\.\s+([a-z])", lambda m: ". " + m.group(1).upper(), text)
    return text


def _build_hormuz(signals: list[dict]) -> str:
    hormuz = [s for s in signals if re.search(
        r"Hormuz|blockade|Iran.*war|Iran.*port|Iran.*nuk|Strait|"
        r"naval\s*block|truce\s*talk|peace\s*deal|ceasefire",
        _blob(s), re.IGNORECASE
    )]

    if not hormuz:
        return "  No direct Hormuz signals today. Last known: US naval blockade active, ceasefire talks ongoing."

    parts = []

    has_escalation = any(re.search(r"intensif|crunch|threaten|block.*port|piracy", s["headline"], re.IGNORECASE) for s in hormuz)
    has_deesc = any(re.search(r"truce|peace\s*deal|ceasefire|talk|negotiat", s["headline"], re.IGNORECASE) for s in hormuz)
    has_last_tanker = any(re.search(r"last.*tanker|prewar.*cargo", s["headline"], re.IGNORECASE) for s in hormuz)
    has_uk = any(re.search(r"Starmer|UK.*will\s*not", s["headline"], re.IGNORECASE) for s in hormuz)
    has_un = any(re.search(r"UN\s*urge|navigation", s["headline"], re.IGNORECASE) for s in hormuz)

    if has_last_tanker:
        parts.append("Last pre-blockade Gulf cargoes reaching refineries — physical supply gap imminent")
    if has_escalation:
        parts.append("Iran threatening Gulf ports in response to US blockade")
    if has_deesc:
        parts.append("Truce talks active — crude pared gains on peace deal hopes, but no breakthrough")
    if has_uk:
        parts.append("UK explicitly declined to support US blockade")
    if has_un:
        parts.append("UN urging all parties to respect Hormuz navigation rights")

    if parts:
        return "  " + ". ".join(parts) + f". ({len(hormuz)} Hormuz-related signals today.)"
    return f"  {len(hormuz)} Hormuz signals — mixed escalation/de-escalation. Status: blockade active, talks ongoing."


def _build_terminals(signals: list[dict]) -> list[str]:
    TERMINALS = {
        "Port Arthur LNG": r"Port\s*Arthur",
        "Cove Point": r"Cove\s*Point",
        "Golden Pass": r"Golden\s*Pass",
        "Sabine Pass": r"Sabine\s*Pass",
        "Corpus Christi": r"Corpus\s*Christi",
        "Freeport LNG": r"Freeport",
        "Calcasieu Pass": r"Calcasieu",
        "Plaquemines": r"Plaquemines",
        "Delfin": r"\bDelfin\b",
        "Commonwealth": r"Commonwealth",
    }

    out = []
    for name, pattern in TERMINALS.items():
        matching = [s for s in signals if re.search(pattern, _blob(s), re.IGNORECASE)]
        if matching:
            # Build one-liner from signal content
            h = matching[0]["headline"][:60]
            if re.search(r"construction.*advanc", h, re.IGNORECASE):
                out.append(f"{name}: Construction progressing. On track.")
            elif re.search(r"re-export", h, re.IGNORECASE):
                out.append(f"{name}: Seeking regulatory OK for re-exports — Hormuz arbitrage play.")
            elif re.search(r"Iran.*reshape|Eyes\s*of", h, re.IGNORECASE):
                out.append(f"{name}: Mentioned in Iran war/LNG reshaping analysis. Export window widening.")
            else:
                out.append(f"{name}: {_clean(h)}")

    return out


def _build_prices(prices: dict) -> str:
    lines = []
    if prices and prices.get("series"):
        hh = prices["series"].get("henry_hub_usd_mmbtu", {})
        wti = prices["series"].get("wti_usd_bbl", {})
        brent = prices["series"].get("brent_usd_bbl", {})
        d7, d30, d90 = prices.get("d7", {}), prices.get("d30", {}), prices.get("d90", {})

        for key, info in [("Henry Hub", hh), ("WTI", wti), ("Brent", brent)]:
            if not info:
                continue
            val = info.get("value")
            if val is None:
                continue
            unit = info.get("unit", "")
            k = {"Henry Hub": "henry_hub_usd_mmbtu", "WTI": "wti_usd_bbl", "Brent": "brent_usd_bbl"}[key]
            d7v, d30v, d90v = d7.get(k), d30.get(k), d90.get(k)
            d7s = f"{d7v:+.1f}%" if d7v is not None else "n/a"
            d30s = f"{d30v:+.1f}%" if d30v is not None else "n/a"
            d90s = f"{d90v:+.1f}%" if d90v is not None else "n/a"
            flag = ""
            for d, label in [(d7v, "7d"), (d30v, "30d"), (d90v, "90d")]:
                if d is not None and abs(d) > 5:
                    flag = f" !! {label}"
                    break
            lines.append(f"  {key}: {val} {unit} | 7d {d7s} 30d {d30s} 90d {d90s}{flag}")

        # Henry Hub - JKM spread note
        if hh.get("value"):
            lines.append(f"  HH-JKM spread: Not available in price snapshot. "
                         f"Signals indicate JKM soaring on Gulf supply disruption — spread widening supports US export economics.")
    else:
        lines.append("  No price snapshot available.")

    return "\n".join(lines)


def _build_shipping(signals: list[dict]) -> str:
    shipping = [s for s in signals if re.search(
        r"tanker|carrier|cargo|shipping|route|insurance|piracy|"
        r"Jones\s*Act|fleet|vessel|navigation",
        _blob(s), re.IGNORECASE
    )]

    if not shipping:
        return "  No shipping-specific signals today."

    parts = []
    seen = set()

    for s in shipping:
        h = s["headline"]
        if s["id"] in seen:
            continue
        seen.add(s["id"])

        if re.search(r"last.*tanker|prewar.*cargo|supply\s*crunch", h, re.IGNORECASE):
            parts.append("Last pre-blockade cargoes unloading — Gulf shipping lane effectively closed to Iranian exports. Insurance costs remain elevated.")
        elif re.search(r"Jones\s*Act", h, re.IGNORECASE):
            parts.append("Jones Act suspension by Trump hasn't eased energy prices — domestic shipping relief insufficient against global supply squeeze.")
        elif re.search(r"carrier|fleet|Buana", h, re.IGNORECASE):
            parts.append("LNG carrier fleet expanding (Indonesia's Buana Lintas added second steam carrier) — but vessel availability remains tight on Atlantic basin routes.")
        elif re.search(r"piracy|state-sponsored", h, re.IGNORECASE):
            parts.append("Iran-linked piracy in Strait adding war risk premium to transit insurance.")
        elif re.search(r"navigation|UN\s*urge", h, re.IGNORECASE):
            parts.append("UN urging navigation rights — diplomatic signal but no enforcement mechanism.")

    if parts:
        return "\n".join(f"  {p}" for p in parts[:4])
    return f"  {len(shipping)} shipping signals — review for route and insurance cost impacts."


def _build_deals(signals: list[dict]) -> list[str]:
    hits = []
    seen = set()

    DEALS = {
        "GT-109 SB Energy Milam": {
            "pat": r"GT-109|Milam",
            "rel": r"gas\s*price|henry\s*hub|fuel\s*cost|natural\s*gas|ERCOT|Permian|Waha|feedgas",
            "mech": ("Henry Hub down 17.8% 90d despite Hormuz — Permian oversupply and Waha basis "
                     "discount insulating GT-109's fuel cost. But if Hormuz persists and HH normalizes "
                     "upward, the fuel cost assumption in the operating model needs stress-testing."),
        },
        "Project Delfin": {
            "pat": r"Delfin",
            "rel": r"LNG|export|Gulf|Iran|Hormuz|shipping|terminal|gas",
            "mech": ("Hormuz blockade widens the HH-JKM spread — positive for Delfin's FLNG export "
                     "economics in the near term. But sustained Gulf disruption raises questions about "
                     "long-term Asian buyer appetite for US-sourced LNG vs. diversifying to Qatar post-crisis."),
        },
        "Project Commonwealth": {
            "pat": r"Commonwealth",
            "rel": r"LNG|export|Gulf|gas|shipping|terminal|Hormuz",
            "mech": ("Same spread dynamic as Delfin. Commonwealth's FID timeline may accelerate "
                     "if Asian buyers are signing contracts to lock in non-Gulf supply. "
                     "Watch for new HOA/SPA announcements in the next 60 days."),
        },
    }

    for s in signals:
        text = _blob(s)
        hs = f"{s.get('headline','')} {s.get('summary','')}"
        for deal, cfg in DEALS.items():
            if deal in seen:
                continue
            if re.search(cfg["pat"], text, re.IGNORECASE):
                if re.search(cfg["rel"], hs, re.IGNORECASE):
                    hits.append(f"{deal}: {cfg['mech']}")
                    seen.add(deal)

    return hits


def _build_vl_watch(signals: list[dict]) -> str:
    vl_candidates = []

    # Cove Point re-export
    for s in signals:
        h = (s.get("headline") or "").lower()
        if "cove point" in h and "re-export" in h:
            vl_candidates.append(
                "Cove Point re-export application: Regulatory filing is public today but the "
                "arbitrage implication (redirecting imported cargoes at Hormuz premium) won't reach "
                "most capital stacks for 2-4 weeks. Est. VL: 15-25 days."
            )
        if "eni" in h and "russian lng" in h:
            vl_candidates.append(
                "Eni CEO calling to suspend EU Russian LNG ban: If Brussels acts, it removes a "
                "key demand driver for US Gulf Coast projects. The policy signal is public but "
                "the FID-level implication won't be priced until EU policy response. Est. VL: 30-60 days."
            )
        if "permian" in h and ("takeaway" in h or "waha" in h):
            vl_candidates.append(
                "Permian gas takeaway expansion approaching FID: Waha basis discount is the "
                "leading indicator — when it narrows, feedgas economics shift for Gulf Coast terminals. "
                "Most project finance models haven't updated Waha assumptions. Est. VL: 20-40 days."
            )

    if vl_candidates:
        return "\n".join(f"  {v}" for v in vl_candidates[:3])
    return "  No high-confidence VL candidates today."


def _build_actionable(signals: list[dict], all_text: str) -> str:
    if re.search(r"last.*tanker|prewar.*cargo|supply\s*crunch\s*intensif", all_text, re.IGNORECASE):
        return (
            "The physical supply gap from Hormuz is about to become real — last pre-blockade cargoes "
            "are unloading now. Once refinery inventories start drawing down (1-2 weeks), expect "
            "spot LNG repricing and potential force majeure declarations from Gulf-sourced contracts. "
            "For Delfin and Commonwealth, this is the moment the export spread thesis either proves "
            "out or gets overwhelmed by shipping risk. Track Asian buyer behavior — if they start "
            "signing new HOAs with US terminals, that's your signal to accelerate FID conversations."
        )

    if re.search(r"Eni.*Russian\s*LNG|suspend.*ban", all_text, re.IGNORECASE):
        return (
            "Eni's call to suspend the EU Russian LNG ban is the tail risk to watch. If Brussels "
            "caves, the demand case for US Gulf Coast export capacity weakens materially. "
            "Track EU Council response over the next 2-3 weeks."
        )

    if re.search(r"Permian.*takeaway|Waha.*price", all_text, re.IGNORECASE):
        return (
            "Permian gas takeaway constraints are the feedgas economics story. When new pipeline "
            "capacity reaches FID, Waha basis narrows and Gulf Coast terminal feedgas costs rise. "
            "Update GT-109's fuel cost assumptions accordingly."
        )

    return "No standout actionable LNG/gas signal today. Monitor Hormuz status and HH-JKM spread."


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GroundTruth US LNG & Gas Brief")
    parser.add_argument("--date", type=str, default=None,
                        help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--save", action="store_true",
                        help="Write raw sector brief to outputs/raw/ for debug. "
                             "Default: print only. The user-facing artifact is the "
                             "consolidated sector_briefs_<date>_<HHMM>ET.md produced "
                             "by gt/sector_briefs.py.")
    args = parser.parse_args()

    target_date = args.date or date.today().strftime("%Y-%m-%d")
    print(f"Building LNG & gas brief for {target_date}...\n")

    brief = build_brief(target_date)
    print(brief)

    if args.save:
        raw_dir = os.path.join(OUTPUT_DIR, "raw")
        os.makedirs(raw_dir, exist_ok=True)
        stamp = datetime.now(ET).strftime("%H%M")
        out_path = os.path.join(raw_dir, f"lng_brief_{target_date}_{stamp}ET.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(brief)
        print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
