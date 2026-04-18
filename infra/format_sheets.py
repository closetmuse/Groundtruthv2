"""
GroundTruth V2 — infra/format_sheets.py
Professional formatting for ALL Google Sheets tabs.
White rows, black text, Calibri 12. Dark charcoal headers.
Color ONLY on designated status/alert cells — nothing else.
"""

import sys
import os

sys.path.insert(0, r"C:\Users\nagar_7kszmu8\GroundTruth_v2")
from dotenv import load_dotenv
load_dotenv(r"C:\Users\nagar_7kszmu8\GroundTruth_v2\.env", override=True)

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

CREDS_PATH = os.getenv("GROUNDTRUTH_SHEETS_CREDENTIALS")
SHEET_ID = os.getenv("GROUNDTRUTH_SHEET_ID")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ── COLORS ────────────────────────────────────────────────────────────────────

HEADER_BG  = {"red": 0.176, "green": 0.176, "blue": 0.176}  # #2D2D2D
WHITE      = {"red": 1.0, "green": 1.0, "blue": 1.0}
BLACK      = {"red": 0.1, "green": 0.1, "blue": 0.1}        # #1A1A1A
BORDER_CLR = {"red": 0.8, "green": 0.8, "blue": 0.8}        # #CCCCCC

# Alert/Heat cell colors
RED_BG     = {"red": 0.957, "green": 0.800, "blue": 0.800}   # #F4CCCC
RED_FG     = {"red": 0.800, "green": 0.000, "blue": 0.000}   # #CC0000
AMBER_BG   = {"red": 0.988, "green": 0.898, "blue": 0.804}   # #FCE5CD
AMBER_FG   = {"red": 0.902, "green": 0.361, "blue": 0.000}   # #E65C00
GREEN_BG   = {"red": 0.851, "green": 0.918, "blue": 0.827}   # #D9EAD3
GREEN_FG   = {"red": 0.176, "green": 0.416, "blue": 0.176}   # #2D6A2D

COLOR_MAP = {
    "RED":      (RED_BG, RED_FG),
    "AMBER":    (AMBER_BG, AMBER_FG),
    "GREEN":    (GREEN_BG, GREEN_FG),
    "HOT":      (RED_BG, RED_FG),
    "WARM":     (AMBER_BG, AMBER_FG),
    "COOL":     (GREEN_BG, GREEN_FG),
    "OPEN":     (AMBER_BG, AMBER_FG),
    "RESOLVED": (GREEN_BG, GREEN_FG),
    "Y":        (GREEN_BG, GREEN_FG),
    "N":        (RED_BG, RED_FG),
}

# Tab-specific color rules: tab_name -> (column_header, {value: color_key})
TAB_COLORS = {
    "Signals":       ("Alert",      {"RED": "RED", "AMBER": "AMBER", "GREEN": "GREEN"}),
    "Binary Events": ("Status",     {"OPEN": "OPEN", "RESOLVED": "RESOLVED"}),
    "Scoreboard":    ("Hit (Y/N)",  {"Y": "Y", "N": "N"}),
    "Deal Watch":    ("Heat Level", {"HOT": "HOT", "WARM": "WARM", "COOL": "COOL"}),
}

ALL_TABS = [
    "Signals", "Prices", "Binary Events", "Pipeline",
    "Scoreboard", "Stats", "Meta", "Deal Watch", "Health",
]


def main():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)

    meta = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    tab_map = {}
    for s in meta["sheets"]:
        p = s["properties"]
        g = p.get("gridProperties", {})
        tab_map[p["title"]] = {
            "id": p["sheetId"],
            "rows": g.get("rowCount", 200),
            "cols": g.get("columnCount", 26),
        }

    for tab_name in ALL_TABS:
        if tab_name not in tab_map:
            print(f"[{tab_name}] — NOT FOUND, skipping")
            continue

        info = tab_map[tab_name]
        tid = info["id"]
        n_rows = min(info["rows"], 300)
        n_cols = info["cols"]

        # Read headers
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{tab_name}'!1:1",
        ).execute()
        headers = result.get("values", [[]])[0]
        data_cols = min(n_cols, len(headers)) if headers else n_cols

        reqs = []

        # 1. White bg + black Calibri 12 on ALL cells
        reqs.append({
            "repeatCell": {
                "range": {"sheetId": tid},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": WHITE,
                    "textFormat": {
                        "foregroundColor": BLACK,
                        "fontFamily": "Calibri",
                        "fontSize": 12,
                        "bold": False,
                    },
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "CLIP",
                }},
                "fields": ("userEnteredFormat(backgroundColor,textFormat,"
                           "verticalAlignment,wrapStrategy)"),
            }
        })

        # 2. Header row: dark charcoal bg, white bold Calibri 12
        reqs.append({
            "repeatCell": {
                "range": {"sheetId": tid, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": HEADER_BG,
                    "textFormat": {
                        "foregroundColor": WHITE,
                        "fontFamily": "Calibri",
                        "fontSize": 12,
                        "bold": True,
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                }},
                "fields": ("userEnteredFormat(backgroundColor,textFormat,"
                           "horizontalAlignment,verticalAlignment)"),
            }
        })

        # 3. Freeze header row
        reqs.append({
            "updateSheetProperties": {
                "properties": {"sheetId": tid,
                               "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        })

        # 4. Header height 28px, data rows 22px
        reqs.append({
            "updateDimensionProperties": {
                "range": {"sheetId": tid, "dimension": "ROWS",
                          "startIndex": 0, "endIndex": 1},
                "properties": {"pixelSize": 28},
                "fields": "pixelSize",
            }
        })
        if n_rows > 1:
            reqs.append({
                "updateDimensionProperties": {
                    "range": {"sheetId": tid, "dimension": "ROWS",
                              "startIndex": 1, "endIndex": n_rows},
                    "properties": {"pixelSize": 22},
                    "fields": "pixelSize",
                }
            })

        # 5. Auto-resize columns
        reqs.append({
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": tid, "dimension": "COLUMNS",
                    "startIndex": 0, "endIndex": data_cols,
                }
            }
        })

        # 6. Thin grey borders on data area
        border = {"style": "SOLID", "width": 1, "color": BORDER_CLR}
        reqs.append({
            "updateBorders": {
                "range": {"sheetId": tid, "startRowIndex": 0,
                          "endRowIndex": n_rows,
                          "startColumnIndex": 0, "endColumnIndex": data_cols},
                "top": border, "bottom": border,
                "left": border, "right": border,
                "innerHorizontal": border, "innerVertical": border,
            }
        })

        # 7. Text wrap on wide columns
        wrap_names = {"headline", "summary", "narrative", "second order",
                      "second_order", "notes", "rationale", "deals",
                      "predicted impact", "actual outcome", "heat rationale",
                      "risk_alert_rationale", "opportunity_rationale"}
        for ci, h in enumerate(headers):
            if h.lower().replace(" ", "_").replace("-", "_") in wrap_names \
                    or h.lower() in wrap_names:
                reqs.append({
                    "repeatCell": {
                        "range": {"sheetId": tid, "startRowIndex": 1,
                                  "startColumnIndex": ci, "endColumnIndex": ci + 1},
                        "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
                        "fields": "userEnteredFormat.wrapStrategy",
                    }
                })
                # Cap at 400px
                reqs.append({
                    "updateDimensionProperties": {
                        "range": {"sheetId": tid, "dimension": "COLUMNS",
                                  "startIndex": ci, "endIndex": ci + 1},
                        "properties": {"pixelSize": 400},
                        "fields": "pixelSize",
                    }
                })

        # 8. Tab-specific color coding — ONLY on the designated column
        color_rule = TAB_COLORS.get(tab_name)
        if color_rule:
            col_name, value_map = color_rule
            col_idx = None
            for i, h in enumerate(headers):
                if h == col_name:
                    col_idx = i
                    break

            if col_idx is not None:
                col_letter = chr(65 + col_idx) if col_idx < 26 else "A"
                val_result = service.spreadsheets().values().get(
                    spreadsheetId=SHEET_ID,
                    range=f"'{tab_name}'!{col_letter}:{col_letter}",
                ).execute()
                col_vals = val_result.get("values", [])

                for row_i, cell in enumerate(col_vals):
                    if row_i == 0:
                        continue
                    val = (cell[0] if cell else "").strip().upper()
                    color_key = value_map.get(val)
                    if color_key and color_key in COLOR_MAP:
                        bg, fg = COLOR_MAP[color_key]
                        reqs.append({
                            "repeatCell": {
                                "range": {"sheetId": tid,
                                          "startRowIndex": row_i,
                                          "endRowIndex": row_i + 1,
                                          "startColumnIndex": col_idx,
                                          "endColumnIndex": col_idx + 1},
                                "cell": {"userEnteredFormat": {
                                    "backgroundColor": bg,
                                    "textFormat": {
                                        "foregroundColor": fg,
                                        "bold": True,
                                        "fontFamily": "Calibri",
                                        "fontSize": 12,
                                    },
                                    "horizontalAlignment": "CENTER",
                                }},
                                "fields": ("userEnteredFormat(backgroundColor,"
                                           "textFormat,horizontalAlignment)"),
                            }
                        })

        # Execute in batches
        print(f"[{tab_name}] — {len(reqs)} formatting requests...")
        for i in range(0, len(reqs), 80):
            chunk = reqs[i:i+80]
            service.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID, body={"requests": chunk},
            ).execute()
        print(f"[{tab_name}] — done")

    print(f"\nAll tabs formatted.")
    print(f"  Font: Calibri 12 everywhere")
    print(f"  Rows: white bg, black text")
    print(f"  Headers: #2D2D2D bg, white bold")
    print(f"  Color: alert/status column only")
    print(f"  Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")


if __name__ == "__main__":
    main()