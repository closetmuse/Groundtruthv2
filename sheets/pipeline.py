"""
GroundTruth V2 — sheets/pipeline.py
Two-way sync for pipeline deal parameters.
Sri enters/edits deal parameters directly in a Google Sheet "Pipeline" tab.
gt/orchestrator.py reads from the Sheet at run time — no code edits required.
Replaces hardcoded deal dicts in ge/scorer.py.

Uses same service account auth as sheets/interface.py.

Last Updated: April 2026
"""

import os
import sys
import json
from datetime import date
from typing import Optional

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

from sheets.interface import _get_sheets_service, _get_sheet_id, _ensure_tab

# ── CONSTANTS ─────────────────────────────────────────────────────────────────

TAB_NAME = "Pipeline"

HEADERS = [
    "Deal ID", "Deal Name", "Asset Type", "Sub-Type", "Status",
    "Sponsor", "SC Role", "Debt Amount (USDm)", "Equity Amount (USDm)",
    "C-Tags", "A-Tags", "Key Commodities", "Offtaker",
    "Binary Events", "FERC Required", "RTO", "State",
    "Construction Start", "COD Target", "Mini-Perm Maturity",
    "Alert Override", "Notes", "Last Updated",
]

HEADER_BG = {"red": 0.1, "green": 0.1, "blue": 0.18}  # #1a1a2e

COL_WIDTHS = {
    0: 90,    # Deal ID
    1: 200,   # Deal Name
    2: 120,   # Asset Type
    3: 100,   # Sub-Type
    4: 80,    # Status
    5: 120,   # Sponsor
    6: 100,   # SC Role
    7: 100,   # Debt Amount
    8: 100,   # Equity Amount
    9: 120,   # C-Tags
    10: 100,  # A-Tags
    11: 150,  # Key Commodities
    12: 120,  # Offtaker
    13: 250,  # Binary Events
    14: 80,   # FERC Required
    15: 60,   # RTO
    16: 80,   # State
    17: 110,  # Construction Start
    18: 100,  # COD Target
    19: 120,  # Mini-Perm Maturity
    20: 100,  # Alert Override
    21: 350,  # Notes
    22: 100,  # Last Updated
}

# ── SEED DATA ─────────────────────────────────────────────────────────────────

SEED_DEALS = [
    [
        "VEGA-001", "Project Vega", "Solar + Storage", "Utility-scale",
        "ACTIVE", "", "Lead Arranger", "", "",
        "C06, C10, C04, C09", "A04, A05", "Aluminum, copper, steel, modules",
        "", "OBBBA July 4, FERC April 30", "Yes", "PJM", "",
        "", "", "", "", "", str(date.today()),
    ],
    [
        "GT-108", "GT-108 SB Energy Ohio", "Gas + Digital Infra", "Data center + power",
        "ACTIVE", "SB Energy", "Lender", "", "",
        "C05, C11, C02", "A01, A09", "Natural gas, steel, copper",
        "", "FERC April 30, PJM April 27", "Yes", "PJM", "Ohio",
        "", "", "", "", "", str(date.today()),
    ],
    [
        "GT-109", "GT-109 SB Energy Milam", "Digital Infra + Power", "Data center + power",
        "ACTIVE", "SB Energy", "Lender", "", "",
        "C11, C05, C03", "A09, A01", "ERCOT power prices, gas",
        "", "FOMC April 28", "No", "ERCOT", "Texas",
        "", "", "", "", "", str(date.today()),
    ],
    [
        "FALCON-001", "Project Falcon", "TBC", "TBC",
        "WATCH", "", "TBC", "", "",
        "", "", "", "", "", "", "", "",
        "", "", "", "", "", str(date.today()),
    ],
    [
        "ATLAS-001", "Project Atlas", "TBC", "TBC",
        "WATCH", "", "TBC", "", "",
        "", "", "", "", "", "", "", "",
        "", "", "", "", "", str(date.today()),
    ],
    [
        "MERID-001", "Project Meridian", "TBC", "TBC",
        "WATCH", "", "TBC", "", "",
        "", "", "", "", "", "", "", "",
        "", "", "", "", "", str(date.today()),
    ],
]


# ── VALIDATION ────────────────────────────────────────────────────────────────

def validate_deal_row(row: list) -> list[str]:
    """
    Validate a single deal row from the Pipeline tab.

    Checks required fields (Deal ID, Deal Name, Asset Type) and
    returns a list of warning strings. Empty list means valid.

    Args:
        row: List of cell values matching HEADERS column order.

    Returns:
        List of warning strings. Empty if row is valid.
    """
    warnings = []
    if len(row) < 3:
        warnings.append("Row too short — fewer than 3 columns")
        return warnings

    deal_id = str(row[0]).strip()
    deal_name = str(row[1]).strip()
    asset_type = str(row[2]).strip()

    if not deal_id:
        warnings.append("Missing Deal ID")
    if not deal_name:
        warnings.append("Missing Deal Name")
    if not asset_type:
        warnings.append("Missing Asset Type")

    # Status validation
    if len(row) > 4:
        status = str(row[4]).strip().upper()
        valid_statuses = {"ACTIVE", "WATCH", "CLOSED", "DEFERRED", ""}
        if status and status not in valid_statuses:
            warnings.append(f"Invalid Status '{status}' — expected ACTIVE|WATCH|CLOSED|DEFERRED")

    return warnings


# ── READ FROM SHEET ───────────────────────────────────────────────────────────

def read_pipeline_from_sheet() -> list[dict]:
    """
    Read the Pipeline tab from Google Sheets and return as list of deal dicts.

    Called by gt/orchestrator.py at start of each run to get current deal
    parameters without code edits. Validates required fields and logs
    warnings for incomplete rows.

    Returns:
        List of deal dicts keyed by header names. Returns empty list if
        tab is empty, credentials are missing, or read fails.
    """
    service = _get_sheets_service()
    sheet_id = _get_sheet_id()

    if not service or not sheet_id:
        print("  Pipeline read: Sheets unavailable — using fallback")
        return []

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{TAB_NAME}'!A:W",
        ).execute()
        rows = result.get("values", [])

        if len(rows) < 2:
            print("  Pipeline tab empty — no deals loaded")
            return []

        headers = rows[0]
        deals = []
        for i, row in enumerate(rows[1:], start=2):
            # Pad row to header length
            padded = row + [""] * (len(headers) - len(row))
            deal = {headers[j]: padded[j] for j in range(len(headers))}

            # Validate
            warnings = validate_deal_row(row)
            if warnings:
                deal_name = deal.get("Deal Name", f"row {i}")
                for w in warnings:
                    print(f"    WARN: {deal_name}: {w}")

            # Skip completely empty rows
            if not any(str(v).strip() for v in row[:3]):
                continue

            deals.append(deal)

        print(f"  Pipeline loaded: {len(deals)} deals from Sheet")
        for d in deals:
            status = d.get("Status", "")
            print(f"    {d.get('Deal ID','?'):12} {d.get('Deal Name','?'):30} [{status}]")

        return deals

    except Exception as e:
        print(f"  Pipeline read failed: {e}")
        return []


# ── SEED TO SHEET ─────────────────────────────────────────────────────────────

def seed_pipeline_sheet():
    """
    Write the 6 current deals as starting rows to the Pipeline tab.

    Only runs if the Pipeline tab is empty or does not exist. Never
    overwrites Sri's edits. Creates the tab if missing.

    Applies formatting: bold frozen header, dark background, column widths,
    and Status column dropdown validation.
    """
    service = _get_sheets_service()
    sheet_id = _get_sheet_id()

    if not service or not sheet_id:
        print("  Pipeline seed: Sheets unavailable")
        return

    # Check if tab already has data
    tab_id = _ensure_tab(service, sheet_id, TAB_NAME)

    try:
        existing = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{TAB_NAME}'!A:A",
        ).execute()
        existing_rows = existing.get("values", [])

        if len(existing_rows) > 1:
            print(f"  Pipeline tab already has {len(existing_rows)-1} deals — "
                  f"skipping seed (never overwrites)")
            return
    except Exception:
        pass  # Tab may be newly created and empty

    # Write headers + seed data
    all_rows = [HEADERS] + SEED_DEALS
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'{TAB_NAME}'!A1",
        valueInputOption="RAW",
        body={"values": all_rows},
    ).execute()

    print(f"  Pipeline seeded: {len(SEED_DEALS)} deals written")

    # Format: bold header, freeze, column widths, dark bg
    requests = []

    # Bold header with dark background and white text
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": tab_id,
                "startRowIndex": 0, "endRowIndex": 1,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    "backgroundColor": HEADER_BG,
                }
            },
            "fields": "userEnteredFormat(textFormat,backgroundColor)",
        }
    })

    # Freeze header row
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": tab_id,
                "gridProperties": {"frozenRowCount": 1},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    })

    # Column widths
    for col_idx, width in COL_WIDTHS.items():
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

    # Status column dropdown validation (column index 4)
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": tab_id,
                "startRowIndex": 1,
                "endRowIndex": 100,
                "startColumnIndex": 4,
                "endColumnIndex": 5,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "ACTIVE"},
                        {"userEnteredValue": "WATCH"},
                        {"userEnteredValue": "CLOSED"},
                        {"userEnteredValue": "DEFERRED"},
                    ],
                },
                "showCustomUi": True,
                "strict": False,
            },
        }
    })

    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": requests},
    ).execute()

    print("  Pipeline formatted: header, widths, status dropdown applied")


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("SHEETS PIPELINE — MODULE TEST")
    print("=" * 55)

    # Test 1: Credentials check
    print("\n1. Testing credentials...")
    creds_path = os.getenv("GROUNDTRUTH_SHEETS_CREDENTIALS", "")
    sheet_id = os.getenv("GROUNDTRUTH_SHEET_ID", "")
    if creds_path and os.path.exists(creds_path):
        print(f"   OK — credentials: {creds_path}")
    else:
        print(f"   SKIP — GROUNDTRUTH_SHEETS_CREDENTIALS not set")
    if sheet_id:
        print(f"   OK — sheet ID: {sheet_id[:20]}...")
    else:
        print(f"   SKIP — GROUNDTRUTH_SHEET_ID not set")

    # Test 2: validate_deal_row
    print("\n2. Testing validate_deal_row...")
    # Complete row
    w = validate_deal_row(SEED_DEALS[0])
    assert len(w) == 0, f"Expected no warnings for complete row, got: {w}"
    print("   Complete row: 0 warnings — OK")
    # Incomplete row
    w = validate_deal_row(["", "Test Deal", ""])
    assert any("Missing" in x for x in w), f"Expected Missing warnings, got: {w}"
    print(f"   Incomplete row: {len(w)} warnings — OK ({w})")
    # TBC row
    w = validate_deal_row(SEED_DEALS[3])  # Project Falcon TBC
    assert len(w) == 0, f"Expected no warnings for TBC row, got: {w}"
    print("   TBC row: 0 warnings — OK")

    # Test 3: Dry run
    print("\n3. Dry run — seed data preview:")
    print(f"   Headers ({len(HEADERS)}): {HEADERS[:5]}...")
    print(f"   Deals to seed: {len(SEED_DEALS)}")
    for deal in SEED_DEALS:
        print(f"     {deal[0]:12} {deal[1]:30} [{deal[4]}]")

    # Test 4: Seed pipeline (live)
    print("\n4. Testing seed_pipeline_sheet...")
    if creds_path and os.path.exists(creds_path) and sheet_id:
        seed_pipeline_sheet()
    else:
        print("   SKIP — credentials not configured")

    # Test 5: Read pipeline (live)
    print("\n5. Testing read_pipeline_from_sheet...")
    if creds_path and os.path.exists(creds_path) and sheet_id:
        deals = read_pipeline_from_sheet()
        if deals:
            print(f"   Read {len(deals)} deals:")
            for d in deals:
                print(f"     {d.get('Deal ID','?'):12} "
                      f"{d.get('Deal Name','?'):30} "
                      f"A-Tags={d.get('A-Tags','')} "
                      f"C-Tags={d.get('C-Tags','')}")
        else:
            print("   No deals returned (tab may be empty)")
    else:
        print("   SKIP — credentials not configured")

    print("\nsheets/pipeline.py operational.")