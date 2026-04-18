# GS — GroundSignals Store
# PRD Section 3.5 — Processing Sequence Step 7
# Atomic writes to gs_signals. Failed write retries once then logs.
# All agents write signals through this module — never directly to DB.
# Last Updated: April 2026

import json
import sqlite3
from datetime import datetime
from sqlmodel import Session, select
from core.schema import (
    Signal, FetchRun, LatencyEvent,
    get_engine, get_next_signal_id,
    SignalStatus, AlertLevel
)

DB_PATH = r"C:\Users\nagar_7kszmu8\GroundTruth_v2\groundtruth.db"

# ── ENGINE ────────────────────────────────────────────────────────────────────

def get_db():
    return get_engine(DB_PATH)

# ── SIGNAL WRITE ──────────────────────────────────────────────────────────────

def write_signal(signal: Signal, retry: bool = True) -> Signal:
    """
    Atomic write of one signal to gs_signals.
    Assigns signal_id if not already set.
    Retries once on failure per PRD Section 3.5 Step 7.
    Returns the written signal with id populated.
    """
    engine = get_db()

    try:
        with Session(engine) as session:
            # Assign signal ID if not set
            if not signal.signal_id:
                signal.signal_id = get_next_signal_id(engine)

            # Set created_at if not set
            if not signal.created_at:
                signal.created_at = datetime.utcnow().isoformat()

            session.add(signal)
            session.commit()
            session.refresh(signal)
            return signal

    except Exception as e:
        if retry:
            print(f"  WARN: write_signal failed for {signal.signal_id}, retrying: {e}")
            return write_signal(signal, retry=False)
        else:
            print(f"  ERROR: write_signal failed after retry for "
                  f"{signal.signal_id}: {e}")
            raise

# ── DEDUPLICATION ─────────────────────────────────────────────────────────────

def is_duplicate(url: str, headline: str, days: int = 7) -> bool:
    """
    PRD Section 3.5 Step 3 — deduplicate by URL + headline within N days.
    Returns True if a matching signal exists in the window.
    """
    if not url and not headline:
        return False

    engine = get_db()
    with Session(engine) as session:
        from datetime import timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        existing = session.exec(
            select(Signal).where(
                Signal.created_at >= cutoff,
                Signal.status != SignalStatus.ARCHIVED,
            )
        ).all()

        for sig in existing:
            if url and sig.url and sig.url.strip() == url.strip():
                return True
            if headline and sig.headline:
                # Fuzzy match — same first 80 chars
                if sig.headline[:80].lower() == headline[:80].lower():
                    return True

    return False

def archive_duplicate(signal: Signal) -> Signal:
    """
    Mark a signal as duplicate and archive it.
    Per PRD: store with is_duplicate=true, status=ARCHIVED.
    """
    signal.status = SignalStatus.ARCHIVED
    signal.verification_note = "Archived — duplicate within 7-day window"
    return write_signal(signal)

# ── SIGNAL READS ──────────────────────────────────────────────────────────────

def get_signal(signal_id: str) -> Signal | None:
    engine = get_db()
    with Session(engine) as session:
        return session.exec(
            select(Signal).where(Signal.signal_id == signal_id)
        ).first()

def get_active_signals(limit: int = 100) -> list[Signal]:
    engine = get_db()
    with Session(engine) as session:
        return session.exec(
            select(Signal)
            .where(Signal.status == SignalStatus.ACTIVE)
            .order_by(Signal.created_at.desc())
            .limit(limit)
        ).all()

def get_red_signals(limit: int = 20) -> list[Signal]:
    engine = get_db()
    with Session(engine) as session:
        return session.exec(
            select(Signal)
            .where(
                Signal.status == SignalStatus.ACTIVE,
                Signal.alert_level == AlertLevel.RED,
            )
            .order_by(Signal.weighted_score.desc())
            .limit(limit)
        ).all()

def get_amber_signals(limit: int = 30) -> list[Signal]:
    engine = get_db()
    with Session(engine) as session:
        return session.exec(
            select(Signal)
            .where(
                Signal.status == SignalStatus.ACTIVE,
                Signal.alert_level == AlertLevel.AMBER,
            )
            .order_by(Signal.weighted_score.desc())
            .limit(limit)
        ).all()

def get_pipeline_alerts() -> list[Signal]:
    engine = get_db()
    with Session(engine) as session:
        return session.exec(
            select(Signal)
            .where(
                Signal.status == SignalStatus.ACTIVE,
                Signal.pipeline_risk_alert == 1,
            )
            .order_by(Signal.created_at.desc())
        ).all()

def get_signals_last_24h() -> list[Signal]:
    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    engine = get_db()
    with Session(engine) as session:
        return session.exec(
            select(Signal)
            .where(Signal.created_at >= cutoff)
            .order_by(Signal.created_at.desc())
        ).all()

# ── SIGNAL UPDATE ─────────────────────────────────────────────────────────────

def update_signal(signal_id: str, updates: dict) -> Signal | None:
    """
    Update specific fields on an existing signal.
    Used by GE to write scoring results back to GS record.
    """
    engine = get_db()
    with Session(engine) as session:
        signal = session.exec(
            select(Signal).where(Signal.signal_id == signal_id)
        ).first()

        if not signal:
            print(f"  WARN: update_signal — {signal_id} not found")
            return None

        for field, value in updates.items():
            if hasattr(signal, field):
                setattr(signal, field, value)
            else:
                print(f"  WARN: unknown field {field} on Signal")

        session.add(signal)
        session.commit()
        session.refresh(signal)
        return signal

def log_outcome(signal_id: str, outcome: str) -> Signal | None:
    """
    Log binary event outcome against a signal.
    Called by GT when Sri logs 'Log outcome for GS-XXX'.
    """
    return update_signal(signal_id, {
        "binary_event_outcome": outcome,
        "verification_note":    f"Outcome logged: {outcome}",
    })

# ── FETCH RUN MANAGEMENT ──────────────────────────────────────────────────────

def start_fetch_run(run_type: str) -> str:
    """
    Create a fetch run record. Returns run_id.
    """
    run_id = f"{run_type}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    engine = get_db()
    with Session(engine) as session:
        run = FetchRun(
            run_id     = run_id,
            run_type   = run_type,
            started_at = datetime.utcnow().isoformat(),
            status     = "RUNNING",
        )
        session.add(run)
        session.commit()
    print(f"Fetch run started: {run_id}")
    return run_id

def close_fetch_run(run_id: str, counts: dict, failures: list):
    """
    Close a fetch run with final counts and failure log.
    """
    engine = get_db()
    with Session(engine) as session:
        run = session.exec(
            select(FetchRun).where(FetchRun.run_id == run_id)
        ).first()

        if not run:
            return

        run.completed_at     = datetime.utcnow().isoformat()
        run.signals_created  = counts.get("created", 0)
        run.signals_draft    = counts.get("draft", 0)
        run.signals_active   = counts.get("active", 0)
        run.red_count        = counts.get("red", 0)
        run.amber_count      = counts.get("amber", 0)
        run.regime_code      = counts.get("regime", None)
        run.failures         = json.dumps(failures)
        run.status           = "PARTIAL" if failures else "COMPLETE"

        session.add(run)
        session.commit()
    print(f"Fetch run closed: {run_id} — "
          f"{counts.get('created', 0)} signals, "
          f"{len(failures)} failures")

# ── LATENCY EVENT WRITE ───────────────────────────────────────────────────────

def write_latency_event(signal_id: str, commodity: str,
                        observation_date: str, price_move_start: str,
                        latency_days: int, note: str = None,
                        encyclopedia_ref: str = None) -> LatencyEvent:
    """
    Log a verification latency measurement.
    Called by GE when ANECDOTAL signal + price move gap > 14 days.
    First measured event: LME Aluminum, 83 days, April 8 2026.
    """
    engine = get_db()
    with Session(engine) as session:
        event = LatencyEvent(
            signal_id        = signal_id,
            commodity        = commodity,
            observation_date = observation_date,
            price_move_start = price_move_start,
            latency_days     = latency_days,
            latency_note     = note,
            encyclopedia_ref = encyclopedia_ref,
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        print(f"Latency event logged: {commodity} — {latency_days} days "
              f"({price_move_start} → {observation_date})")
        return event

# ── DRAFT CLEANUP ─────────────────────────────────────────────────────────────

def cleanup_stale_drafts(max_age_hours: int = 2) -> int:
    """
    Archive DRAFT signals older than max_age_hours.
    These are classification attempts that never completed scoring.
    Called at start of each run by orchestrator.
    """
    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(hours=max_age_hours)).isoformat()

    engine = get_db()
    with Session(engine) as session:
        stale = session.exec(
            select(Signal).where(
                Signal.status == SignalStatus.DRAFT,
                Signal.created_at <= cutoff,
            )
        ).all()

        count = 0
        for sig in stale:
            sig.status = SignalStatus.ARCHIVED
            sig.verification_note = (
                f"Auto-archived — stuck DRAFT >{max_age_hours}h"
            )
            session.add(sig)
            count += 1

        if count:
            session.commit()
            print(f"  Cleaned {count} stale DRAFT signals")

    return count


# ── QUICK SUMMARY ─────────────────────────────────────────────────────────────

def db_summary():
    """
    Print a quick summary of database state.
    Called at start of each capture session.
    """
    engine = get_db()
    with Session(engine) as session:
        total    = len(session.exec(select(Signal)).all())
        active   = len(session.exec(
            select(Signal).where(Signal.status == SignalStatus.ACTIVE)
        ).all())
        red      = len(session.exec(
            select(Signal).where(Signal.alert_level == AlertLevel.RED)
        ).all())
        amber    = len(session.exec(
            select(Signal).where(Signal.alert_level == AlertLevel.AMBER)
        ).all())
        pipeline = len(session.exec(
            select(Signal).where(Signal.pipeline_risk_alert == 1)
        ).all())
        latency  = len(session.exec(select(LatencyEvent)).all())

    print("="*45)
    print("GROUNDTRUTH V2 — DATABASE SUMMARY")
    print("="*45)
    print(f"  Total signals:     {total}")
    print(f"  Active signals:    {active}")
    print(f"  RED alerts:        {red}")
    print(f"  AMBER alerts:      {amber}")
    print(f"  Pipeline alerts:   {pipeline}")
    print(f"  Latency events:    {latency}")
    print("="*45)

if __name__ == "__main__":
    print("Testing gs/store.py...")
    db_summary()

    # Write one test signal to confirm end-to-end
    from core.schema import Signal, SignalStatus, init_database
    init_database(DB_PATH)

    test_signal = Signal(
        source_type  = "ANECDOTAL",
        status       = SignalStatus.ACTIVE,
        headline     = "TEST — gs/store.py write validation",
        summary      = "Test signal written to confirm store module operational.",
        source_name  = "GroundTruth V2 store test",
        c_tags       = '["C08"]',
        t_tag        = "T1",
        o_tag        = "O1",
        second_order = "Store module test — delete after validation.",
        confidence   = 0.90,
        is_verified  = 1,
    )

    written = write_signal(test_signal)
    print(f"\nTest signal written: {written.signal_id}")
    print(f"DB id: {written.id}")

    db_summary()
    print("\ngs/store.py operational.")