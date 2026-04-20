# GS — GroundSignals Classification
# PRD Section 3.5 — Processing Sequence Steps 3-6
# Pure Python deterministic classification. No API calls.
# Keyword matching for C/F/T/O tags, scoring, deal matching.
# Runs inline as part of orchestrator chain.
# Last Updated: April 2026

import json
import re
from datetime import datetime
from typing import Optional

from core.schema import Signal, SignalStatus, SourceType
from gs.store import write_signal, is_duplicate

# ── RELEVANCE GATE ────────────────────────────────────────────────────────────
# Runs BEFORE any classification. Signals must pass to be scored.

HARD_EXCLUSIONS = [
    # Sports
    "premier league", "champions league", "bundesliga", "serie a", "la liga",
    "nfl ", "nba ", "mlb ", "nhl ", "fifa", "world cup", "cricket", "rugby",
    "rout", " goal ", "scored a", "match result", "final score",
    "boxing", "heavyweight", "knockout", "sprint star",
    # Retail / Consumer
    "shoplifting", "discount phone", "mobile plan", "supermarket",
    "lidl", "aldi", "walmart deal", "amazon prime", "netflix", "spotify",
    # Entertainment / Celebrity
    "oscar", "grammy", "box office", "movie release", "film review",
    "album", "tour dates", "celebrity", "reality tv", "superyacht",
    "hospitality empire",
    # Generic politics without infrastructure nexus
    "oligarchy and presidency", "pensioners", "housing costs",
    "shoplifting a crime",
    # Medical / Pharma
    "cancer drug", "clinical trial", "drug licensed", "pharmaceutical",
    "vaccine trial", "hospital patient",
    # Other noise
    "smaller bottles", "prediction market", "wine", "cheese",
    "cooking", "recipe", "fashion",
]

INFRASTRUCTURE_TERMS = [
    # Energy
    "energy", " power ", "power plant", "power grid", "power price",
    "power supply", "power procurement", "electricity",
    " grid ", "megawatt", "gigawatt", " mw ", " gw ",
    "solar", " wind ", "wind farm", "wind energy",
    "battery", "storage", "nuclear", " gas ", "natural gas",
    "oil ", "oil price", "crude", " lng ", "pipeline",
    "refinery", "terminal", "bbl", "mmbtu",
    # Infrastructure asset classes
    "data center", "data centre", "transmission", "substation",
    "interconnect", "toll road", "airport", " port ",
    "water utility", "wastewater", "fiber", "broadband", "telecom",
    "utility", "utilities",
    # Finance / Capital markets
    "project finance", "infrastructure fund", " debt ", "equity",
    "credit spread", " bond ", " loan ", "refinanc", "maturity",
    "interest rate", " fed ", "fomc", "sofr", "treasury",
    "private credit", " bdc ", "spread", "financing",
    "lender", " bank ", "credit market",
    # Corporate structural events on infra entities — privatisations, IPOs,
    # capital raises, SOE restructurings. FT-style thin summaries often
    # describe these without the word "energy" or "infrastructure."
    "privatisation", "privatization", "privatise", "privatize",
    "state-owned", " soe ",
    "capital increase", "capital raise", "rights issue",
    " ipo ", "secondary offering", "share offering",
    "nationalisation", "nationalization",
    # Named EU / energy-adjacent entities whose stories often lack
    # generic infra keywords in thin wire summaries
    "gazprom", " sefe ", "uniper", "naturgy", "equinor",
    "engie", "iberdrola", "enel", "rwe", "e.on", "fortum",
    "venture global", " vg ", "cheniere", "freeport lng",
    "bechtel", "technip", "fluor",
    # Policy / Regulatory
    "ferc", " ira ", "obbba", " doe ", " eia ", " iea ",
    "pjm", "ercot", "miso", "caiso",
    "tariff", "sanction", "permitting", "regulatory", "legislation",
    "tax credit", "itc", "ptc",
    "commission meeting", "sunshine notice", "commission decision",
    "order issued",
    # Geopolitical with energy nexus
    "hormuz", "strait", "opec", "iran", "crude", "wti", "brent",
    "supply chain", "construction cost", "steel", "aluminum", "copper",
    # Sponsors / Developers
    "blackstone", "brookfield", "kkr", "macquarie", "edf", "nextera",
    " bp ", "shell", "exxon", "chevron", "totalenergies",
    "infrastructure", "construction",
    # Data centre demand-side (broadly useful, not ILS-specific)
    "hyperscaler", "hyperscale",
    # AI labs as offtaker credit — Anthropic/OpenAI ARR and capex commitments
    # are the ultimate offtaker-quality signal for DC deals per Sri's
    # DC Axis 1 framework. Kept to distinctive lab names + AI-finance phrases
    # that won't over-match generic "AI" mentions in non-infra content.
    "anthropic", "openai", "mythos model",
    "ai model", "ai lab", "ai factory", "ai revenue", "ai capex",
    "ai training", "ai inference",
    " llm ", "large language model",
    " gpu ", "gpu cluster", "gpu financing",
    # ILS / Insurance-linked securities — added 2026-04-17 (DC Axis 7 watch)
    "cat bond", "catastrophe bond",
    "industry loss warranty", " ilw ",
    "insurance-linked", "insurance linked",
    "parametric", "sidecar",
    "ils fund", "ils market", "ils investor", "ils allocation",
    # Macro with infra relevance
    "imf", "world bank", "gdp", "recession", "inflation",
    "cpi ", "rate decision", "monetary policy",
]


def is_infrastructure_relevant(headline: str, summary: str) -> tuple:
    """
    Infrastructure relevance gate. Runs before any classification.

    Step 1: Hard exclusion keywords kill immediately.
    Step 2: Must contain at least one infrastructure term.
    Step 3: Ambiguous signals (infra term in summary only) flagged LOW.

    Args:
        headline: Signal headline text.
        summary: Signal summary/content text.

    Returns:
        (relevant: bool, confidence: str, reason: str)
        confidence: "HIGH", "LOW", or "FILTERED"
    """
    hl = (headline or "").lower()
    sm = (summary or "").lower()
    text = hl + " " + sm

    # Step 0: Sponsored / advertising content — kill before any other logic.
    # Trade press (DCD, Artemis, others) prefix advertorials with "Sponsored:".
    # Even when the body has infra terms it's vendor marketing, not signal.
    if hl.startswith("sponsored:") or hl.startswith("sponsored "):
        return False, "FILTERED", "Sponsored content"

    # Step 1: Hard exclusion
    for excl in HARD_EXCLUSIONS:
        if excl in text:
            return False, "FILTERED", f"Hard exclusion: '{excl}'"

    # Step 2: Infrastructure terms check
    hl_has_infra = any(term in hl for term in INFRASTRUCTURE_TERMS)
    sm_has_infra = any(term in text for term in INFRASTRUCTURE_TERMS)

    if not sm_has_infra:
        return False, "FILTERED", "No infrastructure terms found"

    # Step 3: Ambiguous — infra only in summary, not headline
    if sm_has_infra and not hl_has_infra:
        return True, "LOW", "Infrastructure term in summary only"

    return True, "HIGH", "Infrastructure relevant"


# ── C-TAG KEYWORD MAP ─────────────────────────────────────────────────────────

C_TAG_KEYWORDS = {
    "C01": ["fed", "fomc", "treasury", "yield", "inflation", "cpi", "rate hike",
            "rate cut", "monetary policy", "powell", "interest rate", "sofr",
            "basis point", "bps"],
    "C02": ["ferc", "sec", "doe ", "epa", "federal register", "nrc",
            "federal regulat", "regulatory approval",
            "commission meeting", "sunshine notice", "commission decision",
            "order issued"],
    "C03": ["pjm", "ercot", "miso", "caiso", "spp", "nerc", "rto",
            "iso ", "state regulat", "public utility commission", "puc"],
    "C04": ["congress", "senate", "house ", "irs", "tax credit", "itc", "ptc",
            "inflation reduction act", "ira ", "obbba", "reconciliation",
            "legislation", "bipartisan", "legislative"],
    "C05": ["oil", " gas ", "lng ", "pipeline", "permian", "natural gas",
            "crude", "petroleum", "opec", "barrel", "brent", "wti",
            "henry hub", "refiner"],
    "C06": ["solar", "photovoltaic", " pv ", "module", "bifacial",
            "solar panel", "solar farm", "utility-scale solar"],
    "C07": ["wind ", "turbine", "offshore wind", "onshore wind",
            "wind farm", "wind energy", "vestas", "siemens gamesa"],
    "C08": ["iran", "hormuz", "tariff", "sanctions", "china trade",
            "geopolit", "conflict", "ceasefire", "war ", "military",
            "opec", "strait", "blockade", "invasion"],
    "C09": ["steel", "aluminum", "copper", "concrete", "lumber",
            "commodity price", "construction cost", "material cost",
            "supply chain", "raw material"],
    "C10": ["battery", "bess", "storage", "lithium", "energy storage",
            "grid storage"],
    "C11": ["data center", "data centre", "gpu", "hyperscal",
            "colocation", "fiber", "telecom", "digital infra",
            "cloud computing", "ai infrastructure",
            "anthropic", "openai", "mythos model",
            "ai model", "ai lab", "ai factory",
            "ai training", "ai inference", "large language model"],
    "C12": ["credit spread", "loan", " debt", "bond ", "financing",
            "lender", " bank", "bdc ", "private credit", "syndication",
            "capital market", "spread widen", "credit market"],
    "C13": ["dollar", "euro", " fx ", "currency", "exchange rate",
            "yen", "pound", "forex", "emerging market currency"],
    "C14": ["acquisition", "merger", "financial close", "equity raise",
            "sponsor", "developer", "ipo", "fund ", "stake",
            "joint venture", "partnership"],
    "C15": ["transmission", "substation", "grid ", "interconnect",
            "power line", "high voltage", "hvdc", "grid upgrade"],
    # ── Capital-stack & market-structure tags (added 2026-04-19, fix #2) ────
    # C16 caught the 7-print ILS → DC-underwriting thread that decayed at
    # GREEN across Apr 13-18 (see alpha_ledger.md ALF-20260419-1).
    # C17 caught the Maine state-wide DC moratorium (Apr 15).
    # C18 isolates rating-agency methodology events which drive IG-uplift
    # paths (key to ALF-20260419-1 Structural hypothesis validation).
    "C16": [  # Structured finance / ILS / capital-markets innovation
            # Bare "ils " collided on "hails " substring — require multi-word
            # patterns for ILS matches. Covers normal Artemis / SIFMA phrasing.
            "ils market", "ils capital", "ils fund", "ils sector",
            "ils investor", "ils vehicle", "growing ils",
            "insurance-linked", "insurance linked",
            "cat bond", "catastrophe bond",
            " sidecar", "casualty sidecar",
            "retrocession", "third-party capital", "third party capital",
            "securitization", "securitisation",
            "london bridge 2", "london bridge pcc",
            "rating uplift", "ig uplift", "investment grade uplift",
            "risk transfer", "capital relief",
            "fermat capital", "elementum advisors"],
    "C17": [  # State-legislative siting / local-government restriction
            "moratorium", "construction ban", "bit barn ban",
            "data centre ban", "data center ban",
            "ban data center", "ban data centre",
            "ban new data center", "ban new data centre",
            "state to ban", "state-wide ban", "statewide ban",
            "state legislat", "state senate passes",
            "county ban", "county moratorium",
            "siting ban", "legislative ban",
            "permitting ban", "zoning restrict"],
    "C18": [  # Rating agency methodology / credit ratings
            "moody's", "s&p global", "s&p ratings", "fitch ratings",
            "kbra", "rating methodology", "rating criteria",
            "rating action", "rating agency",
            "credit rating", "methodology note",
            "sector outlook", "ratings watch"],
}

# ── C-TAG ABBREVIATION MAP (word-boundary matched) ────────────────────
#
# Short uppercase abbreviations (ILS, KBRA, IG, PCC) are frequently used
# standalone in domain text — "Diversification story of ILS a consideration"
# (GS-875 headline) — and bare substring matching can't handle them safely:
# - "ils " (with trailing space) collides with "hails ", "entails ", etc.
# - "ils" (no space) collides with dozens of innocuous English substrings.
#
# Solution: regex word-boundary matching applied AFTER the text is
# lowercased. `\bils\b` matches standalone "ils" (and "ILS" after lowercasing)
# but not internal substrings in "hails", "entails", "foils", etc.
#
# Keep this list curated — only add abbreviations that are (a) highly
# distinctive in our domain and (b) unlikely to collide with common words.
C_TAG_ABBREVS = {
    "C16": ["ils", "pcc"],                # ILS, Protected Cell Company
    "C18": ["kbra", "dbrs", "ig"],        # small rating agencies + IG tier
}

# Semantic names for C-tags — surfaced in UNMAPPED diagnostics and
# downstream displays so codes like C16 read as "C16 (Struct)" rather
# than opaque numbers.
C_TAG_NAMES = {
    "C01": "Rates",       "C02": "FedReg",     "C03": "RTO/ISO",
    "C04": "Legislation", "C05": "Oil/Gas",    "C06": "Solar",
    "C07": "Wind",        "C08": "Geopolit",   "C09": "Commodity",
    "C10": "Storage",     "C11": "Digital",    "C12": "Credit",
    "C13": "FX",          "C14": "Sponsor",    "C15": "Transmission",
    "C16": "Struct",      "C17": "Siting-State", "C18": "RatingMethod",
}

# ── A-TAG DERIVATION ──────────────────────────────────────────────────────────

C_TO_A_MAP = {
    "C05": ["A01", "A12", "A14"],
    "C06": ["A04"],
    "C07": ["A06", "A07"],
    "C10": ["A05"],
    "C11": ["A09"],
    "C15": ["A17"],
}

A_TAG_KEYWORDS = {
    "A01": ["gas power", "gas-fired", "ccgt", "natural gas plant",
            "peaker", "combined cycle"],
    "A02": ["nuclear", "reactor", "nrc license"],
    "A04": ["solar"],
    "A05": ["battery", "bess", "storage"],
    "A06": ["onshore wind"],
    "A07": ["offshore wind"],
    "A09": ["data center", "data centre", "hyperscal", "colocation"],
    "A12": ["lng ", "liquefied natural gas", "lng export", "lng terminal"],
    "A14": ["gas pipeline", "midstream"],
    "A17": ["transmission", "grid", "substation"],
    "A19": ["toll road", "highway", "transport p3"],
    "A25": ["smr", "small modular reactor"],
    "A27": ["critical mineral", "lithium", "rare earth"],
}

# ── F-TAG SOURCE CONFIDENCE ───────────────────────────────────────────────────

SOURCE_CONFIDENCE = {
    "Financial Times":      ("F1", 0.90),
    "FT Energy":            ("F1", 0.90),
    "FT Markets":           ("F1", 0.90),
    "FT Companies":         ("F1", 0.90),
    "Wall Street Journal":  ("F1", 0.90),
    "Bloomberg":            ("F1", 0.90),
    "Reuters":              ("F1", 0.90),
    "CNBC Economy":         ("F1", 0.85),
    "IJGlobal":             ("F6", 0.80),
    "PFI":                  ("F6", 0.80),
    "Recharge News":        ("F7", 0.78),
    "PV Magazine":          ("F7", 0.78),
    "LNG Prime":            ("F8", 0.75),
    "Data Center Dynamics":  ("F8", 0.75),
    "EIA Today In Energy":  ("F5", 0.85),
    "Federal Reserve News": ("F2", 0.88),
    "FERC News":            ("F2", 0.85),
    "DOE News":             ("F3", 0.85),
    "IEA News":             ("F5", 0.83),
    "IMF News":             ("F3", 0.83),
    "SEIA News":            ("F19", 0.55),
    # AGC = Associated General Contractors of America
    # Primary US construction trade body
    # Publishes: construction cost index, labor data, tariff impact, material prices
    # Reclassified F19->F12 April 2026 — signals were stuck DRAFT at 0.55
    "AGC News":             ("F12", 0.70),
    "Construction Dive":    ("F16", 0.65),
    "Utility Dive":         ("F16", 0.70),
    "Natural Gas Intelligence": ("F8", 0.75),
    "Al Jazeera Economy":   ("F16", 0.60),
    # New sources added April 12 2026
    "PV Magazine US":       ("F7", 0.75),
    "Energy Monitor":       ("F7", 0.73),
    "Oil Price":            ("F16", 0.62),
    "Rigzone":              ("F8", 0.70),
    "T&D World":            ("F7", 0.73),
    "Power Magazine":       ("F7", 0.75),
    "The Register DC":      ("F16", 0.62),
    "Infrastructure Investor": ("F6", 0.78),
    "Atlantic Council":     ("F16", 0.65),
    # New sources added April 13 2026
    "RBN Energy":           ("F8", 0.73),   # Premier US midstream/gas analysis
    "Renewable Energy World": ("F7", 0.73), # Renewables trade press
    "Windpower Monthly":    ("F7", 0.75),   # Global wind industry trade press
    # Batch 2 — April 13 2026
    "World Nuclear News":   ("F7", 0.75),   # Global nuclear trade press
    "Solar Power World":    ("F7", 0.73),   # US solar trade press
    "PV Tech":              ("F7", 0.75),   # Global PV technology press
    "Energy Storage News":  ("F7", 0.75),   # BESS/storage trade press
    "LNG Prime":            ("F8", 0.73),   # LNG trade press
    "Artemis":              ("F8", 0.70),   # Insurance/catastrophe risk
}

# ── PIPELINE DEALS ────────────────────────────────────────────────────────────
# Loaded dynamically from Google Sheets. Cached per classify session.
# Falls back to 3 hardcoded deals if Sheets read fails.

_pipeline_cache = None
_pipeline_loaded = False

FALLBACK_DEALS = [
    {"Deal Name": "Project Vega", "A-Tags": "A04, A05",
     "C-Tags": "C06, C10, C04, C09",
     "Key Commodities": "Aluminum, copper, steel, modules",
     "State": "", "Asset Type": "Solar + Storage", "Status": "ACTIVE"},
    {"Deal Name": "GT-108 SB Energy Ohio", "A-Tags": "A01, A09",
     "C-Tags": "C05, C11, C02",
     "Key Commodities": "Natural gas, steel, copper",
     "State": "Ohio", "Asset Type": "Gas + Digital Infra", "Status": "ACTIVE"},
    {"Deal Name": "GT-109 SB Energy Milam", "A-Tags": "A09, A01",
     "C-Tags": "C11, C05, C03",
     "Key Commodities": "ERCOT power prices, gas",
     "State": "Texas", "Asset Type": "Digital Infra + Power", "Status": "ACTIVE"},
]


def load_pipeline_deals() -> list[dict]:
    """
    Load pipeline deals from Google Sheets (cached per session).

    Calls sheets/pipeline.py read_pipeline_from_sheet() once per
    classify run. Falls back to 3 hardcoded deals on failure.
    """
    global _pipeline_cache, _pipeline_loaded
    if _pipeline_loaded:
        return _pipeline_cache

    try:
        from sheets.pipeline import read_pipeline_from_sheet
        deals = read_pipeline_from_sheet()
        if deals:
            _pipeline_cache = deals
            _pipeline_loaded = True
            return deals
    except Exception as e:
        print(f"  WARN: Pipeline Sheets read failed: {e}")

    print("  Using fallback pipeline deals (3 hardcoded)")
    _pipeline_cache = FALLBACK_DEALS
    _pipeline_loaded = True
    return _pipeline_cache


def reset_pipeline_cache():
    """Clear the pipeline cache — forces re-read from Sheets on next call."""
    global _pipeline_cache, _pipeline_loaded
    _pipeline_cache = None
    _pipeline_loaded = False


def _get_deal_name_keywords(deal_name: str) -> list[str]:
    """
    Extract searchable keywords from deal name.

    Filters out generic infrastructure words that would match
    every signal (energy, power, solar, gas, etc.)
    """
    name_lower = deal_name.lower()
    # Generic words that appear in deal names but match too broadly
    skip = {
        "project", "the", "a", "and", "of", "for",
        "energy", "power", "solar", "wind", "gas", "lng",
        "data", "center", "digital", "infra", "infrastructure",
        "clean", "portfolio", "new", "industrial",
    }
    keywords = [name_lower]  # Full name always matches
    parts = name_lower.split()
    # Only add specific words (deal-identifying, not sector-generic)
    keywords.extend([p for p in parts if p not in skip and len(p) > 3])
    # Add hyphenated variants
    for p in parts:
        if "-" in p:
            keywords.append(p.replace("-", ""))
    return keywords


def match_deals(text: str, c_tags: list, a_tags: list,
                pipeline_deals: list) -> list[tuple]:
    """
    Match a signal against pipeline deals using 3-tier specificity system.

    Tier 1 (DEAL-SPECIFIC): Deal name/keywords appear in signal text.
        Written to affected_deals. Full SP weight.
    Tier 2 (ASSET+GEO): A-tag match AND geography (state/ISO) match.
        Written to affected_deals. Half SP weight.
    Tier 3 (SECTOR-GENERAL): C-tag or A-tag match but no specificity.
        NOT written to affected_deals. Excluded from counts.

    Only Tier 1 and Tier 2 results are returned. Tier 3 is silent.

    Returns:
        List of (deal_name, tier, match_layer, match_reason) tuples.
    """
    sig_c = set(c_tags)
    sig_a = set(a_tags)
    matches = []

    for deal in pipeline_deals:
        name = deal.get("Deal Name", "")
        status = deal.get("Status", "").upper()
        if status in ("CLOSED", "DEFERRED"):
            continue

        deal_a = {t.strip() for t in deal.get("A-Tags", "").split(",")
                  if t.strip()}
        state = deal.get("State", "").strip().lower()
        rto = deal.get("RTO", "").strip().lower()

        # Tier 1: Deal name explicitly in signal text
        deal_kws = _get_deal_name_keywords(name)
        if any(kw in text for kw in deal_kws if len(kw) > 4):
            matches.append((name, 1, "DEAL-SPECIFIC",
                            f"Deal name keyword in signal text"))
            continue

        # Tier 2: A-tag match WITH geography context
        a_overlap = sig_a & deal_a
        geo_match = False
        geo_term = ""
        if state and state != "unknown" and len(state) > 1 and state in text:
            geo_match = True
            geo_term = state
        if rto and rto != "unknown" and len(rto) > 1 and rto in text:
            geo_match = True
            geo_term = rto

        # Tier 2a: A-tag + geography = strong regional match
        if a_overlap and geo_match:
            matches.append((name, 2, "ASSET+GEO",
                            f"A-tag {','.join(sorted(a_overlap))} + geo '{geo_term}'"))
            continue

        # Tier 2b: Geography alone with sector-relevant signal
        # (signal mentions deal's state/RTO even without A-tag overlap)
        if geo_match and sig_c:
            deal_c = {t.strip() for t in deal.get("C-Tags", "").split(",")
                      if t.strip()}
            if sig_c & deal_c:
                matches.append((name, 2, "GEO+CTAG",
                                f"Geo '{geo_term}' + C-tag overlap"))
                continue

        # Tier 3: everything else — NOT returned, not written to affected_deals

    return matches

# ── SECOND ORDER TEMPLATES ────────────────────────────────────────────────────

REGIME_CONTEXT = "R0 Compound Stress (Hormuz crisis Day 42+)"

MECHANISM_TEMPLATES = {
    "C08": ("Geopolitical signal transmits through energy supply chain "
            "disruption and shipping cost escalation"),
    "C09": ("Construction commodity price movement affects EPC budget "
            "assumptions and contingency adequacy. Moody's construction "
            "phase CDR 0.94%/yr, LGD 27.5% anchor risk assessment"),
    "C05": ("Energy price signal transmits through fuel cost to "
            "operating margins and offtaker economics"),
    "C01": ("Rate/macro signal affects WACC assumptions and refinancing "
            "economics. 2020-21 vintage faces +375bps vs underwriting"),
    "C04": ("Policy/legislative signal affects tax credit eligibility "
            "and developer IRR requirements"),
    "C06": ("Solar market signal affects module pricing, EPC costs, "
            "and development pipeline economics"),
    "C11": ("Digital infrastructure signal affects power procurement "
            "strategy and interconnection queue dynamics"),
    "C12": ("Credit market signal transmits through lender cost of "
            "funds and credit committee risk appetite. E01 GFC "
            "pattern: financing breaks before assets"),
    "C02": ("Federal regulatory action affects permitting timelines "
            "and compliance cost assumptions"),
}


# ── CLASSIFICATION ENGINE ─────────────────────────────────────────────────────

def classify_item(raw: dict) -> dict:
    """
    Classify a single raw article dict into fully populated Signal fields.

    Pure Python deterministic classification using keyword matching for
    C/F/T/O tags, alert scoring, confidence, deal matching, and
    second_order inference.

    Args:
        raw: Dict from gs/fetch.py with keys: source_name, url,
             publication_date, headline, raw_content/summary, c_tags.

    Returns:
        Dict with all Signal fields populated, ready for Signal() construction.
    """
    headline = raw.get("headline", "")
    summary = raw.get("summary", raw.get("raw_content", ""))
    text = (headline + " " + summary).lower()
    source = raw.get("source_name", "Unknown")

    # ── C-TAGS ────────────────────────────────────────────────────────
    c_tags = set()
    # Start with hints from fetch source registry
    for hint in raw.get("c_tags", []):
        if isinstance(hint, str):
            c_tags.add(hint)

    # Keyword enrichment — substring match (default)
    for tag, keywords in C_TAG_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                c_tags.add(tag)
                break

    # Abbreviation enrichment — word-boundary match.
    # Prevents "ils" / "ig" / "pcc" from colliding with substrings inside
    # "hails", "big", "exceptional", etc., while still catching bare uses
    # like "ILS a consideration" or "IG uplift" after lowercasing.
    for tag, abbrevs in C_TAG_ABBREVS.items():
        for abbrev in abbrevs:
            if re.search(r'\b' + re.escape(abbrev) + r'\b', text):
                c_tags.add(tag)
                break

    c_tags = sorted(c_tags)

    # ── A-TAGS ────────────────────────────────────────────────────────
    a_tags = set()
    for ct in c_tags:
        for at in C_TO_A_MAP.get(ct, []):
            a_tags.add(at)
    for tag, keywords in A_TAG_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                a_tags.add(tag)
                break
    a_tags = sorted(a_tags)

    # ── F-TAGS + CONFIDENCE ───────────────────────────────────────────
    source_info = SOURCE_CONFIDENCE.get(source, ("F16", 0.60))
    f_tag = source_info[0]
    confidence = source_info[1]

    # ── T-TAG ─────────────────────────────────────────────────────────
    t1_words = ["breaking", "today", "immediate", "urgent", "hours",
                "just announced", "breaking:", "this morning"]
    t3_words = ["forecast", "outlook", "long-term", "2027", "2028",
                "multi-year", "decade"]
    t_tag = "T2"  # default
    for w in t1_words:
        if w in text:
            t_tag = "T1"
            break
    if t_tag == "T2":
        for w in t3_words:
            if w in text:
                t_tag = "T3"
                break

    # ── O-TAG ─────────────────────────────────────────────────────────
    o_tag = None
    o_keywords = {
        "O1": ["construction", "greenfield", "build", "development",
               "epc", "financial close"],
        "O2": ["refinanc", "refi", "maturity", "repay"],
        "O3": ["back-leverage", "loan-on-loan", "nav ", "fund finance"],
        "O4": ["merger", "acquisition", "sale", "m&a", "advisory",
               "divest"],
        "O5": ["equity", "mezzanine", "preferred", "sponsor equity"],
    }
    for tag, keywords in o_keywords.items():
        for kw in keywords:
            if kw in text:
                o_tag = tag
                break
        if o_tag:
            break

    # ── INFRASTRUCTURE RELEVANCE CHECK ──────────────────────────────
    infra_anchors = [
        "energy", " power ", "power plant", "power grid",
        "power procurement", "power price",
        " grid ", "utility", "pipeline", "solar",
        " wind ", "wind farm", "wind energy",
        "storage", "battery", "data center", "data centre",
        "fiber", "infrastructure", "financing", " debt ", " loan ",
        "credit", "construction", "developer", "sponsor", "offtake",
        "capacity", "megawatt", " mw ", " gw ", "transmission",
        "interconnect", "tariff", "commodity", "steel", "aluminum",
        "copper", " lng ", "nuclear", "refinanc", "project finance",
        " ppa ", " epc ", "ferc", "ercot", "pjm", "miso",
    ]
    has_infra_anchor = any(anchor in text for anchor in infra_anchors)
    geopolitical_only = ("C08" in c_tags and not has_infra_anchor
                         and not any(t in c_tags for t in
                                     ["C05", "C06", "C07", "C09",
                                      "C11", "C12", "C15"]))

    # ── DEAL MATCHING (dynamic from Sheets, 3-layer hierarchy) ──────
    pipeline_deals = load_pipeline_deals()
    deal_matches = match_deals(text, c_tags, a_tags, pipeline_deals)

    matched_deals = []
    pipeline_risk = 0
    risk_rationale = None

    if deal_matches:
        # New format: (name, tier, layer, reason)
        tier1 = [m for m in deal_matches if m[1] == 1]
        tier2 = [m for m in deal_matches if m[1] == 2]

        matched_deals = [name for name, _, _, _ in tier1 + tier2]
        if tier1 or tier2:
            pipeline_risk = 1

        parts = []
        if tier1:
            parts.append(f"T1: {', '.join(n for n,_,_,_ in tier1)}")
        if tier2:
            parts.append(f"T2: {', '.join(n for n,_,_,_ in tier2)}")

        risk_rationale = (
            f"{' | '.join(parts)} under {REGIME_CONTEXT}. "
            f"[{len(tier1)} deal-specific, {len(tier2)} sector-regional]"
        )

    # ── ALERT LEVEL SCORING ───────────────────────────────────────────
    score = 0

    # Geopolitical-only signals capped at GREEN
    if geopolitical_only:
        score = 20
    else:
        # Core infrastructure C-tag points
        if "C08" in c_tags and has_infra_anchor:
            score += 25       # Geopolitical with infra relevance
        if "C05" in c_tags:
            score += 20       # Oil & gas — core infra commodity
        if "C09" in c_tags:
            score += 20       # Construction commodities
        if "C01" in c_tags:
            score += 15       # Macro/rates — WACC impact
        if "C02" in c_tags or "C03" in c_tags:
            score += 15       # Regulatory
        if "C04" in c_tags:
            score += 15       # Policy/legislative
        if "C12" in c_tags:
            score += 15       # Financing markets
        if "C06" in c_tags or "C07" in c_tags:
            score += 10       # Solar/wind
        if "C11" in c_tags:
            score += 10       # Digital infra
        # Named deal match bonus
        if matched_deals:
            score += 20
        # Compound signal bonus (geopolitical + commodity together)
        if "C08" in c_tags and "C09" in c_tags:
            score += 10
        # Binary event keyword match bonus
        binary_kws = ["fomc", "ferc", "obbba", "reconciliation",
                      "interconnection", "large load"]
        if any(bk in text for bk in binary_kws) and has_infra_anchor:
            score += 10
        # T1 urgency bonus
        if t_tag == "T1":
            score += 10
        # Cap: signals without infra anchor but with C-tags get dampened
        if not has_infra_anchor and score > 55:
            score = 55

    score = min(100, score)

    if score >= 75:
        alert_level = "RED"
        status = SignalStatus.ACTIVE
    elif score >= 45:
        alert_level = "AMBER"
        status = SignalStatus.ACTIVE
    else:
        alert_level = "GREEN"
        status = SignalStatus.DRAFT if confidence < 0.60 else SignalStatus.ACTIVE

    # Tag geopolitical-only signals
    if geopolitical_only:
        alert_level = "GREEN"
        score = min(score, 30)

    if matched_deals:
        pipeline_risk = 1
        risk_rationale = (
            f"Signal touches {', '.join(matched_deals)} via "
            f"{'|'.join(c_tags)} tag overlap under {REGIME_CONTEXT}."
        )

    # ── SECOND ORDER ──────────────────────────────────────────────────
    #
    # 2026-04-19 classifier-quality fix #1: template-fallback removal.
    #
    # The prior implementation emitted MECHANISM_TEMPLATES[c_tag] as the
    # primary second_order text whenever any of the signal's c_tags had a
    # template registered. In practice that meant every Artemis signal this
    # week got "Federal regulatory action affects permitting timelines..."
    # stamped on it because C02 was picked up by incidental keyword / source
    # hints — the template fired regardless of whether regulatory-permitting
    # was the signal's actual mechanism. That produced text that *looked*
    # like analysis but was c-tag boilerplate, and masked a seven-print
    # pre-issuance ILS / DC-finance thread at GREEN (see alpha_ledger.md
    # ALF-20260419-1 late entry for the contemporaneous record).
    #
    # New behaviour: second_order is honest about what the classifier does
    # and doesn't know.
    #   - If a genuinely signal-specific datum exists (matched_deals), emit
    #     that. It's the only current signal-specific inference path.
    #   - Otherwise emit UNMAPPED with diagnostic context (c_tags, source).
    #     UNMAPPED count is a quality metric for GR weekly review.
    #
    # MECHANISM_TEMPLATES is retained in the module (unused here) as a
    # c-tag-level context reference for future signal-specific inference
    # logic. Do not re-wire it into second_order without that logic.

    timeline_map = {"T1": "days", "T2": "weeks to months", "T3": "months"}
    timeline = timeline_map.get(t_tag, "weeks")

    # Render c_tags with semantic names for readability in diagnostics.
    def _label(ct):
        name = C_TAG_NAMES.get(ct)
        return f"{ct} ({name})" if name else ct
    tag_labels = [_label(ct) for ct in c_tags[:3]]

    if matched_deals:
        second_order = (
            f"Direct pipeline exposure: {', '.join(matched_deals)} "
            f"via {'|'.join(tag_labels) or 'no c_tag'} on {timeline} "
            f"timeline under {REGIME_CONTEXT}. Mechanism: UNMAPPED "
            f"(classifier has no signal-specific inference; hand-review "
            f"for transmission detail)."
        )
    else:
        second_order = (
            f"UNMAPPED — classifier produced no signal-specific mechanism. "
            f"c_tags=[{', '.join(tag_labels) or 'none'}] source='{source}' "
            f"t_tag={t_tag} regime={REGIME_CONTEXT}. Hand-review required "
            f"for mechanism inference; see classifier fix 2026-04-19 #1."
        )

    # ── OPPORTUNITY ───────────────────────────────────────────────────
    opp_alert = 0
    opp_sector = None
    opp_rationale = None
    opp_words = ["opportunity", "mandate", "awarded", "selected",
                 "financial close", "fid", "sanctioned"]
    for w in opp_words:
        if w in text:
            opp_alert = 1
            opp_sector = a_tags[0] if a_tags else None
            opp_rationale = f"Potential origination signal in {source}."
            break

    # ── LINKEDIN ──────────────────────────────────────────────────────
    linkedin = 1 if (alert_level == "RED" or
                     ("C08" in c_tags and len(c_tags) >= 3)) else 0

    # ── THEME TAGS ────────────────────────────────────────────────────
    themes = []
    if "C08" in c_tags and "C05" in c_tags:
        themes.append("Hormuz_supply")
    if "C09" in c_tags:
        themes.append("construction_cost")
    if "C12" in c_tags:
        themes.append("BDC_gates")
    if "C04" in c_tags and "C06" in c_tags:
        themes.append("OBBBA_sprint")
    if "C11" in c_tags:
        themes.append("data_center_power")
    if "C05" in c_tags and "C12" not in c_tags:
        themes.append("LNG_origination")

    return {
        "headline":         headline[:120],
        "summary":          (summary or "")[:500],
        "raw_content":      raw.get("raw_content", summary or "")[:3000],
        "url":              raw.get("url", ""),
        "source_name":      source,
        "publication_date": raw.get("publication_date", ""),
        "c_tags":           json.dumps(c_tags),
        "f_tags":           json.dumps([f_tag]),
        "t_tag":            t_tag,
        "o_tag":            o_tag,
        "second_order":     second_order,
        "classifier_model": "groundtruth-v2-keyword",
        "confidence":       confidence,
        "alert_level":      alert_level,
        "status":           status,
        "weighted_score":   float(score),
        "raw_score":        float(score),
        "pipeline_risk_alert":   pipeline_risk,
        "affected_deals":        json.dumps(matched_deals),
        "risk_alert_confidence": "HIGH" if pipeline_risk else None,
        "risk_alert_rationale":  risk_rationale,
        "opportunity_alert":     opp_alert,
        "opportunity_sector":    opp_sector,
        "opportunity_type":      o_tag if opp_alert else None,
        "opportunity_urgency":   t_tag if opp_alert else None,
        "opportunity_rationale": opp_rationale,
        "linkedin_candidate":    linkedin,
        "theme_tags":            json.dumps(themes),
    }


# ── CLASSIFY AND STORE ────────────────────────────────────────────────────────

def classify_and_store(raw: dict, fetch_run_id: str = None) -> Optional[str]:
    """
    Classify a raw article and write the resulting Signal to database.

    Runs relevance gate first. If filtered, writes with status=FILTERED
    and skips scoring. Otherwise runs classify_item() then dedup then write.

    Args:
        raw: Dict from gs/fetch.py.
        fetch_run_id: Fetch run ID for audit trail.

    Returns:
        Signal ID if written with non-FILTERED status (classified),
        the string sentinel "__FILTERED__" if written as irrelevance-filtered,
        or None if duplicate. Callers distinguish to keep dedupe and
        irrelevance-filter counts separate (Health GS-3 depends on this).
    """
    headline = raw.get("headline", "")
    summary = raw.get("summary", raw.get("raw_content", ""))
    url = raw.get("url", "")

    # Dedup check first
    if is_duplicate(url, headline):
        return None

    # ── RELEVANCE GATE ────────────────────────────────────────────────
    relevant, gate_confidence, gate_reason = is_infrastructure_relevant(
        headline, summary
    )

    if not relevant:
        # Write as FILTERED — preserved in DB but never scored or emailed
        signal = Signal(
            source_type    = SourceType.FETCH,
            status         = SignalStatus.FILTERED,
            fetch_run_id   = fetch_run_id,
            headline       = headline[:120],
            summary        = (summary or "")[:500],
            raw_content    = raw.get("raw_content", "")[:3000],
            url            = url,
            source_name    = raw.get("source_name", ""),
            publication_date = raw.get("publication_date", ""),
            alert_level    = "GREEN",
            weighted_score = 0.0,
            raw_score      = 0.0,
            confidence     = 0.0,
            filter_reason  = gate_reason,
            classifier_model = "relevance-gate-filtered",
        )
        write_signal(signal)
        print(f"  [FILTERED] {headline[:60]} -- {gate_reason}")
        return "__FILTERED__"

    # ── CLASSIFY ──────────────────────────────────────────────────────
    fields = classify_item(raw)

    # Apply LOW confidence flag for ambiguous signals
    if gate_confidence == "LOW":
        fields["confidence"] = min(fields.get("confidence", 0.60), 0.55)
        themes = json.loads(fields.get("theme_tags", "[]"))
        themes.append("REVIEW_FLAGGED")
        fields["theme_tags"] = json.dumps(themes)

    signal = Signal(
        source_type       = SourceType.FETCH,
        status            = fields["status"],
        fetch_run_id      = fetch_run_id,
        headline          = fields["headline"],
        summary           = fields["summary"],
        raw_content       = fields["raw_content"],
        url               = fields["url"],
        source_name       = fields["source_name"],
        publication_date  = fields["publication_date"],
        c_tags            = fields["c_tags"],
        f_tags            = fields["f_tags"],
        t_tag             = fields["t_tag"],
        o_tag             = fields["o_tag"],
        second_order      = fields["second_order"],
        classifier_model  = fields["classifier_model"],
        confidence        = fields["confidence"],
        alert_level       = fields["alert_level"],
        weighted_score    = fields["weighted_score"],
        raw_score         = fields["raw_score"],
        pipeline_risk_alert   = fields["pipeline_risk_alert"],
        affected_deals        = fields["affected_deals"],
        risk_alert_confidence = fields["risk_alert_confidence"],
        risk_alert_rationale  = fields["risk_alert_rationale"],
        opportunity_alert     = fields["opportunity_alert"],
        opportunity_sector    = fields["opportunity_sector"],
        opportunity_type      = fields["opportunity_type"],
        opportunity_urgency   = fields["opportunity_urgency"],
        opportunity_rationale = fields["opportunity_rationale"],
        linkedin_candidate    = fields["linkedin_candidate"],
        theme_tags            = fields["theme_tags"],
    )

    written = write_signal(signal)
    return written.signal_id


# ── BATCH CLASSIFIER ──────────────────────────────────────────────────────────

def classify_batch(raw_items: list, fetch_run_id: str = None):
    """
    Classify a list of raw article dicts and write all to database.

    Pure Python classification — no API calls, no subprocess, no paste-back.
    Runs inline as part of the orchestrator chain.

    Args:
        raw_items: List of raw article dicts from gs/fetch.py.
        fetch_run_id: Fetch run ID for audit trail.

    Returns:
        Tuple (signal_ids, stats) where:
          signal_ids  — list of classified signal IDs (excludes filtered/dupes)
          stats       — dict with keys: classified, filtered, dedupes, errors.
                        Filtered = written to DB with status=FILTERED by
                        irrelevance gate. Dedupes = url/headline duplicates,
                        never written. GS-3 uses the filtered/classified
                        split; raw_items - classified conflates them.
    """
    signal_ids = []
    dedupes = 0
    filtered = 0
    errors = 0

    red = amber = green = 0

    print(f"\nClassifying {len(raw_items)} items...")

    for i, raw in enumerate(raw_items, 1):
        try:
            sid = classify_and_store(raw, fetch_run_id=fetch_run_id)
            if sid is None:
                dedupes += 1
            elif sid == "__FILTERED__":
                filtered += 1
            else:
                signal_ids.append(sid)
                fields = classify_item(raw)
                al = fields.get("alert_level", "GREEN")
                if al == "RED":
                    red += 1
                elif al == "AMBER":
                    amber += 1
                else:
                    green += 1
        except Exception as e:
            errors += 1
            headline = raw.get("headline", "")[:40]
            print(f"  ERROR [{i}] {headline}: {e}")

    print(f"\nClassify complete: {len(signal_ids)} stored, "
          f"{dedupes} dupes, {filtered} filtered, {errors} errors")
    print(f"  RED: {red} | AMBER: {amber} | GREEN: {green}")
    return signal_ids, {
        "classified": len(signal_ids),
        "filtered":   filtered,
        "dedupes":    dedupes,
        "errors":     errors,
    }


def update_live_context(prices: dict = None):
    """Update live context — kept for orchestrator compatibility."""
    pass


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("GS CLASSIFY — PURE PYTHON TEST")
    print("=" * 55)

    # Test with sample articles
    test_items = [
        {
            "source_name": "FT Energy",
            "url": "https://ft.com/test-hormuz-oil",
            "headline": "Brent crude above $100 as Hormuz blockade enters sixth week",
            "summary": "Oil prices remained elevated with Brent trading above $100 "
                       "as the Iranian blockade of the Strait of Hormuz continued. "
                       "Steel and aluminum tariffs compounded construction cost "
                       "pressure across US infrastructure projects.",
            "c_tags": ["C05", "C08"],
            "publication_date": "2026-04-12",
        },
        {
            "source_name": "Utility Dive",
            "url": "https://utilitydive.com/test-ferc-rule",
            "headline": "FERC large load interconnection rule deadline April 30",
            "summary": "FERC's interconnection rule for large load customers including "
                       "data centers faces April 30 deadline. PJM queue position "
                       "assignments for Ohio projects depend on ruling.",
            "c_tags": ["C02", "C03"],
            "publication_date": "2026-04-12",
        },
        {
            "source_name": "Data Center Dynamics",
            "url": "https://dcd.com/test-hyperscaler",
            "headline": "Prologis 900MW Project Sail data center approved in Georgia",
            "summary": "Prologis received approval for its 900MW data center campus "
                       "in Coweta County, Georgia. The development will require "
                       "significant power procurement and grid interconnection.",
            "c_tags": ["C11", "C14"],
            "publication_date": "2026-04-12",
        },
    ]

    print("\nClassifying 3 test items...")
    for item in test_items:
        fields = classify_item(item)
        print(f"\n  {fields['headline'][:70]}")
        print(f"    C-tags: {fields['c_tags']}")
        print(f"    A-tags: {json.loads(fields['c_tags'])} -> derived")
        print(f"    Alert:  {fields['alert_level']} (score={fields['weighted_score']})")
        print(f"    T-tag:  {fields['t_tag']}, F-tag: {fields['f_tags']}")
        print(f"    Deals:  {fields['affected_deals']}")
        print(f"    Themes: {fields['theme_tags']}")
        print(f"    2nd:    {fields['second_order'][:100]}...")

    print("\ngs/classify.py operational.")