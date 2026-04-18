# GS — MT Newswires Integration (via Google Sheets staging)
# Architecture: Claude.ai scheduled task fetches MT Newswires MCP at 05:27 ET
# and writes to "MT Newswires" tab in Google Sheets.
# This module reads from that tab and feeds into the classification pipeline.
# Last Updated: April 13 2026

import sys
import os
import json
from datetime import datetime
from typing import Optional

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

SHEET_ID = os.getenv("GROUNDTRUTH_SHEET_ID", "")
TAB_NAME = "MT Newswires"

# C-tag mapping by filter keyword presence in the row
FILTER_TAG_MAP = {
    "LNG":              {"c_tags": ["C08", "C05"], "a_tags": ["A12", "A13"]},
    "Hormuz":           {"c_tags": ["C08", "C05"], "a_tags": ["A12", "A15"]},
    "FERC":             {"c_tags": ["C02", "C15"], "a_tags": ["A17"]},
    "CAISO":            {"c_tags": ["C06", "C15"], "a_tags": ["A04", "A05"]},
    "ERCOT":            {"c_tags": ["C06", "C15"], "a_tags": ["A04", "A05"]},
    "BDC":              {"c_tags": ["C12", "C01"], "a_tags": ["ALL"]},
    "FOMC":             {"c_tags": ["C01", "C02"], "a_tags": ["ALL"]},
    "steel":            {"c_tags": ["C09", "C08"], "a_tags": ["ALL"]},
    "data center":      {"c_tags": ["C11", "C15"], "a_tags": ["A09", "A17"]},
    "nuclear":          {"c_tags": ["C02", "C04"], "a_tags": ["A02", "A25"]},
    "Iran":             {"c_tags": ["C08", "C05"], "a_tags": ["A12", "A15"]},
    "interconnection":  {"c_tags": ["C02", "C15"], "a_tags": ["A17"]},
    "curtailment":      {"c_tags": ["C06", "C15"], "a_tags": ["A04", "A05"]},
    "private credit":   {"c_tags": ["C12", "C01"], "a_tags": ["ALL"]},
    "project finance":  {"c_tags": ["C12", "C05"], "a_tags": ["ALL"]},
}


def fetch_mt_newswires(on_date: str = None) -> list:
    """
    Read MT Newswires articles from Google Sheets staging tab.

    The "MT Newswires" tab is populated by a Claude.ai scheduled task
    at 05:27 ET daily. This function reads that tab and converts rows
    to standard raw article dicts for the classification pipeline.

    Args:
        on_date: Date filter YYYY-MM-DD. If provided, only returns
                 articles from that date. Defaults to all rows in tab.

    Returns:
        List of raw article dicts matching fetch_rss() output format.
        Returns empty list if tab is empty or unavailable.
    """
    try:
        from sheets.interface import _get_sheets_service, _get_sheet_id

        service = _get_sheets_service()
        sheet_id = _get_sheet_id()

        if not service or not sheet_id:
            return []

        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{TAB_NAME}'!A:H",
        ).execute()
        rows = result.get("values", [])

        if len(rows) < 2:
            return []

        headers = rows[0]
        items = []
        seen_subkeys = set()

        for row in rows[1:]:
            padded = row + [""] * (len(headers) - len(row))
            row_dict = {headers[i]: padded[i] for i in range(len(headers))}

            headline = row_dict.get("Headline", "").strip()
            if not headline:
                continue

            subkey = row_dict.get("Subkey", "")
            if subkey and subkey in seen_subkeys:
                continue
            if subkey:
                seen_subkeys.add(subkey)

            fetch_date = row_dict.get("Fetch Date", "")
            if on_date and fetch_date and not fetch_date.startswith(on_date):
                continue

            body = row_dict.get("Body (first 500 chars)", "")
            release_time = row_dict.get("Release Time", fetch_date)
            filter_kws = row_dict.get("Filter Keywords", "")
            c_tags_str = row_dict.get("C-Tags", "")
            a_tags_str = row_dict.get("A-Tags", "")

            # Parse tags from sheet or derive from filter keywords
            c_tags = []
            a_tags = []
            try:
                c_tags = json.loads(c_tags_str) if c_tags_str.startswith("[") else c_tags_str.split(",")
                c_tags = [t.strip() for t in c_tags if t.strip()]
            except Exception:
                pass
            try:
                a_tags = json.loads(a_tags_str) if a_tags_str.startswith("[") else a_tags_str.split(",")
                a_tags = [t.strip() for t in a_tags if t.strip()]
            except Exception:
                pass

            # Fallback: derive tags from filter keywords if not provided
            if not c_tags:
                for kw, tags in FILTER_TAG_MAP.items():
                    if kw.lower() in filter_kws.lower() or kw.lower() in headline.lower():
                        c_tags = tags["c_tags"]
                        a_tags = tags["a_tags"]
                        break

            items.append({
                "headline":         headline[:120],
                "summary":          body[:500],
                "url":              f"https://www.mtnewswires.com/article/{subkey}" if subkey else "",
                "source_name":      "MT Newswires",
                "publication_date": release_time,
                "c_tags":           c_tags if c_tags else ["C01"],
                "a_tags":           a_tags if a_tags else ["ALL"],
                "raw_content":      body[:3000],
            })

        return items

    except Exception as e:
        print(f"    MT Newswires Sheets read failed: {e}")
        return []


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("MT NEWSWIRES — SHEETS STAGING TEST")
    print("=" * 55)

    items = fetch_mt_newswires()
    print(f"Articles from Sheets: {len(items)}")

    if items:
        print("\nFirst 5:")
        for item in items[:5]:
            print(f"  [{item['source_name']}] {item['headline'][:65]}")
            print(f"    c_tags={item['c_tags']} pub={item['publication_date']}")
    else:
        print("\n  No articles in MT Newswires tab.")
        print("  Scheduled task runs daily at 05:27 ET.")
        print("  Click 'Run now' on mt-newswires-fetch task to populate.")

    print("\ngs/mt_newswires.py operational.")