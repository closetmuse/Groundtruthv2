"""
GroundTruth V2 — sheets/interface.py
Google Sheets signal browser interface.
Reads from SQLite groundtruth.db, writes to Google Sheets.
Called by gt/orchestrator.py at end of daily run, or standalone for manual sync.

ONE-TIME SETUP:
  1. Go to https://console.cloud.google.com/
     Create a project (or reuse existing).
     Enable "Google Sheets API" and "Google Drive API".

  2. Go to IAM & Admin > Service Accounts.
     Create a service account (e.g. "groundtruth-sheets").
     Create a JSON key — download it to GroundTruth_v2/ folder.

  3. Open your target Google Sheet in browser.
     Click Share > add the service account email
     (e.g. groundtruth-sheets@project.iam.gserviceaccount.com)
     as Editor.

  4. Set environment variables in GroundTruth_v2/.env:
       GROUNDTRUTH_SHEETS_CREDENTIALS=path/to/service-account.json
       GROUNDTRUTH_SHEET_ID=your-google-sheet-id-here

DEPENDENCIES:
  pip install google-auth google-auth-httplib2 google-api-python-client

Last Updated: April 2026
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, date
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

DB_PATH         = os.path.join(PROJECT_ROOT, "groundtruth.db")
CREDENTIALS_VAR = "GROUNDTRUTH_SHEETS_CREDENTIALS"
SHEET_ID_VAR    = "GROUNDTRUTH_SHEET_ID"

# ── ALERT LEVEL COLORS (Google Sheets RGB 0-1 scale) ─────────────────────────

COLORS = {
    "RED":   {"red": 0.3, "green": 0.08, "blue": 0.08},   # soft red bg
    "AMBER": {"red": 0.3, "green": 0.22, "blue": 0.02},   # soft amber bg
    "GREEN": {"red": 0.08, "green": 0.2, "blue": 0.08},   # soft green bg
    "HEADER": {"red": 0.15, "green": 0.15, "blue": 0.15},  # dark header
    "DEFAULT": {"red": 1, "green": 1, "blue": 1},           # white
}


# ── SYNC RESULT ───────────────────────────────────────────────────────────────

@dataclass
class SyncResult:
    """Result of a Sheets sync operation."""
    success: bool = False
    signals_written: int = 0
    prices_written: int = 0
    binary_events_written: int = 0
    meta_written: bool = False
    errors: list = field(default_factory=list)
    timestamp: str = ""


# ── GOOGLE SHEETS AUTH ────────────────────────────────────────────────────────

def _get_sheets_service():
    """
    Authenticate with Google Sheets API using service account credentials.

    Uses the JSON key file specified by GROUNDTRUTH_SHEETS_CREDENTIALS env var.
    Returns None with a descriptive message if credentials are missing.
    """
    creds_path = os.getenv(CREDENTIALS_VAR, "")
    if not creds_path or not os.path.exists(creds_path):
        print(f"  WARN: {CREDENTIALS_VAR} not set or file not found.")
        print(f"  Current value: '{creds_path}'")
        print(f"  Set in .env: {CREDENTIALS_VAR}=path/to/service-account.json")
        return None

    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        service = build("sheets", "v4", credentials=creds)
        return service
    except ImportError:
        print("  Google API dependencies not installed. Run:")
        print("  pip install google-auth google-auth-httplib2 google-api-python-client")
        return None
    except Exception as e:
        print(f"  Sheets auth failed: {e}")
        return None


def _get_sheet_id() -> Optional[str]:
    """Get the target Google Sheet ID from env."""
    sheet_id = os.getenv(SHEET_ID_VAR, "")
    if not sheet_id:
        print(f"  WARN: {SHEET_ID_VAR} not set in .env")
        return None
    return sheet_id


# ── DB READERS ────────────────────────────────────────────────────────────────

def _derive_a_tags(c_tags_json: str) -> str:
    """Derive A-tags from C-tags using the same mapping as gs/classify.py."""
    C_TO_A = {
        "C05": ["A01", "A12", "A14"], "C06": ["A04"], "C07": ["A06", "A07"],
        "C10": ["A05"], "C11": ["A09"], "C15": ["A17"],
    }
    try:
        c_tags = json.loads(c_tags_json or "[]")
        a_set = set()
        for ct in c_tags:
            for at in C_TO_A.get(ct, []):
                a_set.add(at)
        return json.dumps(sorted(a_set)) if a_set else ""
    except Exception:
        return ""


def _read_signals() -> list[list]:
    """
    Read all signals from gs_signals, most recent first.

    Returns list of rows where each row is a list of cell values
    matching the Signals tab column order.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM gs_signals ORDER BY id DESC"
    ).fetchall()
    conn.close()

    result = []
    import pytz
    utc = pytz.utc
    et = pytz.timezone("America/New_York")

    for r in rows:
        r = dict(r)
        created = r.get("created_at", "")
        # Convert UTC → ET for display
        et_date = created[:10]
        et_time = created[11:19] if len(created) >= 19 else ""
        try:
            from datetime import datetime as _dt
            utc_dt = _dt.fromisoformat(created.replace("Z", "+00:00"))
            if utc_dt.tzinfo is None:
                utc_dt = utc.localize(utc_dt)
            et_dt = utc_dt.astimezone(et)
            et_date = et_dt.strftime("%Y-%m-%d")
            et_time = et_dt.strftime("%H:%M:%S ET")
        except Exception:
            pass
        result.append([
            r.get("signal_id", ""),
            et_date,                                                         # Date YYYY-MM-DD ET
            et_time,                                                         # Time HH:MM:SS ET
            r.get("fetch_run_id", ""),                                       # Run ID
            r.get("alert_level", ""),
            r.get("headline", ""),
            r.get("c_tags", ""),
            _derive_a_tags(r.get("c_tags", "")),                             # A-tags derived from C-tags
            r.get("t_tag", ""),
            r.get("o_tag", ""),
            r.get("source_name", ""),
            r.get("f_tags", ""),
            round(r.get("confidence", 0) or 0, 2),
            r.get("affected_deals", ""),
            r.get("second_order", ""),
            r.get("status", ""),
            "Yes" if r.get("is_verified") else "",
        ])
    return result


def _read_prices() -> list[list]:
    """
    Read latest price snapshot. Standard series + RTO DA with full metadata.
    Returns rows matching PRICE_HEADERS (13 columns).
    """
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT series_data, deltas_7d, deltas_30d, deltas_90d, breaches "
        "FROM gs_price_snapshots ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if not row:
        return []

    series = json.loads(row[0] or "{}")
    d7 = json.loads(row[1] or "{}")
    d30 = json.loads(row[2] or "{}")
    breaches = {b["field"] for b in json.loads(row[4] or "[]")}

    result = []

    # Standard series (non-RTO)
    std_keys = sorted([k for k in series if '_da' not in k and series[k] is not None])
    for k in std_keys:
        data = series[k]
        if not isinstance(data, dict):
            continue
        val = data.get("value", "")
        unit = data.get("unit", "")
        pub = data.get("publication_date", data.get("series_date", ""))
        stale = data.get("staleness_days", 0)
        v7 = d7.get(k)
        v30 = d30.get(k)
        name = k
        if isinstance(stale, int) and stale > 3:
            name = f"{k} STALE"
        result.append([
            name, pub, f"{val} {unit}".strip(),
            "", "", "", "", "", "", "",  # Market through Curtailment blank
            round(v7, 2) if isinstance(v7, (int, float)) else "",
            round(v30, 2) if isinstance(v30, (int, float)) else "",
            "BREACHED" if k in breaches else "",
        ])

    # RTO DA series — full metadata
    rto_keys = sorted([k for k in series if '_da' in k and series[k] is not None])
    if rto_keys:
        result.append(["-- RTO POWER (Day-Ahead) --"] + [""] * 12)

    for k in rto_keys:
        data = series[k]
        if not isinstance(data, dict):
            continue
        display = k.replace("_da", "").replace("_", " ").upper()
        v7 = d7.get(k)
        v30 = d30.get(k)
        result.append([
            display,
            data.get("date", ""),
            f"${data.get('value', '')}/MWh",
            f"DA | {data.get('date', '')}",
            f"${data.get('da_peak_avg', '')}" if data.get("da_peak_avg") else "",
            f"${data.get('da_offpeak_avg', '')}" if data.get("da_offpeak_avg") else "",
            f"${data.get('peak_offpeak_spread', '')}" if data.get("peak_offpeak_spread") is not None else "",
            str(data.get("negative_price_hours", "")) if data.get("negative_price_hours") is not None else "",
            data.get("bess_signal", ""),
            data.get("curtailment_signal", ""),
            round(v7, 2) if isinstance(v7, (int, float)) else "",
            round(v30, 2) if isinstance(v30, (int, float)) else "",
            "BREACHED" if k in breaches else "",
        ])

    return result


PRICE_HISTORY_HEADERS = [
    "Run Timestamp", "Run ID", "Trigger",
    "Series Key", "Category", "Display Name",
    "Value", "Unit", "Series Date",
    "DA Peak Avg", "DA Off-Peak Avg", "Spread $/MWh",
    "Neg Price Hrs", "DA High", "DA Low",
    "BESS Signal", "Curtailment Signal", "Scarcity Signal",
    "Delta 7d", "Delta 30d",
    "Breach",
]

_SERIES_DISPLAY = {
    "wti_usd_bbl": "WTI Crude", "brent_usd_bbl": "Brent Crude",
    "henry_hub_usd_mmbtu": "Henry Hub Gas", "sofr_pct": "SOFR",
    "ust_2y_pct": "2Y Treasury", "ust_5y_pct": "5Y Treasury",
    "ust_10y_pct": "10Y Treasury", "ust_30y_pct": "30Y Treasury",
    "bbb_oas_bps": "BBB Spread", "hy_spread_bps": "HY Spread",
    "usd_index": "USD Index", "usd_eur": "EUR/USD",
    "usd_jpy": "USD/JPY", "usd_gbp": "GBP/USD",
    "aluminum_usd_mt": "Aluminum", "copper_usd_mt": "Copper",
    "steel_hrc_usd_st": "Steel HRC (CME)",
    "steel_hrc_index": "Steel HRC (PPI)",
}


def _append_price_history(service, sheet_id: str,
                          run_id: str = "", trigger: str = "scheduled") -> int:
    """
    Append one row PER SERIES per run to Price History tab.
    Never clears — pure append. Creates tab + header on first call.
    """
    tab_name = "Price History"
    tab_id = _ensure_tab(service, sheet_id, tab_name)

    # Check if header exists
    existing = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"'{tab_name}'!A1:A2",
    ).execute()
    first_run = not existing.get("values")

    if first_run:
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=f"'{tab_name}'!A1",
            valueInputOption="RAW",
            body={"values": [PRICE_HISTORY_HEADERS]},
        ).execute()
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [
                {"repeatCell": {
                    "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": COLORS["HEADER"],
                        "textFormat": {"fontFamily": "Calibri", "fontSize": 12,
                                       "bold": True,
                                       "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    }},
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }},
                {"updateSheetProperties": {
                    "properties": {"sheetId": tab_id,
                                   "gridProperties": {"frozenRowCount": 1}},
                    "fields": "gridProperties.frozenRowCount",
                }},
            ]},
        ).execute()
        _create_price_history_chart(service, sheet_id, tab_id)

    # Read latest snapshot
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT series_data, deltas_7d, deltas_30d, breaches "
        "FROM gs_price_snapshots ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return 0

    series = json.loads(row[0] or "{}")
    d7 = json.loads(row[1] or "{}")
    d30 = json.loads(row[2] or "{}")
    breaches_raw = json.loads(row[3] or "[]")
    breach_set = {b.get("field", "") for b in breaches_raw}

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S ET")
    new_rows = []

    for key in sorted(series.keys()):
        data = series[key]
        if data is None or not isinstance(data, dict):
            continue

        is_rto = "_da" in key
        display = _SERIES_DISPLAY.get(key) or key.replace("_da", "").replace("_", " ").upper()
        category = data.get("category", "")
        val = data.get("value", "")
        unit = data.get("unit", "")
        sdate = data.get("series_date", data.get("date", data.get("publication_date", "")))

        new_rows.append([
            ts, run_id or "", trigger or "scheduled",
            key, category, display,
            val, unit, sdate,
            data.get("da_peak_avg", "") if is_rto else "",
            data.get("da_offpeak_avg", "") if is_rto else "",
            data.get("peak_offpeak_spread", "") if is_rto else "",
            data.get("negative_price_hours", "") if is_rto else "",
            data.get("da_high", "") if is_rto else "",
            data.get("da_low", "") if is_rto else "",
            data.get("bess_signal", "") if is_rto else "",
            data.get("curtailment_signal", "") if is_rto else "",
            data.get("scarcity_signal", "") if is_rto else "",
            round(d7.get(key), 2) if isinstance(d7.get(key), (int, float)) else "",
            round(d30.get(key), 2) if isinstance(d30.get(key), (int, float)) else "",
            "BREACHED" if key in breach_set else "",
        ])

    if new_rows:
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range=f"'{tab_name}'!A:A",
            valueInputOption="RAW", insertDataOption="INSERT_ROWS",
            body={"values": new_rows},
        ).execute()

    print(f"    Price History: {len(new_rows)} rows appended")
    return len(new_rows)


def _create_price_history_chart(service, sheet_id: str, tab_id: int):
    """No-op — chart via Sheets filter on Series Key column."""
    pass


def _read_binary_events() -> list[list]:
    """
    Read all binary events from gt_binary_events with days_remaining.

    Returns list of rows: event_id, name, deadline, days_remaining,
    linked_deals, status, outcome, encyclopedia_trigger.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM gt_binary_events ORDER BY deadline ASC"
    ).fetchall()
    conn.close()

    result = []
    today = date.today()
    for r in rows:
        r = dict(r)
        days_remaining = ""
        try:
            dl = datetime.strptime(r.get("deadline", ""), "%Y-%m-%d").date()
            days_remaining = (dl - today).days
        except Exception:
            pass

        deals = r.get("linked_deals", "")
        try:
            deals = ", ".join(json.loads(deals)) if deals else ""
        except Exception:
            pass

        result.append([
            r.get("event_id", ""),
            r.get("name", ""),
            r.get("deadline", ""),
            days_remaining,
            deals,
            r.get("status", ""),
            r.get("outcome", ""),
            r.get("encyclopedia_trigger", ""),
        ])
    return result


def _build_meta() -> list[list]:
    """
    Build meta tab data: last sync, signal count, price count, status.
    """
    conn = sqlite3.connect(DB_PATH)
    sig_count = conn.execute("SELECT COUNT(*) FROM gs_signals").fetchone()[0]
    price_count = conn.execute("SELECT COUNT(*) FROM gs_price_snapshots").fetchone()[0]
    event_count = conn.execute("SELECT COUNT(*) FROM gt_binary_events").fetchone()[0]
    latency_count = conn.execute("SELECT COUNT(*) FROM ge_latency_events").fetchone()[0]
    conn.close()

    return [
        ["Last Sync", datetime.now().strftime("%Y-%m-%d %H:%M:%S ET")],
        ["Signal Count", sig_count],
        ["Price Snapshots", price_count],
        ["Binary Events", event_count],
        ["Latency Events", latency_count],
        ["System Status", "Operational"],
        ["Phase", "Phase 6"],
        ["Scheduler", "GroundTruth_DailyRun — daily 06:00 ET"],
        ["Digest URL", _get_digest_url()],
    ]


def _get_digest_url() -> str:
    """Read permanent Drive digest URL from marker file."""
    marker = os.path.join(PROJECT_ROOT, ".drive_digest_id")
    if os.path.exists(marker):
        with open(marker) as f:
            fid = f.read().strip()
        return f"https://drive.google.com/file/d/{fid}/view"
    return ""


# ── SHEET WRITERS ─────────────────────────────────────────────────────────────

SIGNAL_HEADERS = [
    "ID", "Date", "Captured At", "Run ID", "Alert", "Headline", "C-Tags", "A-Tags",
    "T-Tag", "O-Tag", "Source", "F-Tag", "Confidence",
    "Deals", "Second Order", "Status", "Verified",
]

PRICE_HEADERS = [
    "Series", "Date", "Value", "Market",
    "Peak Avg", "Off-Peak Avg", "Spread", "Neg Hrs",
    "BESS Signal", "Curtailment",
    "Delta 7d", "Delta 30d", "Threshold",
]

BINARY_HEADERS = [
    "Event ID", "Name", "Deadline", "Days Remaining",
    "Linked Deals", "Status", "Outcome", "Encyclopedia Trigger",
]

META_HEADERS = ["Field", "Value"]

# Column widths in pixels
SIGNAL_WIDTHS = {
    0: 80, 1: 90, 2: 140, 3: 130, 4: 60, 5: 400, 6: 120, 7: 100,
    8: 50, 9: 50, 10: 140, 11: 60, 12: 80, 13: 180, 14: 500, 15: 80, 16: 60,
}


def _ensure_tab(service, sheet_id: str, tab_name: str) -> int:
    """
    Ensure a tab exists in the sheet. Create it if missing.

    Returns the sheetId (int) of the tab.
    """
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    for sheet in meta.get("sheets", []):
        props = sheet.get("properties", {})
        if props.get("title") == tab_name:
            return props["sheetId"]

    # Create the tab
    body = {
        "requests": [{
            "addSheet": {"properties": {"title": tab_name}}
        }]
    }
    resp = service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body=body
    ).execute()
    new_id = resp["replies"][0]["addSheet"]["properties"]["sheetId"]
    print(f"    Created tab: {tab_name} (id={new_id})")
    return new_id


def _write_tab(service, sheet_id: str, tab_name: str,
               headers: list, rows: list,
               widths: dict = None, color_col: int = None) -> int:
    """
    Write headers + data to a tab. Clears existing content first.

    Bolds and freezes header row. Optionally sets column widths and
    applies row background colors based on a color column value.

    Args:
        service: Google Sheets API service.
        sheet_id: Spreadsheet ID.
        tab_name: Tab/sheet name.
        headers: List of header strings.
        rows: List of row lists.
        widths: Optional dict of column_index -> width in pixels.
        color_col: Optional column index whose value determines row color
                   (expects "RED", "AMBER", "GREEN").

    Returns:
        Number of data rows written.
    """
    tab_id = _ensure_tab(service, sheet_id, tab_name)

    # Clear the tab
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range=f"'{tab_name}'",
    ).execute()

    # Write headers + data
    all_rows = [headers] + rows
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'{tab_name}'!A1",
        valueInputOption="RAW",
        body={"values": all_rows},
    ).execute()

    # Build formatting requests
    requests = []

    # a. Bold header row — Calibri 12, dark bg, white text
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": tab_id,
                "startRowIndex": 0, "endRowIndex": 1,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "fontFamily": "Calibri",
                        "fontSize": 12,
                        "bold": True,
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                    },
                    "backgroundColor": COLORS["HEADER"],
                }
            },
            "fields": "userEnteredFormat(textFormat,backgroundColor)",
        }
    })

    # b. Freeze header row
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": tab_id,
                "gridProperties": {"frozenRowCount": 1},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    })

    # c. Column widths
    if widths:
        for col_idx, width in widths.items():
            requests.append({
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": col_idx,
                        "endIndex": col_idx + 1,
                    },
                    "properties": {"pixelSize": width},
                    "fields": "pixelSize",
                }
            })

    # d. White Calibri 12 base for ALL data rows (before color override)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": tab_id,
                "startRowIndex": 1,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 1, "green": 1, "blue": 1},
                    "textFormat": {
                        "fontFamily": "Calibri",
                        "fontSize": 12,
                        "bold": False,
                        "foregroundColor": {"red": 0, "green": 0, "blue": 0},
                    },
                    "verticalAlignment": "TOP",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)",
        }
    })

    # e. Row colors by alert level (overrides white base on specific cells)
    if color_col is not None:
        for i, row in enumerate(rows):
            if len(row) > color_col:
                level = str(row[color_col]).upper()
                if level in COLORS:
                    requests.append({
                        "repeatCell": {
                            "range": {
                                "sheetId": tab_id,
                                "startRowIndex": i + 1,  # +1 for header
                                "endRowIndex": i + 2,
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": COLORS[level],
                                }
                            },
                            "fields": "userEnteredFormat.backgroundColor",
                        }
                    })

    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": requests},
        ).execute()

    return len(rows)


# ── PUBLIC FUNCTIONS ──────────────────────────────────────────────────────────

def sync_all(run_id: str = "", trigger: str = "scheduled") -> SyncResult:
    """
    Write all tabs to Google Sheets: Signals, Prices, Binary Events, Meta,
    and append to Price History.

    Called by gt/orchestrator.py at end of daily run.
    Clears refresh tabs before rewriting. Price History is append-only.
    Returns SyncResult with counts and any errors.
    """
    result = SyncResult(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S ET"))

    service = _get_sheets_service()
    sheet_id = _get_sheet_id()

    if not service or not sheet_id:
        result.errors.append("Sheets service or sheet ID unavailable")
        print(f"  Sync aborted: {result.errors}")
        return result

    print(f"\n  Syncing to Google Sheet: {sheet_id[:20]}...")

    # Tab 1: Signals
    try:
        sig_rows = _read_signals()
        n = _write_tab(service, sheet_id, "Signals",
                       SIGNAL_HEADERS, sig_rows,
                       widths=SIGNAL_WIDTHS, color_col=4)
        result.signals_written = n
        print(f"    Signals: {n} rows")
    except Exception as e:
        result.errors.append(f"Signals tab: {e}")
        print(f"    Signals FAILED: {e}")

    # Tab 2: Prices
    try:
        price_rows = _read_prices()
        n = _write_tab(service, sheet_id, "Prices",
                       PRICE_HEADERS, price_rows)
        result.prices_written = n
        print(f"    Prices: {n} rows")
    except Exception as e:
        result.errors.append(f"Prices tab: {e}")
        print(f"    Prices FAILED: {e}")

    # Tab 3: Binary Events
    try:
        event_rows = _read_binary_events()
        n = _write_tab(service, sheet_id, "Binary Events",
                       BINARY_HEADERS, event_rows)
        result.binary_events_written = n
        print(f"    Binary Events: {n} rows")
    except Exception as e:
        result.errors.append(f"Binary Events tab: {e}")
        print(f"    Binary Events FAILED: {e}")

    # Tab 4: Meta
    try:
        meta_rows = _build_meta()
        _write_tab(service, sheet_id, "Meta",
                   META_HEADERS, meta_rows)
        result.meta_written = True
        print(f"    Meta: {len(meta_rows)} rows")
    except Exception as e:
        result.errors.append(f"Meta tab: {e}")
        print(f"    Meta FAILED: {e}")

    # Tab 5: Price History (append-only — never clears)
    try:
        _append_price_history(service, sheet_id, run_id=run_id, trigger=trigger)
    except Exception as e:
        result.errors.append(f"Price History tab: {e}")
        print(f"    Price History FAILED: {e}")

    result.success = len(result.errors) == 0
    status = "COMPLETE" if result.success else f"PARTIAL ({len(result.errors)} errors)"
    print(f"  Sync {status}")
    return result


def sync_signals_only() -> SyncResult:
    """
    Write only the Signals tab to Google Sheets.

    Lightweight sync for breaking signal runs where only
    the signal table needs updating.
    """
    result = SyncResult(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S ET"))

    service = _get_sheets_service()
    sheet_id = _get_sheet_id()

    if not service or not sheet_id:
        result.errors.append("Sheets service or sheet ID unavailable")
        return result

    try:
        sig_rows = _read_signals()
        n = _write_tab(service, sheet_id, "Signals",
                       SIGNAL_HEADERS, sig_rows,
                       widths=SIGNAL_WIDTHS, color_col=4)
        result.signals_written = n
        result.success = True
        print(f"  Signals synced: {n} rows")
    except Exception as e:
        result.errors.append(f"Signals tab: {e}")
        print(f"  Signals sync FAILED: {e}")

    return result


# ── DRY RUN ───────────────────────────────────────────────────────────────────

def dry_run():
    """
    Print what would be written to Sheets without hitting the API.

    Reads all data from SQLite and prints row counts and sample data.
    """
    print("=" * 55)
    print("SHEETS INTERFACE — DRY RUN")
    print("=" * 55)

    # Signals
    sig_rows = _read_signals()
    print(f"\nSignals tab: {len(sig_rows)} rows")
    print(f"  Headers: {SIGNAL_HEADERS}")
    if sig_rows:
        print(f"  First row: {sig_rows[0][:6]}...")

    # Prices
    price_rows = _read_prices()
    print(f"\nPrices tab: {len(price_rows)} rows")
    print(f"  Headers: {PRICE_HEADERS}")
    for r in price_rows[:3]:
        print(f"  {r}")

    # Binary Events
    event_rows = _read_binary_events()
    print(f"\nBinary Events tab: {len(event_rows)} rows")
    print(f"  Headers: {BINARY_HEADERS}")
    for r in event_rows:
        print(f"  {r}")

    # Meta
    meta_rows = _build_meta()
    print(f"\nMeta tab: {len(meta_rows)} rows")
    for r in meta_rows:
        print(f"  {r[0]}: {r[1]}")

    print(f"\nTotal rows to write: "
          f"{len(sig_rows) + len(price_rows) + len(event_rows) + len(meta_rows)}")


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("SHEETS INTERFACE — MODULE TEST")
    print("=" * 55)

    # Test 1: Credentials load
    print("\n1. Testing credentials load...")
    creds_path = os.getenv(CREDENTIALS_VAR, "")
    sheet_id = os.getenv(SHEET_ID_VAR, "")
    if creds_path and os.path.exists(creds_path):
        print(f"   OK — credentials file found: {creds_path}")
    else:
        print(f"   SKIP — {CREDENTIALS_VAR} not set or file not found")
        print(f"   Value: '{creds_path}'")
    if sheet_id:
        print(f"   OK — sheet ID set: {sheet_id[:20]}...")
    else:
        print(f"   SKIP — {SHEET_ID_VAR} not set")

    # Test 2: DB read
    print("\n2. Testing DB reads...")
    sig_rows = _read_signals()
    price_rows = _read_prices()
    event_rows = _read_binary_events()
    meta_rows = _build_meta()
    print(f"   Signals: {len(sig_rows)} rows")
    print(f"   Prices: {len(price_rows)} rows")
    print(f"   Binary Events: {len(event_rows)} rows")
    print(f"   Meta: {len(meta_rows)} rows")
    assert len(price_rows) > 0, "No price data in DB"
    print("   OK — all tables readable")

    # Test 3: Dry run
    print("\n3. Testing dry run...")
    dry_run()

    # Test 4: Live sync (only if credentials available)
    print("\n4. Testing live sync...")
    if creds_path and os.path.exists(creds_path) and sheet_id:
        result = sync_all()
        print(f"   Success: {result.success}")
        print(f"   Signals: {result.signals_written}")
        print(f"   Prices: {result.prices_written}")
        print(f"   Events: {result.binary_events_written}")
        print(f"   Meta: {result.meta_written}")
        if result.errors:
            print(f"   Errors: {result.errors}")
    else:
        print("   SKIP — credentials or sheet ID not configured")
        print("   Set GROUNDTRUTH_SHEETS_CREDENTIALS and GROUNDTRUTH_SHEET_ID in .env")

    # Test 5: Verify column structure
    print("\n5. Verifying tab column structure...")
    assert len(SIGNAL_HEADERS) == 17, f"Expected 17 signal columns, got {len(SIGNAL_HEADERS)}"
    assert SIGNAL_HEADERS[0] == "ID"
    assert SIGNAL_HEADERS[5] == "Headline"
    assert SIGNAL_HEADERS[14] == "Second Order"
    assert len(PRICE_HEADERS) == 13
    assert len(BINARY_HEADERS) == 8
    assert len(META_HEADERS) == 2
    print(f"   Signal columns: {len(SIGNAL_HEADERS)} — OK")
    print(f"   Price columns: {len(PRICE_HEADERS)} — OK")
    print(f"   Binary columns: {len(BINARY_HEADERS)} — OK")
    print(f"   Meta columns: {len(META_HEADERS)} — OK")

    # Verify signal row width matches headers
    if sig_rows:
        assert len(sig_rows[0]) == len(SIGNAL_HEADERS), \
            f"Signal row width {len(sig_rows[0])} != headers {len(SIGNAL_HEADERS)}"
        print("   Signal row width matches headers — OK")

    print("\nsheets/interface.py operational.")