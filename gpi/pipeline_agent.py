"""
GroundTruth V2 — gpi/pipeline_agent.py
GPi — GroundPipeline Agent. Live deal exposure engine.
Reads pipeline deals from Sheets, scores each against active signals,
price movements, binary event proximity, and regime stress.
Outputs deal heat scores for email Section 6 and Sheets Deal Watch tab.

Last Updated: April 2026
"""

import sys
import os
import json
import sqlite3
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from typing import Optional

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

DB_PATH = os.path.join(PROJECT_ROOT, "groundtruth.db")

# ── DEAL SCORE DATACLASS ─────────────────────────────────────────────────────

@dataclass
class DealScore:
    """Composite deal heat score with sub-component breakdown."""
    deal_id: str = ""
    deal_name: str = ""
    heat_score: float = 0.0
    heat_level: str = "COOL"
    signal_pressure: float = 0.0
    commodity_exposure: float = 0.0
    binary_proximity: float = 0.0
    regime_amplifier: float = 0.0
    action_flag: str = "ROUTINE"
    narrative: str = ""
    heat_rationale: str = ""
    scored_at: str = ""
    top_signals: list = field(default_factory=list)
    data_flags: list = field(default_factory=list)
    # Narrative building context
    top_signal_headlines: list = field(default_factory=list)
    closest_event_name: str = ""
    closest_event_days: int = 999
    red_signal_count: int = 0
    matched_signal_count: int = 0


# ── STEP 1: DEAL LOADER ──────────────────────────────────────────────────────

def load_active_deals() -> list[dict]:
    """
    Load ACTIVE and WATCH deals from Google Sheets Pipeline tab.

    Filters out CLOSED and DEFERRED. Returns list of deal dicts.
    Falls back to empty list if Sheets unavailable.
    """
    try:
        from sheets.pipeline import read_pipeline_from_sheet
        all_deals = read_pipeline_from_sheet()
        active = [
            d for d in all_deals
            if d.get("Status", "").upper() in ("ACTIVE", "WATCH", "")
        ]
        print(f"  GPi: {len(active)} active/watch deals loaded")
        return active
    except Exception as e:
        print(f"  GPi: Deal load failed: {e}")
        return []


# ── STEP 2A: SIGNAL PRESSURE ─────────────────────────────────────────────────

def score_signal_pressure(deal: dict, signals_last_7d: list) -> tuple:
    """
    Score signal pressure on a deal from recent signals.

    Match signals via C-Tags (primary) and A-Tags (fallback for V1 deals).
    RED match = 25 points, AMBER = 15, GREEN = 5.
    Sum matches, normalize to 0-25.

    Returns:
        (score: float, top_signal_ids: list, data_flags: list)
    """
    deal_c = {t.strip() for t in deal.get("C-Tags", "").split(",") if t.strip()}
    deal_a = {t.strip() for t in deal.get("A-Tags", "").split(",") if t.strip()}

    if not deal_c and not deal_a:
        return 0.0, [], ["NO_TAGS"]

    points = 0
    matched = []
    alert_weights = {"RED": 25, "AMBER": 15, "GREEN": 5}

    for sig in signals_last_7d:
        sig_c = set()
        sig_a = set()
        try:
            sig_c = set(json.loads(sig.get("c_tags", "[]")))
        except Exception:
            pass
        # A-tags derived from c_tags via C_TO_A_MAP
        from gs.classify import C_TO_A_MAP
        for ct in sig_c:
            for at in C_TO_A_MAP.get(ct, []):
                sig_a.add(at)

        hit = False
        if deal_c and sig_c & deal_c:
            hit = True
        elif deal_a and sig_a & deal_a:
            hit = True

        if hit:
            alert = sig.get("alert_level", "GREEN")
            points += alert_weights.get(alert, 5)
            matched.append((sig.get("signal_id", ""), alert))

    # Normalize to 0-25
    score = min(25.0, points / max(len(signals_last_7d), 1) * 25)
    # But also cap by raw count
    if points > 0:
        score = min(25.0, max(score, min(25.0, points * 0.5)))

    top_ids = [sid for sid, _ in sorted(matched, key=lambda x: alert_weights.get(x[1], 0), reverse=True)[:3]]
    return round(score, 1), top_ids, []


# ── STEP 2B: COMMODITY EXPOSURE ───────────────────────────────────────────────

COMMODITY_PRICE_MAP = {
    "oil":          "wti_usd_bbl",
    "crude":        "wti_usd_bbl",
    "wti":          "wti_usd_bbl",
    "brent":        "brent_usd_bbl",
    "natural gas":  "henry_hub_usd_mmbtu",
    "gas":          "henry_hub_usd_mmbtu",
    "lng":          "henry_hub_usd_mmbtu",
    "steel":        "steel_hrc_index",      # FRED PPI index
    "aluminum":     "aluminum_usd_mt",      # Yahoo Finance COMEX
    "copper":       "copper_usd_mt",        # Yahoo Finance COMEX
    "modules":      "aluminum_usd_mt",      # Solar module proxy → aluminum
    "power":        "ercot_hub_north_mwh",
    "ercot":        "ercot_hub_north_mwh",
}


def score_commodity_exposure(deal: dict, latest_prices: dict,
                             deltas_30d: dict) -> tuple:
    """
    Score commodity exposure from deal's key commodities vs price movements.

    30d breach thresholds: >50% -> 25, >30% -> 18, >15% -> 10, <15% -> 3.
    If commodity has no live price feed, score 0 with METALS_PENDING flag.

    Returns:
        (score: float, data_flags: list)
    """
    commodities = [c.strip().lower() for c in
                   deal.get("Key Commodities", "").split(",") if c.strip()]
    if not commodities:
        return 0.0, []

    best_score = 0.0
    flags = []

    for comm in commodities:
        price_field = None
        for key, field_name in COMMODITY_PRICE_MAP.items():
            if key in comm:
                price_field = field_name
                break

        if price_field is None:
            flags.append("METALS_PENDING")
            continue

        delta = deltas_30d.get(price_field)
        if delta is None:
            continue

        abs_delta = abs(delta) if isinstance(delta, (int, float)) else 0
        if abs_delta > 50:
            s = 25.0
        elif abs_delta > 30:
            s = 18.0
        elif abs_delta > 15:
            s = 10.0
        else:
            s = 3.0

        best_score = max(best_score, s)

    # Deduplicate flags
    flags = list(set(flags))
    return round(best_score, 1), flags


# ── STEP 2C: BINARY PROXIMITY ────────────────────────────────────────────────

def score_binary_proximity(deal: dict, open_events: list) -> tuple:
    """
    Score binary event proximity for a deal.

    For each open event linked to deal: T-0 to T-7 -> 25,
    T-8 to T-30 -> 15, T-31 to T-90 -> 8, T-90+ -> 3.

    Returns:
        (score: float, closest_event_name: str, days_remaining: int)
    """
    deal_name = deal.get("Deal Name", "")
    binary_field = deal.get("Binary Events", "")

    best_score = 0.0
    closest_name = ""
    closest_days = 999

    for ev in open_events:
        # Check if event is linked to this deal
        linked = False
        try:
            linked_deals = json.loads(ev.get("linked_deals", "[]"))
            for ld in linked_deals:
                if deal_name.lower() in ld.lower() or ld.lower() in deal_name.lower():
                    linked = True
                    break
        except Exception:
            pass

        # Also check deal's binary events field
        if not linked and binary_field:
            ev_name = ev.get("name", "").lower()
            if any(kw in ev_name for kw in binary_field.lower().split(",")):
                linked = True

        if not linked:
            continue

        # Calculate days remaining
        try:
            dl = datetime.strptime(ev.get("deadline", ""), "%Y-%m-%d").date()
            days = (dl - date.today()).days
        except Exception:
            continue

        if days <= 7:
            s = 25.0
        elif days <= 30:
            s = 15.0
        elif days <= 90:
            s = 8.0
        else:
            s = 3.0

        if s > best_score:
            best_score = s
            closest_name = ev.get("name", "")
            closest_days = days

    return round(best_score, 1), closest_name, closest_days


# ── STEP 2D: REGIME AMPLIFIER ────────────────────────────────────────────────

REGIME_SCORES = {
    "R0": 20.0,   # Compound Stress
    "R1": 15.0,   # Stagflationary
    "R2": 18.0,   # Credit Stress
    "R3": 15.0,   # Commodity Shock
    "R4": 5.0,    # Policy Tailwind
}


def score_regime_amplifier(current_regime: str = "R0") -> float:
    """Score based on current macro regime. R0 Compound = 20."""
    return REGIME_SCORES.get(current_regime, 10.0)


# ── STEP 3: DEAL HEAT ENGINE ─────────────────────────────────────────────────

def _get_signals_last_7d() -> list[dict]:
    """Read non-filtered signals from last 7 days from gs_signals."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cutoff = (date.today() - timedelta(days=7)).isoformat()
    rows = conn.execute(
        "SELECT signal_id, alert_level, c_tags, headline, affected_deals "
        "FROM gs_signals WHERE created_at >= ? AND status != 'FILTERED' "
        "ORDER BY CAST(weighted_score AS REAL) DESC",
        (cutoff,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_latest_prices() -> tuple:
    """Read latest price snapshot."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT series_data, deltas_30d FROM gs_price_snapshots "
        "ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return {}, {}
    return json.loads(row[0] or "{}"), json.loads(row[1] or "{}")


def _get_open_events() -> list[dict]:
    """Read open binary events from DB."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM gt_binary_events WHERE status='OPEN'"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


REGIME_CONTEXT = {
    "R0": ("R0 Compound Stress -- all stress vectors amplified simultaneously. "
           "Moody's construction phase CDR of 0.94%/yr (8.5x investment grade) "
           "is the baseline before regime amplification."),
    "R1": ("R1 Stagflationary Stress -- construction cost and supply chain "
           "signals lead capital stack recognition by 6-12 months."),
    "R2": ("R2 Credit Stress -- financing market signals lead asset stress. "
           "Monitor lender CDS and BDC gate status as leading indicators."),
    "R3": ("R3 Commodity Shock -- stress test offtaker balance sheet, "
           "not contract language."),
    "R4": ("R4 Policy Tailwind -- alpha window open. Monitor spread "
           "compression as undercapitalized players enter."),
}


def _select_narrative_lead(ds: DealScore) -> str:
    """Select which sub-score leads the narrative. Binary wins tiebreaks."""
    sub = {
        "binary": ds.binary_proximity,
        "signal": ds.signal_pressure,
        "commodity": ds.commodity_exposure,
    }
    top_val = max(sub.values())
    # Tiebreak: binary > signal > commodity
    if sub["binary"] == top_val:
        return "binary"
    if sub["signal"] == top_val:
        return "signal"
    return "commodity"


def _build_narrative(deal: dict, ds: DealScore,
                     closest_event: str, closest_days: int,
                     signals_7d: list = None, prices: dict = None,
                     deltas_30d: dict = None,
                     current_regime: str = "R0") -> tuple:
    """
    Build structured narrative answering:
    1. What is happening to this deal right now?
    2. Why does it matter to the capital stack?
    3. What is the action or watch item?

    Returns (narrative_text, heat_rationale).
    """
    name = deal.get("Deal Name", "Unknown")
    asset = deal.get("Asset Type", "")
    commodities = deal.get("Key Commodities", "")

    # COOL deals get one-liner
    if ds.heat_level == "COOL":
        narrative = (
            f"{name} has no active stress vectors in the current signal set. "
            f"Regime amplifier {current_regime} applies -- monitor for signal emergence."
        )
        rationale = f"No sub-score dominant -- all within normal parameters"
        return narrative, rationale

    lead = _select_narrative_lead(ds)
    parts = []

    # COMPONENT 1: Signal Pressure lead
    if lead == "signal":
        n_matched = ds.matched_signal_count
        n_red = ds.red_signal_count
        top_hl = ds.top_signal_headlines[0] if ds.top_signal_headlines else "market stress signal"
        parts.append(
            f"{n_matched} active signal{'s' if n_matched != 1 else ''} flagged "
            f"against {name} in the last 7 days"
            f"{f', {n_red} at RED alert level' if n_red else ''}. "
            f"Primary stress: {top_hl}."
        )
        parts.append(
            f"Transmission: signal pressure at {ds.signal_pressure:.0f}/25 "
            f"indicates sustained market attention on this deal's "
            f"asset class and commodity exposures."
        )

    # COMPONENT 2: Commodity Exposure lead
    elif lead == "commodity":
        # Find the breached commodity
        comm_list = [c.strip().lower() for c in commodities.split(",") if c.strip()]
        comm_detail = ""
        for c in comm_list[:2]:
            field = COMMODITY_PRICE_MAP.get(c)
            if field and deltas_30d and deltas_30d.get(field) is not None:
                d30 = deltas_30d[field]
                if isinstance(d30, (int, float)) and abs(d30) > 5:
                    comm_detail += f"{c.title()} {d30:+.0f}% 30d. "
        if comm_detail:
            parts.append(
                f"Commodity exposure elevated for {name}: {comm_detail}"
                f"Direct input cost impact on EPC contract assumptions."
            )
        else:
            parts.append(
                f"Commodity exposure score {ds.commodity_exposure:.0f}/25 "
                f"for {name} -- key commodities ({commodities}) showing "
                f"price movement under {current_regime} stress."
            )

    # COMPONENT 3: Binary Event lead
    elif lead == "binary":
        if closest_event and closest_days < 999:
            parts.append(
                f"{closest_event} in T-{closest_days} days is the primary "
                f"action window for {name}."
            )
            parts.append(
                f"Review financial model inputs and credit committee "
                f"assumptions before deadline. Binary outcome directly "
                f"affects capital stack viability."
            )
        else:
            parts.append(
                f"Binary event proximity score {ds.binary_proximity:.0f}/25 "
                f"for {name}."
            )

    # Always append regime context as final sentence
    regime_text = REGIME_CONTEXT.get(current_regime, "")
    if regime_text:
        parts.append(regime_text)

    # Data flags
    if ds.data_flags:
        parts.append(f"[{', '.join(ds.data_flags)} -- scores may be understated]")

    narrative = " ".join(parts)
    rationale = (
        f"{lead.title()} led -- "
        f"SP={ds.signal_pressure:.0f} CE={ds.commodity_exposure:.0f} "
        f"BP={ds.binary_proximity:.0f} RA={ds.regime_amplifier:.0f}"
    )

    return narrative, rationale


def score_deal(deal: dict, signals_7d: list = None,
               prices: dict = None, deltas_30d: dict = None,
               open_events: list = None,
               current_regime: str = "R0") -> DealScore:
    """
    Score a single deal across all four dimensions.

    Returns DealScore with heat_score, heat_level, action_flag,
    narrative, and sub-score breakdown.
    """
    if signals_7d is None:
        signals_7d = _get_signals_last_7d()
    if prices is None or deltas_30d is None:
        prices, deltas_30d = _get_latest_prices()
    if open_events is None:
        open_events = _get_open_events()

    ds = DealScore(
        deal_id=deal.get("Deal ID", ""),
        deal_name=deal.get("Deal Name", ""),
        scored_at=datetime.now().strftime("%Y-%m-%d %H:%M ET"),
    )

    # Sub-scores
    sp, top_ids, sp_flags = score_signal_pressure(deal, signals_7d)
    ce, ce_flags = score_commodity_exposure(deal, prices, deltas_30d)
    bp, closest_ev, closest_days = score_binary_proximity(deal, open_events)
    ra = score_regime_amplifier(current_regime)

    ds.signal_pressure = sp
    ds.commodity_exposure = ce
    ds.binary_proximity = bp
    ds.regime_amplifier = ra
    ds.top_signals = top_ids
    ds.data_flags = sp_flags + ce_flags
    ds.closest_event_name = closest_ev
    ds.closest_event_days = closest_days

    # Enrich with signal context for narrative — deal-specific + SIL filtered
    deal_name = deal.get("Deal Name", "")
    raw_matched = [
        s for s in signals_7d
        if deal_name and deal_name in (s.get("affected_deals") or "")
    ]
    # Apply Sector Intelligence Layer filter
    try:
        from ge.sector_intelligence import filter_signals_for_deal
        matched_sigs, sil_filtered = filter_signals_for_deal(raw_matched, deal)
    except Exception:
        matched_sigs = raw_matched
    ds.matched_signal_count = len(matched_sigs)
    ds.red_signal_count = sum(
        1 for s in matched_sigs if s.get("alert_level") == "RED"
    )
    ds.top_signal_headlines = [
        s.get("headline", "")[:80] for s in matched_sigs[:3]
    ]

    # Heat score
    ds.heat_score = round(sp + ce + bp + ra, 1)

    # Heat level
    if ds.heat_score >= 75:
        ds.heat_level = "HOT"
    elif ds.heat_score >= 45:
        ds.heat_level = "WARM"
    else:
        ds.heat_level = "COOL"

    # Action flag
    if ds.heat_level == "HOT" and closest_days <= 7:
        ds.action_flag = "IMMEDIATE ACTION"
    elif ds.heat_level == "HOT":
        ds.action_flag = "MONITOR DAILY"
    elif ds.heat_level == "WARM" and closest_days <= 30:
        ds.action_flag = "WATCH"
    else:
        ds.action_flag = "ROUTINE"

    # Narrative
    ds.narrative, ds.heat_rationale = _build_narrative(
        deal, ds, closest_ev, closest_days,
        signals_7d, prices, deltas_30d, current_regime,
    )

    return ds


def score_all_deals(current_regime: str = "R0") -> list[DealScore]:
    """
    Score all active/watch pipeline deals. Returns sorted by heat_score desc.
    """
    deals = load_active_deals()
    if not deals:
        return []

    # Load shared data once
    signals_7d = _get_signals_last_7d()
    prices, deltas_30d = _get_latest_prices()
    open_events = _get_open_events()

    scores = []
    for deal in deals:
        ds = score_deal(deal, signals_7d, prices, deltas_30d,
                        open_events, current_regime)
        scores.append(ds)

    scores.sort(key=lambda x: x.heat_score, reverse=True)

    hot = sum(1 for s in scores if s.heat_level == "HOT")
    warm = sum(1 for s in scores if s.heat_level == "WARM")
    cool = sum(1 for s in scores if s.heat_level == "COOL")
    print(f"  GPi: {len(scores)} deals scored — "
          f"HOT {hot} | WARM {warm} | COOL {cool}")

    return scores


# ── STEP 4: DEAL WATCH EMAIL BLOCK ───────────────────────────────────────────

def get_deal_watch_block(scores: list = None) -> str:
    """
    Build formatted text block for email Section 6 (Deal Watch).

    Includes heat level definitions, sub-score breakdown per deal,
    and structured narratives. HOT in full, top 3 WARM with narrative,
    COOL count only.
    """
    if scores is None:
        scores = score_all_deals()

    hot = [s for s in scores if s.heat_level == "HOT"]
    warm = [s for s in scores if s.heat_level == "WARM"]
    cool = [s for s in scores if s.heat_level == "COOL"]

    lines = [
        f"DEAL WATCH -- {len(hot)} HOT | {len(warm)} WARM | {len(cool)} COOL",
        "",
        "HOT (75-100)  Immediate attention. Multiple stress vectors active.",
        "WARM (45-74)  Monitor closely. Stress developing. Review within 7 days.",
        "COOL (0-44)   Normal parameters. Routine monitoring.",
    ]

    def _deal_block(ds, full=True):
        """Format one deal entry."""
        block = [
            "",
            f"  {ds.deal_name:40} HEAT {ds.heat_score:.0f}  |  {ds.action_flag}",
            f"    Signal Pressure:   {ds.signal_pressure:4.0f}/25   "
            f"{ds.matched_signal_count} signals, {ds.red_signal_count} RED",
            f"    Commodity:         {ds.commodity_exposure:4.0f}/25"
            f"{'   ' + ', '.join(ds.data_flags) if ds.data_flags else ''}",
            f"    Binary Event:      {ds.binary_proximity:4.0f}/25"
            f"{'   ' + ds.closest_event_name + ' T-' + str(ds.closest_event_days) + 'd' if ds.closest_event_name and ds.closest_event_days < 999 else ''}",
            f"    Regime:            {ds.regime_amplifier:4.0f}/25   R0 Compound Stress",
        ]
        if full and ds.narrative:
            # Wrap narrative at ~80 chars per line
            words = ds.narrative.split()
            nar_lines = []
            current = "    "
            for w in words:
                if len(current) + len(w) + 1 > 82:
                    nar_lines.append(current)
                    current = "    " + w
                else:
                    current += " " + w if current.strip() else "    " + w
            if current.strip():
                nar_lines.append(current)
            block.extend(nar_lines)
        return block

    if hot:
        lines.append("")
        lines.append("HOT DEALS")
        for ds in hot:
            lines.extend(_deal_block(ds, full=True))

    if warm:
        lines.append("")
        lines.append(f"WARM DEALS (top 3 of {len(warm)})")
        for ds in warm[:3]:
            lines.extend(_deal_block(ds, full=True))
        if len(warm) > 3:
            lines.append("")
            lines.append(f"  + {len(warm) - 3} more WARM deals. "
                         f"Full list in Deal Watch tab.")

    lines.append("")
    lines.append(f"COOL -- {len(cool)} deals within normal parameters. "
                 f"No active stress vectors.")

    return "\n".join(lines)


# ── STEP 5: SHEETS DEAL WATCH TAB ────────────────────────────────────────────

DEAL_WATCH_HEADERS = [
    "Deal Name", "Heat Score", "Heat Level", "Action Flag",
    "Signal Pressure", "Commodity Exposure", "Binary Proximity",
    "Regime Amplifier", "Top Signal", "Narrative",
    "Heat Rationale", "Data Flags", "Scored At",
]

DEAL_WATCH_WIDTHS = {
    0: 220, 1: 80, 2: 70, 3: 130, 4: 100, 5: 110,
    6: 100, 7: 100, 8: 120, 9: 400, 10: 250, 11: 150, 12: 130,
}


def write_deal_watch_to_sheets(scores: list = None):
    """
    Create or overwrite Deal Watch tab in Google Sheets.

    Color rows: HOT = red, WARM = amber, COOL = green.
    Dark theme consistent with other V2 tabs.
    """
    if scores is None:
        scores = score_all_deals()

    try:
        from sheets.interface import (
            _get_sheets_service, _get_sheet_id, _ensure_tab, COLORS
        )
    except ImportError:
        print("  GPi: Sheets interface not available")
        return

    service = _get_sheets_service()
    sheet_id = _get_sheet_id()
    if not service or not sheet_id:
        print("  GPi: Sheets unavailable — Deal Watch not synced")
        return

    tab_name = "Deal Watch"
    tab_id = _ensure_tab(service, sheet_id, tab_name)

    # Build rows
    rows = []
    for ds in scores:
        rows.append([
            ds.deal_name,
            round(ds.heat_score, 1),
            ds.heat_level,
            ds.action_flag,
            round(ds.signal_pressure, 1),
            round(ds.commodity_exposure, 1),
            round(ds.binary_proximity, 1),
            round(ds.regime_amplifier, 1),
            ", ".join(ds.top_signals[:2]) if ds.top_signals else "",
            ds.narrative[:500],
            ds.heat_rationale,
            ", ".join(ds.data_flags) if ds.data_flags else "",
            ds.scored_at,
        ])

    # Clear and write
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id, range=f"'{tab_name}'",
    ).execute()

    all_rows = [DEAL_WATCH_HEADERS] + rows
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'{tab_name}'!A1",
        valueInputOption="RAW",
        body={"values": all_rows},
    ).execute()

    # Formatting
    BG_DARK = {"red": 0.06, "green": 0.06, "blue": 0.06}
    BG_HEADER = {"red": 0.10, "green": 0.10, "blue": 0.18}
    TXT_WHITE = {"red": 0.91, "green": 0.91, "blue": 0.91}
    HOT_BG = {"red": 0.25, "green": 0.06, "blue": 0.06}
    WARM_BG = {"red": 0.25, "green": 0.18, "blue": 0.02}
    COOL_BG = {"red": 0.06, "green": 0.16, "blue": 0.06}

    reqs = []

    # Dark bg + white text on all
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": tab_id},
            "cell": {"userEnteredFormat": {
                "backgroundColor": BG_DARK,
                "textFormat": {"foregroundColor": TXT_WHITE,
                               "fontFamily": "Arial", "fontSize": 10},
                "wrapStrategy": "WRAP",
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat,wrapStrategy)",
        }
    })

    # Header
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
            "cell": {"userEnteredFormat": {
                "backgroundColor": BG_HEADER,
                "textFormat": {"foregroundColor": TXT_WHITE, "bold": True,
                               "fontFamily": "Arial", "fontSize": 10},
                "horizontalAlignment": "CENTER",
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # Freeze header
    reqs.append({
        "updateSheetProperties": {
            "properties": {"sheetId": tab_id,
                           "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount",
        }
    })

    # Column widths
    for col, w in DEAL_WATCH_WIDTHS.items():
        reqs.append({
            "updateDimensionProperties": {
                "range": {"sheetId": tab_id, "dimension": "COLUMNS",
                          "startIndex": col, "endIndex": col + 1},
                "properties": {"pixelSize": w},
                "fields": "pixelSize",
            }
        })

    # Color heat level column (col 2) per value
    level_colors = {"HOT": HOT_BG, "WARM": WARM_BG, "COOL": COOL_BG}
    for i, ds in enumerate(scores):
        bg = level_colors.get(ds.heat_level)
        if bg:
            reqs.append({
                "repeatCell": {
                    "range": {"sheetId": tab_id,
                              "startRowIndex": i + 1, "endRowIndex": i + 2,
                              "startColumnIndex": 2, "endColumnIndex": 3},
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": bg,
                        "textFormat": {"bold": True},
                        "horizontalAlignment": "CENTER",
                    }},
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
                }
            })

    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": reqs},
    ).execute()

    print(f"  GPi: Deal Watch tab written — {len(rows)} deals")


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 58)
    print("GPi PIPELINE AGENT — MODULE TEST")
    print("=" * 58)

    # Test 1: Load active deals
    print("\n1. Loading active deals...")
    deals = load_active_deals()
    print(f"   {len(deals)} deals loaded")
    tagged = sum(1 for d in deals
                 if d.get("C-Tags", "").strip() or d.get("A-Tags", "").strip())
    print(f"   With tags: {tagged}")
    for d in deals[:5]:
        ct = d.get("C-Tags", "")[:20]
        at = d.get("A-Tags", "")[:20]
        print(f"     {d.get('Deal Name','')[:30]:30} C=[{ct}] A=[{at}]")

    # Test 2: Score Project Vega
    print("\n2. Scoring Project Vega...")
    vega = [d for d in deals if "Vega" in d.get("Deal Name", "")]
    if vega:
        ds = score_deal(vega[0])
        print(f"   Heat: {ds.heat_score} ({ds.heat_level}) — {ds.action_flag}")
        print(f"   Signal Pressure:    {ds.signal_pressure}/25")
        print(f"   Commodity Exposure: {ds.commodity_exposure}/25")
        print(f"   Binary Proximity:   {ds.binary_proximity}/25")
        print(f"   Regime Amplifier:   {ds.regime_amplifier}/25")
        print(f"   Top signals: {ds.top_signals}")
        print(f"   Data flags: {ds.data_flags}")
        print(f"   Narrative: {ds.narrative[:120]}")

    # Test 3: Score all deals — top 5
    print("\n3. Scoring all deals...")
    all_scores = score_all_deals()
    print(f"\n   Top 5 by heat score:")
    for ds in all_scores[:5]:
        flags = f" [{','.join(ds.data_flags)}]" if ds.data_flags else ""
        print(f"     {ds.deal_name[:30]:30} HEAT={ds.heat_score:5.1f} "
              f"({ds.heat_level:4}) SP={ds.signal_pressure:4.1f} "
              f"CE={ds.commodity_exposure:4.1f} BP={ds.binary_proximity:4.1f} "
              f"RA={ds.regime_amplifier:4.1f}{flags}")

    # Test 4: Email block
    print("\n4. Deal Watch email block:")
    block = get_deal_watch_block(all_scores)
    print(block)

    # Test 5: Write to Sheets
    print("\n5. Writing Deal Watch to Sheets...")
    write_deal_watch_to_sheets(all_scores)

    print("\ngpi/pipeline_agent.py operational.")