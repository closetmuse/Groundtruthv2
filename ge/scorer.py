# GE — GroundEngines Scorer
# PRD Section 4.2 — Signal Scoring
# Pure function — same inputs always produce same outputs.
# No memory, no state, no opinion about what Sri should do.
# Last Updated: April 2026

import json
from datetime import datetime, timedelta
from core.schema import Signal, AlertLevel, RegimeCode

# ─────────────────────────────────────────────────────────────────────────────
# SCORER DESIGN — conceptual decomposition
# ─────────────────────────────────────────────────────────────────────────────
# A signal's final alert level comes from two layers:
#
#   1. Raw score (0–55): how strong is the signal on its own?
#      Five components contribute, with weights summing to 0.55 by design.
#      The remaining 0.45 of the nominal 1.0 weight budget is reserved for
#      Layer 2 — multiplicative boosts deliver it when context warrants.
#
#   2. Boosts (0–40): how much does context amplify the raw signal?
#      Regime match (current macro regime relevance) and deal match
#      (named live-deal exposure) each add up to some cap, gated by
#      raw-score bands so weak signals don't get inflated.
#
#   weighted = raw + regime_boost + deal_boost (clipped 0–100)
#   alert   = RED/AMBER/GREEN by ALERT_THRESHOLDS on weighted
#
# Everything tunable lives in the config block below. To adjust behavior:
#   - bump RAW_COMPONENT_WEIGHTS to shift what counts as signal strength
#   - bump BOOST_BANDS to change how context amplifies
#   - bump ALERT_THRESHOLDS to reclassify the distribution
# Log every numeric change in TUNING_HISTORY and increment SCORER_VERSION.
# ─────────────────────────────────────────────────────────────────────────────

SCORER_VERSION = "2.3.0"

TUNING_HISTORY = [
    # (version, date, note)
    ("1.0.0", "2026-04-15", "Initial weights from PRD 4.2"),
    ("1.1.0", "2026-04-18", "Added C11=1.3, C13=1.2 to R0 regime map (Fix A)"),
    ("2.0.0", "2026-04-18",
     "Path A refactor: WEIGHTS split into RAW_COMPONENT_WEIGHTS + BOOST_BANDS, "
     "alert thresholds and geo-penalty extracted as named config; no math change "
     "vs 1.1.0 (verified by A/B simulation on 526-signal backlog, 0 changes)"),
    ("2.1.0", "2026-04-18",
     "Fix C: score_deal_relevance now reads signal.affected_deals from the "
     "classifier (44 real deals via Sheets) instead of 3-deal scaffold. "
     "Removes spurious deal_boost from scaffold c_tag overlap. "
     "Backlog distribution shift: AMBER 77->39, RED 1->0, GREEN 587->626 "
     "on 665-signal sample. The AMBER drop is correction of inflation — "
     "76/77 old AMBERs had empty affected_deals. Monitor for a week; if "
     "brief-relevant signals (e.g. market-wide FEOC or PPA stories without "
     "a specific deal name) are under-surfaced, lower ALERT_THRESHOLDS['AMBER'] "
     "(current 48) or extend classifier match_deals() with a sector-exposure "
     "Tier 2.5."),
    ("2.2.0", "2026-04-18",
     "Calibration pass driven by GREEN audit (infra/audit_green.py): "
     "(1) SOURCE_TYPE_CONFIDENCE['PRICE'] raised 0.80->0.95 — RTO DA measured "
     "data from authoritative feeds should not score below F2 FERC. Lifts "
     "curtailment signals (CAISO/ERCOT/NYISO/ISONE/MISO DA Market) from the "
     "GREEN cluster at ~40 up through the AMBER threshold when fresh. "
     "(2) ALERT_THRESHOLDS['AMBER'] 48->45 — recovers NEAR-AMBER F1/F2 signals "
     "the audit flagged as false negatives (Maine DC ban, Hormuz blockade, "
     "FERC trade-press echo, private-credit derivatives). "
     "Together targets ~20% AMBER rate vs 15% at v2.1.0, still selective."),
    ("2.3.0", "2026-04-19",
     "Structural-candidate scoring lane. Triggered by this week's classifier "
     "miss: a 7-print pre-issuance ILS → DC-finance thread decayed at GREEN×6 "
     "+ AMBER×1 across Artemis source (see alpha_ledger.md ALF-20260419-1). "
     "Three additions: "
     "(1) REGIME_RELEVANCE extended with C16 (Struct), C17 (Siting-State), "
     "C18 (RatingMethod) at R0=1.4/1.3/1.3; R2=1.5/1.2/1.5; R4=1.3/1.2/1.2. "
     "(2) New score_cluster_amplifier boost: when signal carries a structural "
     "C-tag and 2+ other signals in the batch share it, add +5/member cap +20. "
     "Catches pre-issuance ladders that no single print can elevate alone. "
     "(3) New score_structural_keyword_bonus: flat additive points for "
     "IG-uplift / rating-methodology / first-in-class / capital-pool language. "
     "Cap +15. Keeps raw-budget invariant (RAW_COMPONENT_WEIGHTS unchanged). "
     "Expected effect: this week's ILS cluster would land AMBER on the 3rd+ "
     "print instead of GREEN; Maine moratorium 3-print cluster lands AMBER on "
     "print 2. BP/Veolia-class noise unaffected (no structural tags)."),
]

# ── RAW SCORE COMPONENTS (sum to 0.55 by design — see design note above) ─────
RAW_COMPONENT_WEIGHTS = {
    "source_confidence":      0.25,  # F-tag / source-type derived reliability
    "recency":                0.15,  # Exponential decay — T1 decays faster
    "novelty":                0.05,  # First signal on topic scores higher
    "sri_desk_proximity":     0.05,  # ANECDOTAL bonus
    "encyclopedia_alignment": 0.05,  # Matches current encyclopedia pattern?
}
assert abs(sum(RAW_COMPONENT_WEIGHTS.values()) - 0.55) < 1e-9, (
    "RAW_COMPONENT_WEIGHTS must sum to 0.55 — the designed raw-score ceiling."
)

# ── BOOST BANDS ──────────────────────────────────────────────────────────────
# Data-driven replacement for the old 3-way if/elif block.
# Weak signals (raw < 30) get token regime boost and no deal boost, so noise
# can't cross alert thresholds just because a strong regime happens to match.
# Moderate signals (30 ≤ raw < 45) get half-strength boosts.
# Strong signals (raw ≥ 45) get full boosts.
# Each row: (min_raw, regime_scale, regime_cap, deal_scale, deal_cap)
BOOST_BANDS = [
    (45, 1.0, 25.0, 0.15, 15.0),   # Strong band — full boosts
    (30, 0.5, 12.0, 0.10,  8.0),   # Moderate band — halved
    ( 0, 0.2,  5.0, 0.00,  0.0),   # Weak band — token regime, no deal
]

# ── ALERT THRESHOLDS ─────────────────────────────────────────────────────────
# Weighted-score cutoffs for alert level assignment. GREEN is implicit below
# AMBER. Thresholds are calibrated for the current (0.55 raw + 40 boost cap)
# distribution. If you change RAW_COMPONENT_WEIGHTS or BOOST_BANDS, re-check
# the percentile distribution of weighted scores and reconsider these.
ALERT_THRESHOLDS = {
    "RED":   78,
    "AMBER": 45,   # v2.2.0: lowered 48→45 to capture NEAR-AMBER F1/F2 signals
                   # surfaced by the GREEN audit (Maine DC ban, Hormuz blockade,
                   # private-credit derivatives, FERC trade-press echo, etc.)
}

# ── STRUCTURAL-CANDIDATE LANE (v2.3.0) ───────────────────────────────────────
# Purpose: catch pre-issuance structural threads that any single print lacks
# the weight to elevate. Two mechanics, both in the BOOST budget so the raw
# 0.55 invariant stays intact.
#
# STRUCTURAL_C_TAGS — the tags whose cluster behaviour we watch. Matches the
# schema additions in gs/classify.py fix #2 (2026-04-19).
STRUCTURAL_C_TAGS = {"C16", "C17", "C18"}

# Cluster amplifier — incremental boost per additional cluster member.
# +5 points per sibling carrying the same structural tag, cap +20.
# A 7-signal ILS-like ladder lands the 5th+ member above +20 cap.
CLUSTER_BONUS_PER_MEMBER = 5.0
CLUSTER_BONUS_CAP         = 20.0

# Structural keyword bonus — flat additive points when specific phrases
# appear. These are the language markers for rating-threshold / capital-pool
# / regulatory-escalation content that the generic regime relevance doesn't
# capture. Kept as a config dict so adding a new marker is one-line surgery.
STRUCTURAL_KEYWORD_BONUSES = {
    # IG-uplift and rating-threshold language
    "ig uplift":                10,
    "investment grade uplift":  10,
    "rating uplift":             8,
    "investment grade":          5,
    "capital relief":            7,
    "risk transfer":             5,
    # Rating-methodology language
    "rating methodology":        7,
    "methodology note":          7,
    "rating action":             5,
    "rating agency":             4,
    # Structural-finance language
    "third-party capital":       6,
    "third party capital":       6,
    "insurance-linked":          5,
    "insurance linked":          5,
    "cat bond":                  4,
    "casualty sidecar":          5,
    # State-legislative / first-in-class language
    "first-in-class":            4,
    "first u.s. state":          5,
    "first us state":            5,
    "state-wide":                4,
    "bit barn ban":              5,
    "moratorium":                3,
}
STRUCTURAL_KEYWORD_CAP = 15.0


# ── PENALTIES ────────────────────────────────────────────────────────────────
# Subtractive corrections applied after boosts. Kept here so policy changes
# are visible at config level, not buried in score_signal().
GEO_NO_INFRA_PENALTY = {
    "amount": 15,
    "requires_c_tag": "C08",
    "trigger_terms": [
        "election", "vote", "ballot", "parliament",
        "concedes", "polling", "candidat",
    ],
    "bypass_terms": [
        "pipeline", "grid", "port", "energy", "lng",
        " power ", "transmission", "construction",
        "tariff", "supply chain", "commodity",
        "interest rate", "infrastructure",
    ],
}

# ── DRAFT STATUS FLOOR ───────────────────────────────────────────────────────
# Source confidence below this threshold auto-marks FETCH signals as DRAFT
# (won't surface in briefs until a higher-confidence corroboration arrives).
DRAFT_CONFIDENCE_FLOOR = 0.60

# ── F-TAG CONFIDENCE LOOKUP ───────────────────────────────────────────────────
# Maps F-tags to base confidence scores
# PRD Appendix A.4 — Full lookup table

F_TAG_CONFIDENCE = {
    # Primary institutional sources
    "F1":  0.90,  # FT, WSJ, Bloomberg, Reuters
    "F2":  0.88,  # FERC official filings
    "F3":  0.85,  # DOE, Treasury, White House
    "F4":  0.85,  # Moody's, S&P, rating agencies
    "F5":  0.83,  # IEA, EIA official reports
    # Specialized trade press
    "F6":  0.78,  # IJGlobal, PFI
    "F7":  0.75,  # Recharge News, PV Magazine
    "F8":  0.73,  # LNG Prime, DataCenter Dynamics
    "F9":  0.72,  # Bond Buyer, P3 Bulletin
    "F10": 0.70,  # Wood Mackenzie press, BNEF press
    # Market data
    "F11": 0.85,  # EIA API data
    "F12": 0.85,  # gridstatus RTO data
    "F13": 0.85,  # FRED macro data
    "F14": 0.80,  # metals-api LME data
    "F15": 0.78,  # Anza, PV Insights solar data
    # Secondary and aggregator
    "F16": 0.60,  # Industry aggregators
    "F17": 0.55,  # Company press releases
    "F18": 0.52,  # Analyst reports secondary
    "F19": 0.50,  # Trade association statements
    "F20": 0.45,  # General news aggregators
}

# Source type base confidence per PRD Section 3.1.
# PRICE raised to 0.95 in v2.2.0 — RTO DA market data is measured from
# authoritative feeds (CAISO/ERCOT/NYISO/ISONE/MISO APIs), not interpreted
# reporting. Should score at least as high as FERC primary filings (F2=0.88).
# Previous 0.80 caused curtailment signals to cluster at weighted ~40 GREEN
# even with real regime boosts — see GREEN audit 2026-04-18.
SOURCE_TYPE_CONFIDENCE = {
    "FETCH":      None,   # Derived from F-tags
    "PRICE":      0.95,   # Measured RTO / market-data feeds
    "ANECDOTAL":  0.75,   # Direct observation
}

# ── REGIME RELEVANCE MULTIPLIERS ──────────────────────────────────────────────
# PRD Section 4.3 — regime affects weighting
# Stress regimes amplify stress signals
# Maps (regime, c_tag) → relevance multiplier

REGIME_RELEVANCE = {
    # R0 Compound — current Hormuz regime
    # All stress signals amplified. Hormuz transmits to DC via the power-cost
    # channel (LNG feedgas → US gas prices → DC offtaker economics), so C11
    # digital infra + C13 land/capex are demand-side participants in the same
    # regime threat chain, not unrelated sectors.
    # v2.3.0: C16/C17/C18 added as structural-candidate amplifiers. In R0 a
    # structural-finance innovation (C16) is high-relevance because credit-
    # stress + capital-markets innovation is the E01-GFC-shape response; state
    # siting escalation (C17) compounds with regulatory uncertainty; rating
    # methodology (C18) is the transmission channel through which structural
    # finance reaches IG-threshold pricing.
    "R0": {
        "C08": 1.5,   # Geopolitical — core driver
        "C05": 1.5,   # Oil and gas — core driver
        "C16": 1.4,   # Structured finance / ILS — structural innovation lane
        "C09": 1.4,   # Construction commodities
        "C11": 1.3,   # Digital infra — DC demand-side of Hormuz power stress
        "C02": 1.3,   # Credit markets — BDC gates
        "C17": 1.3,   # Siting-state — live regulatory escalation
        "C18": 1.3,   # Rating methodology — IG-threshold transmission
        "C01": 1.3,   # Macro — Fed constrained
        "C12": 1.3,   # Financing markets
        "C13": 1.2,   # Land / capex commitment
        "C04": 1.2,   # Policy — OBBBA
        "C06": 1.2,   # Solar — OBBBA affected
        "C07": 1.2,   # Wind — OBBBA affected
        "C14": 1.1,   # Sponsor/developer activity
        "DEFAULT": 1.0,
    },
    # R1 Stagflationary
    "R1": {
        "C08": 1.5, "C09": 1.5, "C01": 1.3,
        "C02": 1.2, "C12": 1.2,
        "C16": 1.2, "C18": 1.2,
        "DEFAULT": 0.9,
    },
    # R2 Credit stress — structural finance and rating-methodology events
    # are MOST relevant here; they are directly in the stress transmission.
    "R2": {
        "C02": 1.5, "C12": 1.5, "C14": 1.3,
        "C16": 1.5,   # structural finance is the stress response
        "C18": 1.5,   # rating-methodology directly paired
        "C17": 1.2,   # regulatory tailwind or headwind both matter
        "C01": 1.2, "DEFAULT": 0.9,
    },
    # R3 Commodity shock
    "R3": {
        "C08": 1.5, "C05": 1.5, "C09": 1.4,
        "C14": 1.2,
        "C16": 1.1, "C18": 1.1,
        "DEFAULT": 0.9,
    },
    # R4 Policy tailwind — structured innovation and rating evolution often
    # parallel policy in this regime.
    "R4": {
        "C04": 1.5, "C06": 1.3, "C07": 1.3,
        "C10": 1.2, "C11": 1.2,
        "C16": 1.3, "C17": 1.2, "C18": 1.2,
        "DEFAULT": 1.0,
    },
    # R1 Normal operations
    "R1_NORMAL": {
        "DEFAULT": 1.0,
    },
}

# ── PIPELINE DEAL MATCHING — architectural note ──────────────────────────────
# Deal matching is owned by the classifier (gs/classify.py:match_deals), not
# the scorer. The classifier loads the 44 live deals from the Google Sheet
# via sheets/pipeline.py, runs a 3-tier matching hierarchy:
#   Tier 1 — deal name keyword in signal text  → written to affected_deals
#   Tier 2 — A-tag + geography (state/ISO)     → written to affected_deals
#   Tier 3 — sector-general overlap            → excluded (too noisy)
# Only Tier 1 and Tier 2 matches reach the scorer via signal.affected_deals.
# score_deal_relevance() simply trusts that field — no separate scaffold.
#
# Prior to 2026-04-18 (v2.1.0), this file had a hardcoded 3-deal scaffold
# that never updated; deal_relevance was effectively zero for the real 44
# deals in the Sheet (see GE-2 Deal Match Rate 2% health alert). The fix
# was to read signal.affected_deals instead.

# ── SCORING FUNCTIONS ─────────────────────────────────────────────────────────

def score_source_confidence(signal: Signal) -> float:
    """
    Derive confidence from F-tags or source type.
    Returns 0.0-1.0.
    """
    if signal.source_type in ("PRICE", "ANECDOTAL"):
        return SOURCE_TYPE_CONFIDENCE[signal.source_type]

    # FETCH — derive from F-tags
    f_tags = []
    try:
        f_tags = json.loads(signal.f_tags or "[]")
    except Exception:
        pass

    if not f_tags:
        return 0.50  # Unknown source — conservative default

    scores = [F_TAG_CONFIDENCE.get(tag, 0.50) for tag in f_tags]
    return round(max(scores), 3)  # Use highest F-tag confidence


def score_recency(signal: Signal) -> float:
    """
    Exponential decay based on signal age and T-tag.
    T1 signals decay faster — immediate value degrades quickly.
    Returns 0.0-1.0.
    """
    try:
        created = datetime.fromisoformat(signal.created_at)
    except Exception:
        return 0.50

    age_hours = (datetime.utcnow() - created).total_seconds() / 3600

    # Decay rates by T-tag
    decay_rates = {
        "T1": 0.05,   # Half-life ~14 hours
        "T2": 0.02,   # Half-life ~35 hours
        "T3": 0.008,  # Half-life ~87 hours
    }
    rate = decay_rates.get(signal.t_tag, 0.02)
    score = max(0.0, 1.0 - (rate * age_hours))
    return round(score, 3)


def score_regime_relevance(signal: Signal,
                           current_regime: str = "R0") -> float:
    """
    Does this signal align with the current regime?
    Returns 0.0-1.5 multiplier applied to base score.
    """
    c_tags = []
    try:
        c_tags = json.loads(signal.c_tags or "[]")
    except Exception:
        pass

    regime_map = REGIME_RELEVANCE.get(current_regime, {})
    default    = regime_map.get("DEFAULT", 1.0)

    if not c_tags:
        return default

    # Use highest relevance across all c_tags
    multipliers = [regime_map.get(tag, default) for tag in c_tags]
    return round(max(multipliers), 3)


def score_deal_relevance(signal: Signal) -> float:
    """
    Score deal relevance from classifier-assigned affected_deals.
    Returns 0.0-2.0 — used as a weight factor in scoring formula.

    The classifier (gs/classify.py:match_deals) runs a 3-tier matching
    hierarchy against the 44 live deals loaded from the Google Sheet,
    and writes Tier 1 (deal-specific) and Tier 2 (asset+geo) matches
    to signal.affected_deals. Scorer simply reads that field.

    Scaling:
      0 matches → 0.0 (no relevance)
      1 match   → 1.0 (single named-deal hit)
      2 matches → 1.5
      3+ matches → 2.0 (cap — broad pipeline exposure)

    Architectural rule: scorer never writes affected_deals, only reads it.
    """
    try:
        affected = json.loads(signal.affected_deals or "[]")
    except Exception:
        affected = []

    if not affected:
        return 0.0

    return round(min(2.0, 0.5 + 0.5 * len(affected)), 3)


def score_novelty(signal: Signal,
                  recent_signals: list[Signal]) -> float:
    """
    Inverse of corroboration count.
    First signal on a topic scores 1.0.
    Fifth signal on same topic scores 0.2.
    """
    c_tags = set()
    try:
        c_tags = set(json.loads(signal.c_tags or "[]"))
    except Exception:
        pass

    if not c_tags or not recent_signals:
        return 1.0

    overlap_count = 0
    for s in recent_signals:
        if s.signal_id == signal.signal_id:
            continue
        try:
            other_tags = set(json.loads(s.c_tags or "[]"))
        except Exception:
            continue
        if c_tags & other_tags:
            overlap_count += 1

    score = max(0.1, 1.0 - (overlap_count * 0.15))
    return round(score, 3)


def score_sri_desk_proximity(signal: Signal) -> float:
    """
    ANECDOTAL signals receive bonus — field-confirmed observations.
    """
    if signal.source_type == "ANECDOTAL":
        return 1.5
    return 1.0


def score_encyclopedia_alignment(signal: Signal,
                                 current_regime: str = "R0") -> float:
    """
    Does signal match the current encyclopedia pattern?
    Simplified version — full stumpy matching in Phase 2 GI.
    Uses C-tag overlap with known regime fingerprints.
    """
    c_tags = set()
    try:
        c_tags = set(json.loads(signal.c_tags or "[]"))
    except Exception:
        pass

    # E07 Hormuz fingerprint tags
    hormuz_tags = {"C03", "C08", "C02", "C09", "C04", "C05"}
    # E01 GFC fingerprint tags — includes C11 (digital infra), so DC
    # hyperscaler signals get encyclopedia_alignment via GFC overlap.
    gfc_tags    = {"C02", "C06", "C07", "C12", "C11"}
    # E03 Ukraine fingerprint tags
    ukraine_tags = {"C03", "C08", "C09", "C05", "C12"}

    best_match = 0.0
    for fingerprint in [hormuz_tags, ukraine_tags, gfc_tags]:
        overlap = len(c_tags & fingerprint)
        if overlap > 0:
            match = min(1.5, 0.5 + (overlap * 0.25))
            best_match = max(best_match, match)

    return round(best_match, 3)

# ── STRUCTURAL-CANDIDATE SCORING (v2.3.0) ────────────────────────────────────

def score_cluster_amplifier(signal: Signal,
                            recent_signals: list) -> float:
    """
    Cluster-detection boost for structural threads.

    If this signal carries a structural C-tag (C16/C17/C18) AND other signals
    in the batch share any of its structural tags, add a per-member bonus.
    Pre-issuance structural ladders (e.g. the 7-print ILS → DC-finance thread
    Apr 13-18, 2026 — see alpha_ledger.md ALF-20260419-1) cannot elevate any
    single print above GREEN but collectively constitute a structural
    inflection. This function lets the cluster be recognized as the signal.

    Returns a flat boost in score points, 0.0 to CLUSTER_BONUS_CAP.
    """
    try:
        sig_tags = set(json.loads(signal.c_tags or "[]"))
    except Exception:
        return 0.0
    sig_struct = sig_tags & STRUCTURAL_C_TAGS
    if not sig_struct:
        return 0.0

    cluster_count = 0
    for other in recent_signals:
        if other.signal_id == signal.signal_id:
            continue
        try:
            other_tags = set(json.loads(other.c_tags or "[]"))
        except Exception:
            continue
        if other_tags & sig_struct:
            cluster_count += 1

    if cluster_count == 0:
        return 0.0
    return min(CLUSTER_BONUS_CAP, cluster_count * CLUSTER_BONUS_PER_MEMBER)


def score_structural_keyword_bonus(signal: Signal) -> float:
    """
    Flat additive bonus for structural-finance / rating-threshold / siting
    language. These phrases are the precise markers the classifier's generic
    regime relevance cannot catch — they indicate rating-threshold mechanics
    (IG uplift, rating methodology) or capital-stack innovation (third-party
    capital, insurance-linked, casualty sidecar) or state-level siting
    escalation (first-in-class, state-wide moratorium).

    Returns a flat boost in score points, 0.0 to STRUCTURAL_KEYWORD_CAP.
    """
    text = ((signal.headline or "") + " " + (signal.summary or "")).lower()
    total = 0.0
    for phrase, pts in STRUCTURAL_KEYWORD_BONUSES.items():
        if phrase in text:
            total += pts
    return min(STRUCTURAL_KEYWORD_CAP, total)


# ── BOOST / PENALTY / ALERT HELPERS ──────────────────────────────────────────

def _compute_boosts(raw: float, rr: float, dr: float) -> tuple[float, float]:
    """Look up the active BOOST_BANDS row for this raw score and return
    (regime_boost, deal_boost). Data-driven — edit BOOST_BANDS to tune."""
    for min_raw, regime_scale, regime_cap, deal_scale, deal_cap in BOOST_BANDS:
        if raw >= min_raw:
            regime_boost = (
                min(raw * (rr - 1.0) * regime_scale, regime_cap)
                if rr > 1.0 else 0.0
            )
            deal_boost = (
                min(raw * dr * deal_scale, deal_cap)
                if dr > 0 and deal_scale > 0 else 0.0
            )
            return regime_boost, deal_boost
    return 0.0, 0.0


def _apply_geo_penalty(weighted: float, c_tags: list,
                       headline: str, summary: str) -> float:
    """Subtract GEO_NO_INFRA_PENALTY['amount'] when a C08 signal mentions
    election terms without any infrastructure nexus."""
    policy = GEO_NO_INFRA_PENALTY
    if policy["requires_c_tag"] not in c_tags:
        return weighted
    text = ((headline or "") + " " + (summary or "")).lower()
    has_trigger = any(t in text for t in policy["trigger_terms"])
    has_bypass  = any(t in text for t in policy["bypass_terms"])
    if has_trigger and not has_bypass:
        return weighted - policy["amount"]
    return weighted


def _classify_alert(weighted: float) -> AlertLevel:
    if weighted >= ALERT_THRESHOLDS["RED"]:
        return AlertLevel.RED
    if weighted >= ALERT_THRESHOLDS["AMBER"]:
        return AlertLevel.AMBER
    return AlertLevel.GREEN


# ── MASTER SCORER ─────────────────────────────────────────────────────────────

def score_signal(signal: Signal,
                 current_regime: str = "R0",
                 recent_signals: list = None) -> Signal:
    """
    Master scoring function.

    Decomposition (see design note at top of file):
      raw      = weighted sum of 5 raw components, ceiling ~55
      weighted = raw + regime_boost + deal_boost - penalties, clipped 0–100
      alert    = RED/AMBER/GREEN by ALERT_THRESHOLDS on weighted
    """
    if recent_signals is None:
        recent_signals = []

    # Component scores
    sc  = score_source_confidence(signal)
    rec = score_recency(signal)
    rr  = score_regime_relevance(signal, current_regime)
    dr  = score_deal_relevance(signal)
    nov = score_novelty(signal, recent_signals)
    sdp = score_sri_desk_proximity(signal)
    ea  = score_encyclopedia_alignment(signal, current_regime)

    # Raw score — 5-component weighted sum scaled to 0–100 scale.
    # Ceiling is ~55 because RAW_COMPONENT_WEIGHTS sum to 0.55 by design.
    raw = (
        sc  * RAW_COMPONENT_WEIGHTS["source_confidence"]      +
        rec * RAW_COMPONENT_WEIGHTS["recency"]                +
        nov * RAW_COMPONENT_WEIGHTS["novelty"]                +
        sdp * RAW_COMPONENT_WEIGHTS["sri_desk_proximity"]     +
        ea  * RAW_COMPONENT_WEIGHTS["encyclopedia_alignment"]
    ) * 100

    # Contextual boosts delivered from the 0.45 weight budget reserved outside
    # the raw sum. Bands prevent weak signals from amplifying on regime match.
    regime_boost, deal_boost = _compute_boosts(raw, rr, dr)

    # v2.3.0 structural-candidate lane:
    #   cluster_boost    — amplifies pre-issuance structural threads by
    #                      counting siblings that share a structural C-tag
    #   structural_kw    — flat additive for IG-uplift / rating-methodology /
    #                      first-in-class / capital-pool language
    # Both bypass the raw-band gating because the ILS-class miss was
    # precisely the case where no single print crosses min_raw=30 — gating
    # these behind the same bands would reproduce the bug we're fixing.
    cluster_boost = score_cluster_amplifier(signal, recent_signals)
    structural_kw = score_structural_keyword_bonus(signal)

    weighted = raw + regime_boost + deal_boost + cluster_boost + structural_kw

    # Penalty — C08 geopolitical-without-infra-nexus
    c_tags = []
    try:
        c_tags = json.loads(signal.c_tags or "[]")
    except Exception:
        pass
    weighted = _apply_geo_penalty(weighted, c_tags, signal.headline, signal.summary)

    weighted = min(100.0, max(0.0, weighted))
    alert    = _classify_alert(weighted)

    # DRAFT gate — unreliable sources stay out of briefs until corroborated
    if sc < DRAFT_CONFIDENCE_FLOOR and signal.source_type == "FETCH":
        signal.status = "DRAFT"
    elif signal.status == "DRAFT" and sc >= DRAFT_CONFIDENCE_FLOOR:
        signal.status = "ACTIVE"

    # Write scores back to signal
    signal.raw_score       = round(raw, 2)
    signal.weighted_score  = round(weighted, 2)
    signal.alert_level     = alert
    signal.scored_at       = datetime.utcnow().isoformat()
    signal.regime_at_score = current_regime
    signal.confidence      = sc

    # Fire pipeline alert if RED and deal matched
    if alert == AlertLevel.RED and signal.affected_deals:
        signal.pipeline_risk_alert = 1

    return signal


def score_batch(signals: list[Signal],
                current_regime: str = "R0") -> list[Signal]:
    """
    Score a list of signals with shared recent context.
    PRD Section 3.5 Step 4 — batch all new items, single pass.
    """
    scored = []
    for signal in signals:
        scored_signal = score_signal(
            signal,
            current_regime = current_regime,
            recent_signals = signals,
        )
        scored.append(scored_signal)

    red   = sum(1 for s in scored if s.alert_level == AlertLevel.RED)
    amber = sum(1 for s in scored if s.alert_level == AlertLevel.AMBER)
    green = sum(1 for s in scored if s.alert_level == AlertLevel.GREEN)

    print(f"Batch scored: {len(scored)} signals — "
          f"RED {red} | AMBER {amber} | GREEN {green}")
    return scored


# ── CALIBRATION HELPERS ───────────────────────────────────────────────────────
# Use these when tuning RAW_COMPONENT_WEIGHTS / BOOST_BANDS / ALERT_THRESHOLDS.
# Workflow:
#   1. Edit the config values at the top of this file.
#   2. Bump SCORER_VERSION and add a TUNING_HISTORY entry.
#   3. Run `python ge/scorer.py --calibrate` to see the distribution impact
#      against the last N days of signals in the DB.
#   4. Commit and let Monday's first run validate against fresh tape.

def rescore_sample_from_db(days_back: int = 7, regime: str = "R0") -> dict:
    """Re-score every stored signal from the last N days under the current
    config and return distribution counts. Side-effect free — does not write."""
    import sqlite3
    from collections import Counter
    from datetime import date, timedelta

    cutoff = (date.today() - timedelta(days=days_back)).isoformat()
    conn = sqlite3.connect(
        r"C:\Users\nagar_7kszmu8\GroundTruth_v2\groundtruth.db"
    )
    c = conn.cursor()
    c.execute("""SELECT signal_id, source_type, status, headline, summary,
                        source_name, c_tags, f_tags, t_tag, created_at,
                        weighted_score, alert_level
                 FROM gs_signals WHERE created_at >= ?""", (cutoff,))
    rows = c.fetchall()
    batch = [Signal(signal_id=r[0], source_type=r[1], status=r[2],
                    headline=r[3], summary=r[4], source_name=r[5],
                    c_tags=r[6] or "[]", f_tags=r[7] or "[]",
                    t_tag=r[8] or "T2", created_at=r[9])
             for r in rows]
    current = Counter(r[11] or "UNSCORED" for r in rows)
    fresh = Counter()
    shifts = []
    for row, sig in zip(rows, batch):
        s2 = score_signal(sig, regime, batch)
        new_al = s2.alert_level.value if hasattr(s2.alert_level, "value") \
                 else str(s2.alert_level).replace("AlertLevel.", "")
        fresh[new_al] += 1
        old_al = row[11] or "UNSCORED"
        if old_al != new_al and old_al != "UNSCORED":
            shifts.append((row[0], old_al, new_al, row[10] or 0,
                          s2.weighted_score, row[3][:60]))
    return {
        "days_back": days_back,
        "total": len(rows),
        "current_in_db": dict(current),
        "fresh_rescored": dict(fresh),
        "shifts": shifts,
    }


# ── TEST / CALIBRATION ENTRY POINT ────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if "--calibrate" in sys.argv:
        # Calibration mode — rescore DB against current config and report
        days = 7
        if "--days" in sys.argv:
            days = int(sys.argv[sys.argv.index("--days") + 1])
        print(f"Calibration run: SCORER_VERSION={SCORER_VERSION}")
        print(f"Config in effect:")
        print(f"  RAW_COMPONENT_WEIGHTS sum = "
              f"{sum(RAW_COMPONENT_WEIGHTS.values()):.3f}")
        print(f"  ALERT_THRESHOLDS         = {ALERT_THRESHOLDS}")
        print(f"  BOOST_BANDS rows         = {len(BOOST_BANDS)}")
        print()
        r = rescore_sample_from_db(days_back=days)
        print(f"Backlog scan: {r['total']} signals from last {r['days_back']} days")
        print(f"  Currently stored: {r['current_in_db']}")
        print(f"  Would re-score as: {r['fresh_rescored']}")
        print(f"  Signals that would shift alert level: {len(r['shifts'])}")
        for sid, old, new, ow, nw, hd in r["shifts"][:20]:
            print(f"    [{old}->{new}]  {sid}  {ow:.1f}->{nw:.1f}  {hd}")
        sys.exit(0)

    # Default — smoke tests
    print(f"Testing ge/scorer.py (version {SCORER_VERSION})...")

    # Test 1 — ANECDOTAL signal (aluminum latency event — GS-107 equivalent)
    s1 = Signal(
        signal_id   = "TEST-001",
        source_type = "ANECDOTAL",
        status      = "ACTIVE",
        headline    = "Desk observation — LME aluminum entering active deal conversation",
        summary     = "Aluminum cost inflation now in active discussion at deal team level.",
        source_name = "Sri desk observation",
        c_tags      = '["C09","C08"]',
        f_tags      = '[]',
        t_tag       = "T1",
        created_at  = datetime.utcnow().isoformat(),
    )

    # Test 2 — FETCH signal touching Project Vega (solar + OBBBA)
    s2 = Signal(
        signal_id   = "TEST-002",
        source_type = "FETCH",
        status      = "ACTIVE",
        headline    = "OBBBA solar ITC/PTC elimination advancing in reconciliation",
        summary     = "Congressional sources confirm solar tax credit elimination language.",
        source_name = "Reuters Energy",
        c_tags      = '["C04","C06"]',
        f_tags      = '["F1"]',
        t_tag       = "T1",
        created_at  = datetime.utcnow().isoformat(),
    )

    # Test 3 — Geopolitical Hormuz signal
    s3 = Signal(
        signal_id   = "TEST-003",
        source_type = "FETCH",
        status      = "ACTIVE",
        headline    = "Brent crude above $100 for 40th consecutive day",
        summary     = "Hormuz disruption sustaining oil price elevation.",
        source_name = "Financial Times",
        c_tags      = '["C08","C05"]',
        f_tags      = '["F1"]',
        t_tag       = "T2",
        created_at  = datetime.utcnow().isoformat(),
    )

    signals = [s1, s2, s3]
    scored  = score_batch(signals, current_regime="R0")

    print("\nScoring results:")
    for s in scored:
        print(f"  {s.signal_id}: raw={s.raw_score} "
              f"weighted={s.weighted_score} "
              f"alert={s.alert_level} "
              f"confidence={s.confidence} "
              f"deals={s.affected_deals}")

    print(f"\nge/scorer.py operational (v{SCORER_VERSION}).")
    print("Run `python ge/scorer.py --calibrate [--days N]` to see how current "
          "config would classify the last N days of stored signals.")