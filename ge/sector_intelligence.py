"""
GroundTruth V2 — ge/sector_intelligence.py
Sector Intelligence Layer (SIL). Sits between signal classification and
deal matching. Filters signals by sector materiality before they affect
a deal's heat score, narrative, or signal count.

Last Updated: April 2026
"""

import sys
import os
import json
import sqlite3
from datetime import datetime
from typing import Optional

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "groundtruth.db")

# ── SECTOR DEFINITIONS ────────────────────────────────────────────────────────

SECTOR_INTELLIGENCE = {
    "SR-01": {
        "sector_code": "SR-01",
        "name": "Data Centers / Digital Infrastructure",
        "a_tags": ["A09", "A10", "A11"],
        "key_c_tags": ["C02", "C11", "C15", "C09", "C14"],
        "noise_c_tags": ["C06", "C07", "C05"],
        "key_keywords": [
            "ferc", "interconnection", "hyperscale", "data center",
            "power purchase", "gpu", "compute", "cooling", "colocation",
            "microsoft", "google", "amazon", "meta", "oracle",
            "ercot", "pjm", "miso", "power price", "electricity",
            "steel", "copper", "construction cost", "digitalbridge",
            "blackstone", "brookfield", "equinix",
        ],
        "noise_keywords": [
            "lng", "liquefaction", "solar itc", "solar ptc", "offshore wind",
            "turbine", "monopile", "asian financial crisis", "contagion",
            "oil price", "crude", "wti", "brent", "opec",
            "module", "bifacial", "photovoltaic",
        ],
    },
    "SR-02": {
        "sector_code": "SR-02",
        "name": "Solar + Storage",
        "a_tags": ["A04", "A05"],
        "key_c_tags": ["C04", "C06", "C09", "C02", "C10"],
        "noise_c_tags": ["C08", "C05"],
        "key_keywords": [
            "itc", "ptc", "obbba", "solar", "photovoltaic", "pv",
            "bifacial", "module", "bess", "battery", "storage",
            "feoc", "interconnection", "curtailment", "ercot",
            "caiso", "aluminum", "copper", "steel", "tax equity",
            "blattner", "nextera", "developer",
        ],
        "noise_keywords": [
            "lng", "liquefaction", "offshore wind", "turbine",
            "asian financial crisis", "oil price", "crude",
            "hyperscale", "data center", "gpu",
            "nuclear", "smr",
        ],
    },
    "SR-03": {
        "sector_code": "SR-03",
        "name": "Natural Gas Power",
        "a_tags": ["A01"],
        "key_c_tags": ["C05", "C01", "C03", "C09", "C02"],
        "noise_c_tags": ["C06", "C07", "C10"],
        "key_keywords": [
            "henry hub", "natural gas", "gas price", "spark spread",
            "capacity market", "pjm", "miso", "ercot", "combined cycle",
            "ccgt", "peaker", "gas turbine", "ge vernova", "siemens",
            "feedgas", "pipeline", "hormuz", "lng price",
            "steel", "construction cost", "utility offtaker",
        ],
        "noise_keywords": [
            "solar itc", "solar ptc", "module", "bifacial",
            "offshore wind", "monopile", "asian financial crisis",
            "hyperscale", "data center", "gpu",
        ],
    },
    "SR-04": {
        "sector_code": "SR-04",
        "name": "LNG / Export Terminals",
        "a_tags": ["A12", "A13"],
        "key_c_tags": ["C05", "C08", "C02", "C09"],
        "noise_c_tags": ["C06", "C07", "C10", "C11"],
        "key_keywords": [
            "lng", "liquefaction", "regasification", "export terminal",
            "force majeure", "take-or-pay", "offtaker", "qatarenergy",
            "hormuz", "strait", "shipping", "tanker", "feedgas",
            "henry hub", "steel", "bechtel", "kbr", "technip",
            "doe", "ferc", "export authorization",
        ],
        "noise_keywords": [
            "solar itc", "solar ptc", "module", "offshore wind",
            "data center", "hyperscale", "gpu",
            "toll road", "airport", "nuclear smr",
        ],
    },
    "SR-05": {
        "sector_code": "SR-05",
        "name": "Transmission and Grid",
        "a_tags": ["A17"],
        "key_c_tags": ["C02", "C15", "C09", "C04"],
        "noise_c_tags": ["C05", "C06", "C07"],
        "key_keywords": [
            "ferc", "transmission", "interconnection", "substation",
            "right-of-way", "rate case", "roe", "rate base",
            "steel", "aluminum", "construction cost", "permitting",
            "large load", "order 2023", "grid", "congestion",
        ],
        "noise_keywords": [
            "lng", "liquefaction", "solar module", "offshore wind turbine",
            "asian financial crisis", "oil price", "crude",
            "data center demand",
        ],
    },
    "SR-06": {
        "sector_code": "SR-06",
        "name": "Transport P3 / Toll Roads",
        "a_tags": ["A19", "A20", "A21"],
        "key_c_tags": ["C01", "C09", "C04", "C12"],
        "noise_c_tags": ["C05", "C06", "C07", "C11"],
        "key_keywords": [
            "toll road", "traffic", "p3", "ppp", "availability payment",
            "airport", "port", "passenger", "gdp", "recession",
            "government budget", "fiscal", "refinancing", "mini-perm",
            "steel", "concrete", "labor", "construction cost",
            "force majeure", "pandemic",
        ],
        "noise_keywords": [
            "lng", "solar itc", "offshore wind", "data center",
            "hyperscale", "gpu", "oil price", "henry hub",
        ],
    },
    "SR-07": {
        "sector_code": "SR-07",
        "name": "Offshore Wind",
        "a_tags": ["A07"],
        "key_c_tags": ["C07", "C09", "C04", "C02"],
        "noise_c_tags": ["C05", "C06", "C08"],
        "key_keywords": [
            "offshore wind", "vestas", "siemens gamesa", "monopile",
            "jones act", "vessel", "boem", "cfd", "contract for difference",
            "steel", "cable", "subsea", "permitting", "rps",
            "orsted", "bp", "equinor", "state utility",
        ],
        "noise_keywords": [
            "lng", "solar module", "itc ptc", "data center",
            "hyperscale", "hormuz", "asian financial crisis",
            "oil price", "natural gas price",
        ],
    },
    "SR-08": {
        "sector_code": "SR-08",
        "name": "Nuclear / SMR",
        "a_tags": ["A02", "A25"],
        "key_c_tags": ["C02", "C04", "C09"],
        "noise_c_tags": ["C06", "C07", "C05", "C08"],
        "key_keywords": [
            "nuclear", "smr", "nrc", "vogtle", "nuscale",
            "terrapower", "x-energy", "uranium", "fuel cost",
            "decommissioning", "licensing", "loan guarantee",
            "nuclear ptc", "baseload", "capacity factor",
        ],
        "noise_keywords": [
            "solar itc", "solar ptc", "module", "offshore wind",
            "lng", "data center", "hyperscale",
            "asian financial crisis", "oil price",
        ],
    },
    "SR-09": {
        "sector_code": "SR-09",
        "name": "Carbon Capture / CCUS",
        "a_tags": ["A26"],
        "key_c_tags": ["C02", "C04", "C05", "C09", "C12"],
        "noise_c_tags": ["C06", "C07", "C11"],
        "key_keywords": [
            "carbon capture", "ccs", "ccus", "45q", "sequestration",
            "co2", "carbon dioxide", "direct air capture", "dac",
            "class vi", "injection well", "epa permit",
            "occidental", "1pointfive", "exxon", "chevron", "bkv",
            "blue hydrogen", "enhanced oil recovery", "eor",
            "feedgas", "permian", "gulf coast",
            "steel", "construction cost", "pipeline",
        ],
        "noise_keywords": [
            "solar itc", "solar ptc", "module", "bifacial",
            "offshore wind", "monopile", "turbine",
            "hyperscale", "gpu", "data center",
            "toll road", "airport", "port",
        ],
    },
}

# Universal pass — these C-tags/keywords always pass regardless of sector
# (regime-wide stress that affects all infrastructure)
UNIVERSAL_PASS = {
    "c_tags": ["C01", "C12"],  # Macro/rates and financing markets
    "keywords": [
        "interest rate", "fed", "fomc", "sofr", "treasury",
        "credit spread", "bdc gate", "private credit",
        "tariff", "sanction", "construction cost",
        "refinancing", "mini-perm", "maturity",
    ],
}


# ── SECTOR MAPPING ────────────────────────────────────────────────────────────

def get_sectors_for_deal(deal: dict) -> list[dict]:
    """
    Map a deal to its sector entries using A-tags.

    A deal with multiple A-tags (e.g. A01+A09 for gas+digital) gets
    multiple sector assignments. Signal must be material for ANY of
    the deal's sectors to pass.

    Returns list of sector dicts, or empty list if no match.
    """
    deal_a = {t.strip() for t in deal.get("A-Tags", "").split(",")
              if t.strip()}
    if not deal_a:
        return []

    sectors = []
    for code, sector in SECTOR_INTELLIGENCE.items():
        if deal_a & set(sector["a_tags"]):
            sectors.append(sector)
    return sectors


# ── MATERIALITY CHECK ─────────────────────────────────────────────────────────

def is_signal_material_for_sector(signal: dict, sector: dict) -> tuple:
    """
    Check if a signal is material for a given sector.

    Returns (is_material: bool, reason: str).

    Check order:
    1. Universal pass keywords → True
    2. Noise keyword in headline/summary → False
    3. Key keyword match → True
    4. C-tag intersection with key_c_tags → True
    5. C-tag intersection with noise_c_tags only → False
    6. No match → True with LOW_CONFIDENCE (fail open)
    """
    headline = (signal.get("headline") or "").lower()
    summary = (signal.get("summary") or signal.get("raw_content") or "").lower()
    text = headline + " " + summary

    sig_c = set()
    try:
        sig_c = set(json.loads(signal.get("c_tags", "[]")))
    except Exception:
        pass

    sector_name = sector.get("name", "")

    # Step 0: Universal pass — macro/financing signals always material
    if sig_c & set(UNIVERSAL_PASS["c_tags"]):
        for kw in UNIVERSAL_PASS["keywords"]:
            if kw in text:
                return True, f"UNIVERSAL: '{kw}' — macro/financing signal"

    # Step 1: Noise keyword check (headline priority)
    for kw in sector.get("noise_keywords", []):
        if kw in headline:
            return False, f"NOISE: '{kw}' in headline"
    for kw in sector.get("noise_keywords", []):
        if kw in text and kw not in headline:
            # Noise in summary only — weaker signal, still filter
            return False, f"NOISE: '{kw}' in summary"

    # Step 2: Key keyword match
    for kw in sector.get("key_keywords", []):
        if kw in text:
            return True, f"MATCH: keyword '{kw}'"

    # Step 3: C-tag intersection with key tags
    key_overlap = sig_c & set(sector.get("key_c_tags", []))
    if key_overlap:
        return True, f"MATCH: C-tag {','.join(sorted(key_overlap))}"

    # Step 4: Only noise C-tags matched
    noise_overlap = sig_c & set(sector.get("noise_c_tags", []))
    if noise_overlap and not key_overlap:
        return False, f"NOISE: only noise C-tags {','.join(sorted(noise_overlap))}"

    # Step 5: Uncertain — fail open
    return True, "UNCERTAIN: no keyword/C-tag match — passed LOW_CONFIDENCE"


def is_signal_material_for_deal(signal: dict, deal: dict) -> tuple:
    """
    Check if signal is material for a deal across ALL its sectors.

    Signal passes if material for ANY sector the deal belongs to.
    Returns (is_material: bool, reason: str).
    """
    sectors = get_sectors_for_deal(deal)
    if not sectors:
        return True, "NO_SECTOR: deal has no sector assignment — passed"

    for sector in sectors:
        material, reason = is_signal_material_for_sector(signal, sector)
        if material:
            return True, f"{sector['name']}: {reason}"

    # Failed all sectors
    sector_names = [s["name"] for s in sectors]
    return False, f"FILTERED by all sectors: {', '.join(sector_names)}"


def filter_signals_for_deal(signals: list, deal: dict) -> tuple:
    """
    Split signals into material and filtered lists for a deal.

    Returns (material_signals, filtered_signals).
    Logs every filter to ge_sil_misses table.
    """
    sectors = get_sectors_for_deal(deal)
    if not sectors:
        return signals, []

    material = []
    filtered = []
    deal_name = deal.get("Deal Name", "")

    for sig in signals:
        is_mat, reason = is_signal_material_for_deal(sig, deal)
        if is_mat:
            material.append(sig)
        else:
            filtered.append(sig)
            _log_sil_miss(deal_name, sig, reason)

    return material, filtered


def _log_sil_miss(deal_name: str, signal: dict, reason: str):
    """Log a SIL filter decision to ge_sil_misses table. Deduped by signal+deal."""
    try:
        sig_id = signal.get("signal_id", "")
        conn = sqlite3.connect(DB_PATH)
        # Dedup check — only insert if pair doesn't already exist
        existing = conn.execute(
            "SELECT COUNT(*) FROM ge_sil_misses WHERE signal_id=? AND deal_name=?",
            (sig_id, deal_name),
        ).fetchone()[0]
        if existing > 0:
            conn.close()
            return
        conn.execute(
            "INSERT INTO ge_sil_misses "
            "(logged_at, deal_name, signal_id, headline, filter_reason) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M ET"),
                deal_name,
                sig_id,
                (signal.get("headline") or "")[:120],
                reason,
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # Non-critical — don't break pipeline


def init_sil_table():
    """Create ge_sil_misses table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ge_sil_misses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            logged_at TEXT,
            deal_name TEXT,
            signal_id TEXT,
            headline TEXT,
            filter_reason TEXT,
            sri_override TEXT
        )
    """)
    conn.commit()
    conn.close()


# ── STATS ─────────────────────────────────────────────────────────────────────

def get_sil_stats() -> dict:
    """Get SIL filter statistics for health monitor."""
    try:
        conn = sqlite3.connect(DB_PATH)
        total_misses = conn.execute(
            "SELECT COUNT(*) FROM ge_sil_misses"
        ).fetchone()[0]
        conn.close()
        return {"total_filtered": total_misses}
    except Exception:
        return {"total_filtered": 0}


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 58)
    print("SECTOR INTELLIGENCE LAYER — MODULE TEST")
    print("=" * 58)

    init_sil_table()

    # Test 1: Sector mapping
    print("\nTest 1: Sector mapping for pipeline deals")
    from sheets.pipeline import read_pipeline_from_sheet
    deals = read_pipeline_from_sheet()
    no_sector = []
    for d in deals:
        sectors = get_sectors_for_deal(d)
        if sectors:
            names = [f"{s['sector_code']} {s['name']}" for s in sectors]
            print(f"  {d['Deal Name'][:32]:32} -> {' + '.join(names)}")
        else:
            no_sector.append(d["Deal Name"])
            print(f"  {d['Deal Name'][:32]:32} -> NO SECTOR")
    print(f"\n  Deals with sector: {len(deals) - len(no_sector)}")
    print(f"  Deals without: {len(no_sector)}")

    # Test 2: Signal filter validation
    print("\nTest 2: Signal filter validation against GT-108 (SR-01+SR-03)")
    gt108 = [d for d in deals if "GT-108" in d.get("Deal Name", "")][0]

    test_signals = [
        {"headline": "Iran oil shock stirs memories of 1997 Asian Financial Crisis",
         "summary": "Oil prices surged.", "c_tags": '["C08","C01"]'},
        {"headline": "Rooftop solar photovoltaic systems 20% of Puerto Rico",
         "summary": "Solar PV expanding.", "c_tags": '["C06","C04"]'},
        {"headline": "FERC Large Load Rule decision April 30",
         "summary": "FERC interconnection ruling.", "c_tags": '["C02","C03"]'},
        {"headline": "When data centers bring their own power supply",
         "summary": "Data center power procurement.", "c_tags": '["C11"]'},
        {"headline": "Steel prices up 18% on tariff escalation",
         "summary": "Steel construction cost.", "c_tags": '["C09"]'},
        {"headline": "Henry Hub gas price spike on Hormuz disruption",
         "summary": "Natural gas prices elevated.", "c_tags": '["C05","C08"]'},
    ]

    for sig in test_signals:
        mat, reason = is_signal_material_for_deal(sig, gt108)
        status = "PASS" if mat else "FILTER"
        print(f"  {status:6} {sig['headline'][:55]:55} | {reason[:50]}")

    # Test 3: Signal count before/after SIL
    print("\nTest 3: Signal count before/after SIL")
    import sqlite3 as _sq
    conn = _sq.connect(DB_PATH)
    conn.row_factory = _sq.Row

    for target_name in ["GT-108 SB Energy Ohio", "Project Vega"]:
        target = [d for d in deals if d["Deal Name"] == target_name]
        if not target:
            continue
        target = target[0]

        rows = conn.execute(
            "SELECT signal_id, alert_level, c_tags, headline, summary, affected_deals "
            "FROM gs_signals WHERE affected_deals LIKE ? AND status != 'FILTERED' "
            "ORDER BY CAST(weighted_score AS REAL) DESC",
            (f"%{target_name}%",)
        ).fetchall()
        before = [dict(r) for r in rows]
        material, filtered = filter_signals_for_deal(before, target)

        print(f"  {target_name}:")
        print(f"    Before SIL: {len(before)} signals")
        print(f"    After SIL:  {len(material)} material, {len(filtered)} filtered")
        if filtered:
            print(f"    Filtered samples:")
            for s in filtered[:3]:
                print(f"      {s['headline'][:60]}")

    conn.close()

    # Test 5: SIL miss table
    print("\nTest 5: SIL miss table")
    conn = _sq.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM ge_sil_misses").fetchone()[0]
    print(f"  Total rows: {count}")
    rows = conn.execute(
        "SELECT deal_name, headline, filter_reason FROM ge_sil_misses LIMIT 5"
    ).fetchall()
    for r in rows:
        print(f"  {r[0][:25]:25} | {r[1][:40]:40} | {r[2][:30]}")
    conn.close()

    print("\nge/sector_intelligence.py operational.")