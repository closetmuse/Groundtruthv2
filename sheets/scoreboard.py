"""
GroundTruth V2 — sheets/scoreboard.py
Alpha Scoreboard — Sri's feedback loop closure mechanism.
Binary event outcomes logged here in under 2 minutes.
Hit rate calculated automatically from outcomes vs alert predictions.
Feeds Section 9 of the daily email (Alpha Scoreboard Delta).

Last Updated: April 2026
"""

import os
import sys
import json
from datetime import datetime, date, timedelta
from typing import Optional

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

from sheets.interface import (
    _get_sheets_service, _get_sheet_id, _ensure_tab, COLORS,
)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────

SCOREBOARD_TAB = "Scoreboard"
STATS_TAB      = "Stats"

HEADER_BG = {"red": 0.1, "green": 0.1, "blue": 0.18}   # #1a1a2e

SCOREBOARD_HEADERS = [
    "Event ID", "Event Name", "Event Date", "Resolution Date",
    "Predicted Impact", "Actual Outcome", "Hit (Y/N)",
    "Alert Level", "Linked Deals", "Signal IDs",
    "Days Warning", "Notes", "Logged By", "Logged At",
]

STATS_HEADERS = ["Metric", "Value"]

SCOREBOARD_WIDTHS = {
    0: 100,   # Event ID
    1: 200,   # Event Name
    2: 100,   # Event Date
    3: 110,   # Resolution Date
    4: 350,   # Predicted Impact
    5: 350,   # Actual Outcome
    6: 70,    # Hit
    7: 80,    # Alert Level
    8: 200,   # Linked Deals
    9: 150,   # Signal IDs
    10: 90,   # Days Warning
    11: 250,  # Notes
    12: 100,  # Logged By
    13: 140,  # Logged At
}

SEED_ROW = [
    "TRUMP_APR8",
    "Trump April 8 Tariff Deadline",
    "2026-04-08",
    "2026-04-08",
    "E07 Hormuz window extension, oil price sustained above $100",
    "Pending — outcome not yet logged by Sri",
    "TBD",
    "RED",
    "GT-108, GT-109, Project Vega",
    "GT-041, GT-042, GT-043",
    4,
    "Seed row — Sri to update Actual Outcome and Hit field",
    "System",
    datetime.now().strftime("%Y-%m-%d %H:%M ET"),
]


# ── LOG OUTCOME ───────────────────────────────────────────────────────────────

def log_outcome(event_id: str, event_name: str, event_date: str,
                predicted_impact: str, actual_outcome: str,
                hit: str, alert_level: str = "",
                linked_deals: str = "", signal_ids: str = "",
                days_warning: int = 0, notes: str = "",
                logged_by: str = "Sri"):
    """
    Append one resolved event row to the Scoreboard tab.

    Called by Sri via Claude Desktop or gt/orchestrator.py when a binary
    event resolves. Triggers recalculate_stats() after write.

    Args:
        event_id:         Unique event identifier (e.g. FOMC_APR28).
        event_name:       Human-readable event name.
        event_date:       Date the event occurred (YYYY-MM-DD).
        predicted_impact: What GroundTruth predicted would happen.
        actual_outcome:   What actually happened.
        hit:              "Y", "N", or "TBD".
        alert_level:      RED, AMBER, or GREEN.
        linked_deals:     Comma-separated deal names.
        signal_ids:       Comma-separated signal IDs.
        days_warning:     How many days ahead GT flagged it.
        notes:            Free text.
        logged_by:        Who logged it (default "Sri").
    """
    service = _get_sheets_service()
    sheet_id = _get_sheet_id()
    if not service or not sheet_id:
        print("  Scoreboard: Sheets unavailable — outcome not logged")
        return

    tab_id = _ensure_tab(service, sheet_id, SCOREBOARD_TAB)

    # Check if header exists, write it if tab is empty
    existing = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{SCOREBOARD_TAB}'!A1:A1",
    ).execute()
    if not existing.get("values"):
        # Write header first
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{SCOREBOARD_TAB}'!A1",
            valueInputOption="RAW",
            body={"values": [SCOREBOARD_HEADERS]},
        ).execute()
        _format_header(service, sheet_id, tab_id)

    logged_at = datetime.now().strftime("%Y-%m-%d %H:%M ET")
    row = [
        event_id, event_name, event_date, "",
        predicted_impact, actual_outcome, hit.upper(),
        alert_level, linked_deals, signal_ids,
        days_warning, notes, logged_by, logged_at,
    ]

    # Append row
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"'{SCOREBOARD_TAB}'!A:N",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()

    print(f"  Scoreboard: logged {event_id} — Hit={hit}")

    # Color the new row
    _color_scoreboard_rows(service, sheet_id, tab_id)

    # Recalculate stats
    recalculate_stats()


# ── RECALCULATE STATS ─────────────────────────────────────────────────────────

def recalculate_stats() -> dict:
    """
    Read all Scoreboard rows, compute stats, rewrite the Stats tab.

    Calculates: total events, hits, misses, hit rate, average days warning,
    RED/AMBER breakdown, and per-asset-class hit rates.

    Returns:
        Dict with computed stats for use by email builder.
    """
    service = _get_sheets_service()
    sheet_id = _get_sheet_id()
    if not service or not sheet_id:
        return _empty_stats()

    # Read scoreboard data
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{SCOREBOARD_TAB}'!A:N",
    ).execute()
    rows = result.get("values", [])

    if len(rows) < 2:
        stats = _empty_stats()
        _write_stats_tab(service, sheet_id, stats)
        return stats

    headers = rows[0]
    data = rows[1:]

    # Parse into dicts
    events = []
    for r in data:
        padded = r + [""] * (len(headers) - len(r))
        events.append({headers[i]: padded[i] for i in range(len(headers))})

    # Compute stats
    total = len(events)
    hits = sum(1 for e in events if e.get("Hit (Y/N)", "").upper() == "Y")
    misses = sum(1 for e in events if e.get("Hit (Y/N)", "").upper() == "N")
    tbd = total - hits - misses

    hit_rate = round((hits / (hits + misses)) * 100, 1) if (hits + misses) > 0 else 0.0

    # Days warning average
    day_vals = []
    for e in events:
        try:
            d = int(e.get("Days Warning", 0))
            if d > 0:
                day_vals.append(d)
        except (ValueError, TypeError):
            pass
    avg_days = round(sum(day_vals) / len(day_vals), 1) if day_vals else 0.0

    # RED/AMBER breakdown
    red_events = [e for e in events if e.get("Alert Level", "").upper() == "RED"]
    amber_events = [e for e in events if e.get("Alert Level", "").upper() == "AMBER"]
    red_hits = sum(1 for e in red_events if e.get("Hit (Y/N)", "").upper() == "Y")
    red_resolved = sum(1 for e in red_events if e.get("Hit (Y/N)", "").upper() in ("Y", "N"))
    amber_hits = sum(1 for e in amber_events if e.get("Hit (Y/N)", "").upper() == "Y")
    amber_resolved = sum(1 for e in amber_events if e.get("Hit (Y/N)", "").upper() in ("Y", "N"))

    red_rate = round((red_hits / red_resolved) * 100, 1) if red_resolved > 0 else 0.0
    amber_rate = round((amber_hits / amber_resolved) * 100, 1) if amber_resolved > 0 else 0.0

    # Per-deal breakdown
    deal_stats = {}
    for e in events:
        deals = e.get("Linked Deals", "")
        hit_val = e.get("Hit (Y/N)", "").upper()
        if hit_val not in ("Y", "N"):
            continue
        for deal in deals.split(","):
            deal = deal.strip()
            if not deal:
                continue
            if deal not in deal_stats:
                deal_stats[deal] = {"hits": 0, "total": 0}
            deal_stats[deal]["total"] += 1
            if hit_val == "Y":
                deal_stats[deal]["hits"] += 1

    stats = {
        "total": total,
        "hits": hits,
        "misses": misses,
        "tbd": tbd,
        "hit_rate": hit_rate,
        "avg_days_warning": avg_days,
        "red_hit_rate": red_rate,
        "amber_hit_rate": amber_rate,
        "deal_stats": deal_stats,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M ET"),
    }

    _write_stats_tab(service, sheet_id, stats)
    print(f"  Stats: {total} events, {hits} hits, {misses} misses, "
          f"rate={hit_rate}%, avg warning={avg_days}d")

    return stats


def _empty_stats() -> dict:
    """Return zeroed stats dict."""
    return {
        "total": 0, "hits": 0, "misses": 0, "tbd": 0,
        "hit_rate": 0.0, "avg_days_warning": 0.0,
        "red_hit_rate": 0.0, "amber_hit_rate": 0.0,
        "deal_stats": {},
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M ET"),
    }


def _write_stats_tab(service, sheet_id: str, stats: dict):
    """Write the Stats tab from computed stats dict."""
    tab_id = _ensure_tab(service, sheet_id, STATS_TAB)

    rows = [
        STATS_HEADERS,
        ["Total Events Logged", stats["total"]],
        ["Hits (Y)", stats["hits"]],
        ["Misses (N)", stats["misses"]],
        ["Pending (TBD)", stats["tbd"]],
        ["Hit Rate %", f"{stats['hit_rate']}%"],
        ["Avg Days Warning", stats["avg_days_warning"]],
        ["RED Alert Hit Rate %", f"{stats['red_hit_rate']}%"],
        ["AMBER Alert Hit Rate %", f"{stats['amber_hit_rate']}%"],
        ["Last Updated", stats["last_updated"]],
        [],  # separator
        ["--- Deal Breakdown ---", ""],
    ]

    for deal, ds in sorted(stats.get("deal_stats", {}).items()):
        rate = round((ds["hits"] / ds["total"]) * 100, 1) if ds["total"] > 0 else 0
        rows.append([deal, f"{rate}% ({ds['hits']}/{ds['total']})"])

    # Clear and write
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range=f"'{STATS_TAB}'",
    ).execute()

    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'{STATS_TAB}'!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()

    # Format header
    requests = [
        {
            "repeatCell": {
                "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "backgroundColor": HEADER_BG,
                    }
                },
                "fields": "userEnteredFormat(textFormat,backgroundColor)",
            }
        },
        {
            "updateSheetProperties": {
                "properties": {"sheetId": tab_id, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        },
        {
            "updateDimensionProperties": {
                "range": {"sheetId": tab_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                "properties": {"pixelSize": 250},
                "fields": "pixelSize",
            }
        },
        {
            "updateDimensionProperties": {
                "range": {"sheetId": tab_id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
                "properties": {"pixelSize": 200},
                "fields": "pixelSize",
            }
        },
    ]
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": requests},
    ).execute()


# ── SCOREBOARD DELTA ──────────────────────────────────────────────────────────

def get_scoreboard_delta(since_date: str = None) -> dict:
    """
    Return new hits and misses since a given date.

    Called by gt/email_builder.py for Section 9 of email.

    Args:
        since_date: ISO date string (YYYY-MM-DD). Defaults to 7 days ago.

    Returns:
        Dict with: new_hits, new_misses, new_tbd, events (list of dicts).
    """
    if not since_date:
        since_date = (date.today() - timedelta(days=7)).isoformat()

    service = _get_sheets_service()
    sheet_id = _get_sheet_id()
    if not service or not sheet_id:
        return {"new_hits": 0, "new_misses": 0, "new_tbd": 0, "events": []}

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{SCOREBOARD_TAB}'!A:N",
        ).execute()
        rows = result.get("values", [])

        if len(rows) < 2:
            return {"new_hits": 0, "new_misses": 0, "new_tbd": 0, "events": []}

        headers = rows[0]
        data = rows[1:]

        recent = []
        for r in data:
            padded = r + [""] * (len(headers) - len(r))
            event = {headers[i]: padded[i] for i in range(len(headers))}

            logged_at = event.get("Logged At", "")[:10]
            if logged_at >= since_date:
                recent.append(event)

        new_hits = sum(1 for e in recent if e.get("Hit (Y/N)", "").upper() == "Y")
        new_misses = sum(1 for e in recent if e.get("Hit (Y/N)", "").upper() == "N")
        new_tbd = len(recent) - new_hits - new_misses

        return {
            "new_hits": new_hits,
            "new_misses": new_misses,
            "new_tbd": new_tbd,
            "events": recent,
        }

    except Exception as e:
        print(f"  Scoreboard delta failed: {e}")
        return {"new_hits": 0, "new_misses": 0, "new_tbd": 0, "events": []}


# ── FORMATTING HELPERS ────────────────────────────────────────────────────────

def _format_header(service, sheet_id: str, tab_id: int):
    """Apply bold, frozen, dark header to the Scoreboard tab."""
    requests = [
        {
            "repeatCell": {
                "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "backgroundColor": HEADER_BG,
                    }
                },
                "fields": "userEnteredFormat(textFormat,backgroundColor)",
            }
        },
        {
            "updateSheetProperties": {
                "properties": {"sheetId": tab_id, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        },
    ]
    # Column widths
    for col_idx, width in SCOREBOARD_WIDTHS.items():
        requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": tab_id, "dimension": "COLUMNS",
                          "startIndex": col_idx, "endIndex": col_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": requests},
    ).execute()


def _color_scoreboard_rows(service, sheet_id: str, tab_id: int):
    """Color scoreboard rows: green for Hit=Y, red for Hit=N."""
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{SCOREBOARD_TAB}'!G:G",
    ).execute()
    col_values = result.get("values", [])

    requests = []
    for i, cell in enumerate(col_values):
        if i == 0:
            continue  # skip header
        val = cell[0].upper().strip() if cell else ""
        if val == "Y":
            color = COLORS["GREEN"]
        elif val == "N":
            color = COLORS["RED"]
        else:
            continue

        requests.append({
            "repeatCell": {
                "range": {"sheetId": tab_id, "startRowIndex": i, "endRowIndex": i + 1},
                "cell": {"userEnteredFormat": {"backgroundColor": color}},
                "fields": "userEnteredFormat.backgroundColor",
            }
        })

    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id, body={"requests": requests},
        ).execute()


def _seed_scoreboard(service, sheet_id: str):
    """Write header + seed row if Scoreboard tab is empty."""
    tab_id = _ensure_tab(service, sheet_id, SCOREBOARD_TAB)

    existing = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{SCOREBOARD_TAB}'!A:A",
    ).execute()
    if len(existing.get("values", [])) > 1:
        print(f"  Scoreboard already has data — skipping seed")
        return

    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'{SCOREBOARD_TAB}'!A1",
        valueInputOption="RAW",
        body={"values": [SCOREBOARD_HEADERS, SEED_ROW]},
    ).execute()

    _format_header(service, sheet_id, tab_id)
    print(f"  Scoreboard seeded: header + 1 seed row")


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("SHEETS SCOREBOARD — MODULE TEST")
    print("=" * 55)

    creds_path = os.getenv("GROUNDTRUTH_SHEETS_CREDENTIALS", "")
    sheet_id_val = os.getenv("GROUNDTRUTH_SHEET_ID", "")

    # Test 1: Credentials check
    print("\n1. Testing credentials...")
    if creds_path and os.path.exists(creds_path):
        print(f"   OK — credentials: {creds_path}")
    else:
        print(f"   SKIP — GROUNDTRUTH_SHEETS_CREDENTIALS not set")
    if sheet_id_val:
        print(f"   OK — sheet ID: {sheet_id_val[:20]}...")
    else:
        print(f"   SKIP — GROUNDTRUTH_SHEET_ID not set")

    # Test 2: recalculate_stats on empty/seed data
    print("\n2. Testing recalculate_stats (no divide-by-zero)...")
    empty = _empty_stats()
    assert empty["hit_rate"] == 0.0
    assert empty["total"] == 0
    print(f"   Empty stats: rate={empty['hit_rate']}%, total={empty['total']} — OK")

    # Test 3: Dry run
    print("\n3. Dry run — seed row preview:")
    print(f"   Headers ({len(SCOREBOARD_HEADERS)}): {SCOREBOARD_HEADERS[:5]}...")
    print(f"   Seed row: {SEED_ROW[:4]}...")
    print(f"   Hit: {SEED_ROW[6]}, Alert: {SEED_ROW[7]}, Days Warning: {SEED_ROW[10]}")

    # Test 4: Live seed
    print("\n4. Testing live seed + recalculate...")
    if creds_path and os.path.exists(creds_path) and sheet_id_val:
        service = _get_sheets_service()
        _seed_scoreboard(service, sheet_id_val)
        stats = recalculate_stats()
        print(f"   Stats: total={stats['total']}, hits={stats['hits']}, "
              f"misses={stats['misses']}, tbd={stats['tbd']}, "
              f"rate={stats['hit_rate']}%")
    else:
        print("   SKIP — credentials not configured")

    # Test 5: get_scoreboard_delta
    print("\n5. Testing get_scoreboard_delta (last 7 days)...")
    if creds_path and os.path.exists(creds_path) and sheet_id_val:
        delta = get_scoreboard_delta()
        print(f"   New hits: {delta['new_hits']}")
        print(f"   New misses: {delta['new_misses']}")
        print(f"   New TBD: {delta['new_tbd']}")
        print(f"   Events: {len(delta['events'])}")
    else:
        print("   SKIP — credentials not configured")

    print("\nsheets/scoreboard.py operational.")