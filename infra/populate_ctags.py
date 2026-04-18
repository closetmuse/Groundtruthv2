"""
GroundTruth V2 — infra/populate_ctags.py
Auto-populate C-Tags for Pipeline deals based on Asset Type, A-Tags, and Notes.
Safe to re-run — never overwrites existing C-Tag values.
"""

import sys
import os

sys.path.insert(0, r"C:\Users\nagar_7kszmu8\GroundTruth_v2")
from dotenv import load_dotenv
load_dotenv(r"C:\Users\nagar_7kszmu8\GroundTruth_v2\.env", override=True)

from sheets.interface import _get_sheets_service, _get_sheet_id

# ── CLASSIFICATION RULES ─────────────────────────────────────────────────────
# Check notes, asset_type, and a_tags fields for keywords

KEYWORD_MAP = {
    "C06": ["solar", "pv", "photovoltaic", "bifacial", "module", "renewables"],
    "C07": ["wind", "turbine", "offshore wind", "onshore wind"],
    "C10": ["battery", "bess", "storage", "lithium"],
    "C05": ["gas", "natural gas", "combined cycle", "ccgt", "peaker",
            "lng", "liquefaction", "regasification", "export terminal",
            "pipeline", "midstream", "power -"],
    "C11": ["data center", "data centre", "hyperscale", "colocation",
            "gpu", "compute", "fiber", "telecom", "broadband", "dc -", "dc "],
    "C02": ["ferc", "interconnection queue", "large load", "nuclear",
            "smr", "advanced nuclear", "nrc"],
    "C04": ["itc", "ptc", "ira", "tax credit", "obbba", "nuclear",
            "smr", "legislative"],
    "C15": ["transmission", "grid", "substation", "interconnection"],
    "C03": ["toll road", "highway", "p3", "ppp", "airport", "port",
            "rail", "water", "wastewater", "desalination", "transport",
            "transition"],
    "C09": ["tariff", "steel", "aluminum", "copper", "commodity cost",
            "construction", "epc", "contractor"],
    "C12": ["refinancing", "refi", "mini-perm", "maturity"],
    "C14": ["acquisition", "m&a", "equity stake", "sponsor"],
    "C13": ["international", "cross-border", "fx", "currency"],
    "C08": ["hormuz", "geopolitic", "conflict", "war", "sanction"],
}

# A-tag to C-tag mapping (when notes are sparse, use asset class)
ATAG_MAP = {
    "A04": ["C06"],               # Solar
    "A05": ["C06", "C10"],        # BESS
    "A06": ["C07"],               # Onshore Wind
    "A07": ["C07"],               # Offshore Wind
    "A01": ["C05"],               # Gas Power
    "A09": ["C11"],               # Data Center
    "A10": ["C11"],               # GPU
    "A12": ["C05"],               # LNG
    "A14": ["C05"],               # Gas Pipeline
    "A17": ["C15"],               # Transmission
    "A19": ["C03"],               # Toll Road
    "A27": ["C09"],               # Critical Minerals
    "A02": ["C02", "C04"],        # Nuclear
}

# Asset type string to C-tag mapping
ASSET_TYPE_MAP = {
    "solar":           ["C06"],
    "bess":            ["C10"],
    "storage":         ["C10"],
    "wind":            ["C07"],
    "gas power":       ["C05"],
    "gas":             ["C05"],
    "lng":             ["C05"],
    "data center":     ["C11"],
    "digital":         ["C11"],
    "nuclear":         ["C02", "C04"],
    "transmission":    ["C15"],
    "toll road":       ["C03"],
    "transport":       ["C03"],
    "critical mineral": ["C09"],
    "mining":          ["C09"],
}

# All solar/renewables deals also get C09 (construction commodities exposed)
# All construction-phase deals get C09


def classify_deal(name, asset_type, a_tags_str, notes):
    """Classify a deal into C-Tags from available fields."""
    text = f"{name} {asset_type} {a_tags_str} {notes}".lower()
    tags = set()
    reasons = []

    # 1. Keyword matching from notes + asset type
    for tag, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text:
                tags.add(tag)
                reasons.append(f"{tag}:{kw}")
                break

    # 2. A-tag mapping (strong signal even with sparse notes)
    for a_code in a_tags_str.replace(",", " ").split():
        a_code = a_code.strip()
        if a_code in ATAG_MAP:
            for ct in ATAG_MAP[a_code]:
                if ct not in tags:
                    tags.add(ct)
                    reasons.append(f"{ct}:from_{a_code}")

    # 3. Asset type string mapping
    at_lower = asset_type.lower()
    for key, ctags in ASSET_TYPE_MAP.items():
        if key in at_lower:
            for ct in ctags:
                if ct not in tags:
                    tags.add(ct)
                    reasons.append(f"{ct}:asset_{key}")

    # 4. ALL pipeline deals are construction-phase — C09 always applies
    # SC Project Finance pipeline = construction debt. No exceptions.
    if "C09" not in tags:
        tags.add("C09")
        reasons.append("C09:all_deals_construction_phase")

    # 5. ALL deals get C12 (financing markets — they're all project finance)
    if "C12" not in tags:
        tags.add("C12")
        reasons.append("C12:project_finance")

    if not tags:
        return "NEEDS REVIEW", ["no keywords matched"]

    return ", ".join(sorted(tags)), reasons


def main():
    service = _get_sheets_service()
    sheet_id = _get_sheet_id()

    # Read Pipeline tab
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range="'Pipeline'!A:W",
    ).execute()
    rows = result.get("values", [])
    headers = rows[0]
    data = rows[1:]

    # Column indices
    idx = {}
    for i, h in enumerate(headers):
        idx[h] = i

    name_i = idx.get("Deal Name", 1)
    ctag_i = idx.get("C-Tags", 9)
    atag_i = idx.get("A-Tags", 10)
    asset_i = idx.get("Asset Type", 2)
    notes_i = idx.get("Notes", 21)

    print(f"{len(data)} deals found")

    skipped = 0
    written = 0
    needs_review = 0
    updates = []  # (row_number, ctag_value)

    for row_idx, r in enumerate(data):
        padded = r + [""] * (len(headers) - len(r))
        name = padded[name_i].strip()
        existing = padded[ctag_i].strip()
        a_tags = padded[atag_i].strip()
        asset = padded[asset_i].strip()
        notes = padded[notes_i].strip()

        if existing:
            skipped += 1
            continue

        ctags, reasons = classify_deal(name, asset, a_tags, notes)
        sheet_row = row_idx + 2  # 1-indexed + header

        if ctags == "NEEDS REVIEW":
            needs_review += 1
            print(f"  NEEDS REVIEW: {name[:35]:35} — {'; '.join(reasons)}")
        else:
            written += 1
            reason_str = ", ".join(reasons[:5])
            print(f"  {name[:35]:35} -> {ctags:30} | {reason_str}")

        updates.append((sheet_row, ctags))

    # Write updates to Sheet
    if updates:
        # Use batch update for efficiency
        col_letter = chr(65 + ctag_i)  # 'J' for index 9
        batch_data = []
        for sheet_row, ctags in updates:
            batch_data.append({
                "range": f"'Pipeline'!{col_letter}{sheet_row}",
                "values": [[ctags]],
            })

        service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id,
            body={
                "valueInputOption": "RAW",
                "data": batch_data,
            },
        ).execute()

    print(f"\n{written} C-Tags written")
    print(f"{needs_review} NEEDS REVIEW")
    print(f"{skipped} skipped (already had tags)")

    # Verification pass
    print("\nVerification pass...")
    result2 = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range="'Pipeline'!A:W",
    ).execute()
    rows2 = result2.get("values", [])
    data2 = rows2[1:]

    empty_after = 0
    populated_after = 0
    for r in data2:
        padded = r + [""] * (len(headers) - len(r))
        ctag = padded[ctag_i].strip()
        if ctag:
            populated_after += 1
        else:
            empty_after += 1

    print(f"  Populated: {populated_after}/{len(data2)}")
    print(f"  Empty: {empty_after}/{len(data2)}")
    if empty_after == 0:
        print("  All C-Tag cells now have a value.")


if __name__ == "__main__":
    main()