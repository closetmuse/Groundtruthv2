# GroundTruth V2 — Core Schema
# PRD Section 3.2 — Signal, Price, Deal data models
# Single source of truth for all data structures.
# All agents import from here. Never define schema elsewhere.
# Last Updated: April 2026

from datetime import datetime, date
from typing import Optional, List
from sqlmodel import SQLModel, Field, JSON, Column
import sqlalchemy as sa

# ── ENUMS ─────────────────────────────────────────────────────────────────────

class SourceType:
    FETCH      = "FETCH"       # Automated fetch from P1 sources
    PRICE      = "PRICE"       # Price threshold breach
    ANECDOTAL  = "ANECDOTAL"   # Sri desk observation

class SignalStatus:
    DRAFT      = "DRAFT"       # Confidence < 0.60 or awaiting Sri review
    ACTIVE     = "ACTIVE"      # Confidence >= 0.60, in play
    ARCHIVED   = "ARCHIVED"    # Duplicate or superseded
    SUPERSEDED = "SUPERSEDED"  # Replaced by newer signal on same event
    FILTERED   = "FILTERED"    # Failed infrastructure relevance gate

class AlertLevel:
    RED        = "RED"         # Score 75-100 — immediate, named deal
    AMBER      = "AMBER"       # Score 45-74 — monitor
    GREEN      = "GREEN"       # Score 0-44  — FYI, not surfaced in email

class RegimeCode:
    R0         = "R0"          # Compound stress — multiple vectors
    R1         = "R1"          # Stagflationary stress
    R2         = "R2"          # Credit stress
    R3         = "R3"          # Commodity shock
    R4         = "R4"          # Policy tailwind

# ── SIGNAL TABLE ──────────────────────────────────────────────────────────────

class Signal(SQLModel, table=True):
    __tablename__ = "gs_signals"

    # Identity
    id               : Optional[int] = Field(default=None, primary_key=True)
    signal_id        : str            = Field(index=True)   # GS-001 format
    legacy_id        : Optional[str]  = Field(default=None) # GT-XXX from V1
    created_at       : str            = Field(
                           default_factory=lambda: datetime.utcnow().isoformat()
                       )
    source_type      : str            = Field(default=SourceType.FETCH)
    status           : str            = Field(default=SignalStatus.DRAFT)
    fetch_run_id     : Optional[str]  = Field(default=None)

    # Content
    headline         : str            = Field()             # Max 120 chars
    summary          : str            = Field()             # 3-5 sentences, factual
    raw_content      : Optional[str]  = Field(default=None) # Source text max 3000 chars
    url              : Optional[str]  = Field(default=None)
    source_name      : str            = Field()
    publication_date : Optional[str]  = Field(default=None)

    # Classification
    c_tags           : Optional[str]  = Field(default=None) # JSON array e.g. ["C08","C03"]
    f_tags           : Optional[str]  = Field(default=None) # JSON array e.g. ["F1","F6"]
    t_tag            : Optional[str]  = Field(default=None) # T1 | T2 | T3
    o_tag            : Optional[str]  = Field(default=None) # O1-O5
    second_order     : Optional[str]  = Field(default=None) # Mechanism chain — most important field
    classifier_model : Optional[str]  = Field(default=None) # Claude version for audit

    # Price anchor — snapshot at moment of signal creation
    anchor_commodity    : Optional[str]   = Field(default=None) # e.g. WTI, LME_ALUMINUM
    anchor_value        : Optional[float] = Field(default=None) # Price at creation
    anchor_unit         : Optional[str]   = Field(default=None) # $/bbl, $/t, %
    anchor_delta_7d     : Optional[float] = Field(default=None) # % or abs change 7d
    anchor_delta_30d    : Optional[float] = Field(default=None) # % or abs change 30d
    anchor_delta_90d    : Optional[float] = Field(default=None) # % or abs change 90d
    anchor_source       : Optional[str]   = Field(default=None) # FRED, gridstatus
    anchor_fetched_at   : Optional[str]   = Field(default=None) # UTC ISO

    # Confidence and scoring
    confidence          : Optional[float] = Field(default=None) # 0.0-1.0
    is_verified         : int             = Field(default=0)     # 1 = Sri confirmed
    verification_note   : Optional[str]   = Field(default=None)
    corroboration_count : int             = Field(default=0)
    related_signal_ids  : Optional[str]   = Field(default=None) # JSON array of GS IDs

    # Relationships
    superseded_by          : Optional[str] = Field(default=None) # GS ID
    linked_binary_events   : Optional[str] = Field(default=None) # JSON array of event IDs
    binary_event_outcome   : Optional[str] = Field(default=None) # Logged when event resolves

    # GE scoring output
    raw_score        : Optional[float] = Field(default=None) # 0-100 pre-weighting
    weighted_score   : Optional[float] = Field(default=None) # 0-100 post-weighting
    alert_level      : Optional[str]   = Field(default=None) # RED|AMBER|GREEN
    scored_at        : Optional[str]   = Field(default=None) # UTC ISO
    regime_at_score  : Optional[str]   = Field(default=None) # R0-R4 at time of scoring

    # Pipeline
    pipeline_risk_alert    : int            = Field(default=0)    # 1 = fires pipeline alert
    affected_deals         : Optional[str]  = Field(default=None) # JSON array of deal nicknames
    risk_alert_confidence  : Optional[str]  = Field(default=None) # HIGH|MEDIUM|LOW
    risk_alert_rationale   : Optional[str]  = Field(default=None)
    opportunity_alert      : int            = Field(default=0)
    opportunity_sector     : Optional[str]  = Field(default=None)
    opportunity_type       : Optional[str]  = Field(default=None) # O1-O5
    opportunity_urgency    : Optional[str]  = Field(default=None) # T1|T2|T3
    opportunity_rationale  : Optional[str]  = Field(default=None)

    # Output
    linkedin_candidate : int           = Field(default=0)
    theme_tags         : Optional[str] = Field(default=None) # JSON array

    # Relevance filter
    filter_reason      : Optional[str] = Field(default=None) # Why signal was FILTERED

# ── PRICE SNAPSHOT TABLE ──────────────────────────────────────────────────────

class PriceSnapshot(SQLModel, table=True):
    __tablename__ = "gs_price_snapshots"

    id            : Optional[int] = Field(default=None, primary_key=True)
    snapshot_date : str           = Field(index=True)
    fetched_at    : str           = Field()
    series_data   : str           = Field()  # JSON — all series values
    deltas_7d     : Optional[str] = Field(default=None)  # JSON
    deltas_30d    : Optional[str] = Field(default=None)  # JSON
    deltas_90d    : Optional[str] = Field(default=None)  # JSON
    breaches      : Optional[str] = Field(default=None)  # JSON array
    partial       : int           = Field(default=0)     # 1 = some series failed

# ── BINARY EVENT TABLE ────────────────────────────────────────────────────────

class BinaryEvent(SQLModel, table=True):
    __tablename__ = "gt_binary_events"

    id              : Optional[int] = Field(default=None, primary_key=True)
    event_id        : str           = Field(index=True)  # e.g. FOMC_APR28
    name            : str           = Field()
    deadline        : str           = Field()            # ISO date
    linked_signals  : Optional[str] = Field(default=None) # JSON array GS IDs
    linked_deals    : Optional[str] = Field(default=None) # JSON array deal nicknames
    status          : str           = Field(default="OPEN") # OPEN|RESOLVED
    outcome         : Optional[str] = Field(default=None)
    outcome_date    : Optional[str] = Field(default=None)
    resolved_by     : Optional[str] = Field(default=None) # Who logged it
    encyclopedia_trigger : Optional[str] = Field(default=None) # E01-E08 if fires

# ── FETCH RUN TABLE ───────────────────────────────────────────────────────────

class FetchRun(SQLModel, table=True):
    __tablename__ = "gs_fetch_runs"

    id             : Optional[int] = Field(default=None, primary_key=True)
    run_id         : str           = Field(index=True)
    run_type       : str           = Field()  # CONTENT | PRICE | SCORING
    started_at     : str           = Field()
    completed_at   : Optional[str] = Field(default=None)
    signals_created: int           = Field(default=0)
    signals_draft  : int           = Field(default=0)
    signals_active : int           = Field(default=0)
    red_count      : int           = Field(default=0)
    amber_count    : int           = Field(default=0)
    regime_code    : Optional[str] = Field(default=None)
    failures       : Optional[str] = Field(default=None) # JSON array
    status         : str           = Field(default="RUNNING") # RUNNING|COMPLETE|PARTIAL|FAILED

# ── VERIFICATION LATENCY TABLE ────────────────────────────────────────────────

class LatencyEvent(SQLModel, table=True):
    __tablename__ = "ge_latency_events"

    id               : Optional[int] = Field(default=None, primary_key=True)
    signal_id        : str           = Field(index=True) # ANECDOTAL signal that confirmed
    commodity        : str           = Field()
    observation_date : str           = Field()  # When Sri logged desk observation
    price_move_start : str           = Field()  # When GS price data shows move began
    latency_days     : int           = Field()  # observation_date minus price_move_start
    latency_note     : Optional[str] = Field(default=None)
    encyclopedia_ref : Optional[str] = Field(default=None) # E01-E08 closest match

# ── RESOLUTION PROPOSAL TABLE ─────────────────────────────────────────────────

class ResolutionProposal(SQLModel, table=True):
    __tablename__ = "gt_resolution_proposals"

    id               : Optional[int] = Field(default=None, primary_key=True)
    event_id         : str           = Field(index=True)   # BE-001 etc
    signal_id        : str           = Field()             # GS-XXX that matched
    match_score      : float         = Field()             # 0.0-1.0
    proposed_outcome : str           = Field()             # Extracted from signal
    proposed_hit     : str           = Field(default="TBD") # Y|N|TBD
    status           : str           = Field(default="PENDING") # PENDING|ACCEPTED|REJECTED
    reject_reason    : Optional[str] = Field(default=None)
    created_at       : str           = Field(
                           default_factory=lambda: datetime.utcnow().isoformat()
                       )

# ── DATABASE INIT ─────────────────────────────────────────────────────────────

def init_database(db_path: str):
    from sqlmodel import create_engine
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    SQLModel.metadata.create_all(engine)
    print(f"Database initialised: {db_path}")
    print("Tables created:")
    for table in SQLModel.metadata.tables:
        print(f"  {table}")
    return engine

def get_engine(db_path: str):
    from sqlmodel import create_engine
    return create_engine(f"sqlite:///{db_path}", echo=False)

# ── HELPER: NEXT SIGNAL ID ────────────────────────────────────────────────────

def get_next_signal_id(engine) -> str:
    from sqlmodel import Session, select
    with Session(engine) as session:
        signals = session.exec(
            select(Signal).order_by(Signal.id.desc()).limit(1)
        ).first()
        if signals is None:
            return "GS-001"
        last_num = int(signals.signal_id.split("-")[1])
        return f"GS-{str(last_num + 1).zfill(3)}"

# ── HELPER: ATTACH PRICE ANCHOR ───────────────────────────────────────────────

def attach_price_anchor(signal: Signal, series_data: dict,
                        deltas_7d: dict, deltas_30d: dict,
                        deltas_90d: dict) -> Signal:
    """
    Given a signal and today's price snapshot, attach the most relevant
    commodity anchor. Called during GS classification step.
    C08 signals → WTI or Brent
    C09 signals → LME Aluminum or Steel
    C02 signals → UST 10Y or BBB OAS
    All others  → most breached series today
    """
    c_tags = []
    try:
        import json
        c_tags = json.loads(signal.c_tags or "[]")
    except Exception:
        pass

    commodity_map = {
        "C08": ("brent_usd_bbl",    "BRENT",        "$/bbl"),
        "C05": ("wti_usd_bbl",      "WTI",          "$/bbl"),
        "C09": ("bbb_oas_bps",      "BBB_OAS",      "bps"),
        "C02": ("ust_10y_pct",      "UST_10Y",      "%"),
        "C01": ("ust_10y_pct",      "UST_10Y",      "%"),
        "C06": ("henry_hub_usd_mmbtu", "HENRY_HUB", "$/MMBtu"),
        "C07": ("henry_hub_usd_mmbtu", "HENRY_HUB", "$/MMBtu"),
        "C11": ("ercot_hub_north_mwh", "ERCOT_NORTH", "$/MWh"),
    }

    anchor_field = None
    anchor_name  = None
    anchor_unit  = None

    for tag in c_tags:
        if tag in commodity_map:
            anchor_field, anchor_name, anchor_unit = commodity_map[tag]
            break

    if anchor_field and series_data.get(anchor_field):
        data = series_data[anchor_field]
        signal.anchor_commodity  = anchor_name
        signal.anchor_value      = data.get("value")
        signal.anchor_unit       = anchor_unit
        signal.anchor_delta_7d   = deltas_7d.get(anchor_field)
        signal.anchor_delta_30d  = deltas_30d.get(anchor_field)
        signal.anchor_delta_90d  = deltas_90d.get(anchor_field)
        signal.anchor_source     = data.get("category", "FRED")
        signal.anchor_fetched_at = data.get("series_date")

    return signal

if __name__ == "__main__":
    import os
    DB_PATH = r"C:\Users\nagar_7kszmu8\GroundTruth_v2\groundtruth.db"
    engine = init_database(DB_PATH)
    print("\nSchema validation complete.")
    print(f"Next signal ID will be: {get_next_signal_id(engine)}")