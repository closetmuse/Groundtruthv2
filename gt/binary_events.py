"""
GroundTruth V2 — gt/binary_events.py
Binary event manager. Owns Section 8 of the daily email.
Countdown, outcome logging, encyclopedia trigger on resolution.
Feeds sheets/scoreboard.py when events resolve.
Connective tissue between live signals and historical record.

Last Updated: April 2026
"""

import sys
import os
import json
from datetime import datetime, date, timedelta
from typing import Optional

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

from sqlmodel import Session, select
from core.schema import BinaryEvent, Signal, ResolutionProposal, get_engine, init_database

DB_PATH = os.path.join(PROJECT_ROOT, "groundtruth.db")

VALID_ECODES = {"E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08"}

# ── SEED DATA ─────────────────────────────────────────────────────────────────

SEED_EVENTS = [
    {
        "event_id":             "BE-001",
        "name":                 "FOMC April 28-29 2026",
        "deadline":             "2026-04-29",
        "linked_deals":         '["Project Vega", "GT-108", "GT-109"]',
        "linked_signals":       None,
        "status":               "OPEN",
        "outcome":              None,
        "outcome_date":         None,
        "resolved_by":          None,
        "encyclopedia_trigger": "E08",
    },
    {
        "event_id":             "BE-002",
        "name":                 "FERC Large Load Rule",
        "deadline":             "2026-04-30",
        "linked_deals":         '["GT-108 SB Energy Ohio"]',
        "linked_signals":       None,
        "status":               "OPEN",
        "outcome":              None,
        "outcome_date":         None,
        "resolved_by":          None,
        "encyclopedia_trigger": None,
    },
    {
        "event_id":             "BE-003",
        "name":                 "OBBBA BOC Deadline",
        "deadline":             "2026-07-04",
        "linked_deals":         '["Project Vega"]',
        "linked_signals":       None,
        "status":               "OPEN",
        "outcome":              None,
        "outcome_date":         None,
        "resolved_by":          None,
        "encyclopedia_trigger": None,
    },
    {
        "event_id":             "BE-004",
        "name":                 "Trump April 8 Tariff Deadline",
        "deadline":             "2026-04-08",
        "linked_deals":         '["GT-108", "GT-109", "Project Vega"]',
        "linked_signals":       '["GT-041", "GT-042", "GT-043"]',
        "status":               "OPEN",
        "outcome":              None,
        "outcome_date":         None,
        "resolved_by":          None,
        "encyclopedia_trigger": "E07",
    },
]


# ── ENGINE ────────────────────────────────────────────────────────────────────

def _engine():
    return get_engine(DB_PATH)


# ── SEED ──────────────────────────────────────────────────────────────────────

def seed_events():
    """
    Insert the 4 active binary events if gt_binary_events table is empty.

    Safe to call multiple times — only seeds when table has zero rows.
    """
    engine = _engine()
    with Session(engine) as session:
        count = len(session.exec(select(BinaryEvent)).all())
        if count > 0:
            print(f"  Binary events table has {count} rows — skipping seed")
            return

        for ev in SEED_EVENTS:
            session.add(BinaryEvent(**ev))
        session.commit()
        print(f"  Seeded {len(SEED_EVENTS)} binary events")


# ── GET ACTIVE EVENTS ─────────────────────────────────────────────────────────

def get_active_events() -> list[dict]:
    """
    Return all OPEN binary events ordered by deadline ascending.

    Computes days_remaining and flags URGENT if <= 7 days.

    Returns:
        List of dicts with all event fields plus days_remaining and urgent.
    """
    engine = _engine()
    today = date.today()

    with Session(engine) as session:
        events = session.exec(
            select(BinaryEvent)
            .where(BinaryEvent.status == "OPEN")
            .order_by(BinaryEvent.deadline)
        ).all()

        result = []
        for ev in events:
            days_remaining = None
            try:
                dl = datetime.strptime(ev.deadline, "%Y-%m-%d").date()
                days_remaining = (dl - today).days
            except Exception:
                pass

            deals = []
            try:
                deals = json.loads(ev.linked_deals or "[]")
            except Exception:
                pass

            signals = []
            try:
                signals = json.loads(ev.linked_signals or "[]")
            except Exception:
                pass

            result.append({
                "event_id":             ev.event_id,
                "name":                 ev.name,
                "deadline":             ev.deadline,
                "days_remaining":       days_remaining,
                "urgent":               days_remaining is not None and days_remaining <= 7,
                "linked_deals":         deals,
                "linked_signals":       signals,
                "status":               ev.status,
                "encyclopedia_trigger": ev.encyclopedia_trigger,
            })

    return result


# ── COUNTDOWN BLOCK (Section 8 of email) ──────────────────────────────────────

def get_countdown_block() -> str:
    """
    Build formatted text block for Section 8 of the daily email.

    Groups events into URGENT (<=7d) and UPCOMING.
    Format per event:
        [BE-ID] EVENT NAME — T-N days
        Deals: linked deals
        Impact: from DB

    Returns:
        Multi-line plain text string for email insertion.
    """
    events = get_active_events()
    if not events:
        return "No open binary events."

    urgent = [e for e in events if e["urgent"]]
    upcoming = [e for e in events if not e["urgent"]]

    lines = []
    total = len(events)
    lines.append(f"BINARY EVENTS -- {total} OPEN")

    if urgent:
        lines.append("")
        lines.append("URGENT (7 days or less)")
        for e in urgent:
            days = e["days_remaining"]
            days_str = f"T-{days} days" if days >= 0 else f"T+{abs(days)} days OVERDUE"
            deals_str = ", ".join(e["linked_deals"]) if e["linked_deals"] else "none"
            enc = f" [triggers {e['encyclopedia_trigger']}]" if e["encyclopedia_trigger"] else ""
            lines.append(f"  [{e['event_id']}] {e['name']} -- {days_str}{enc}")
            lines.append(f"    Deals: {deals_str}")

    if upcoming:
        lines.append("")
        lines.append("UPCOMING")
        for e in upcoming:
            days = e["days_remaining"]
            days_str = f"T-{days} days" if days is not None else "date unknown"
            deals_str = ", ".join(e["linked_deals"]) if e["linked_deals"] else "none"
            enc = f" [triggers {e['encyclopedia_trigger']}]" if e["encyclopedia_trigger"] else ""
            lines.append(f"  [{e['event_id']}] {e['name']} -- {days_str}{enc}")
            lines.append(f"    Deals: {deals_str}")

    return "\n".join(lines)


# ── RESOLVE EVENT ─────────────────────────────────────────────────────────────

def resolve_event(event_id: str, outcome: str, hit: str = "TBD",
                  notes: str = "", resolved_by: str = "Sri",
                  dry_run: bool = False) -> dict:
    """
    Resolve a binary event: mark as RESOLVED, log outcome, update scoreboard.

    Args:
        event_id:    Binary event ID (e.g. BE-001).
        outcome:     What actually happened (free text).
        hit:         "Y", "N", or "TBD".
        notes:       Additional notes.
        resolved_by: Who resolved it (default "Sri").
        dry_run:     If True, print what would happen without writing.

    Returns:
        Resolution summary dict.
    """
    engine = _engine()

    with Session(engine) as session:
        ev = session.exec(
            select(BinaryEvent).where(BinaryEvent.event_id == event_id)
        ).first()

        if not ev:
            print(f"  ERROR: Binary event {event_id} not found")
            return {"error": f"{event_id} not found"}

        if ev.status == "RESOLVED":
            print(f"  WARN: {event_id} already resolved on {ev.outcome_date}")
            return {"error": f"{event_id} already resolved"}

        now = datetime.now().strftime("%Y-%m-%d %H:%M ET")

        deals = []
        try:
            deals = json.loads(ev.linked_deals or "[]")
        except Exception:
            pass

        signals = []
        try:
            signals = json.loads(ev.linked_signals or "[]")
        except Exception:
            pass

        # Compute days warning
        days_warning = 0
        try:
            dl = datetime.strptime(ev.deadline, "%Y-%m-%d").date()
            days_warning = max(0, (dl - date.today()).days)
        except Exception:
            pass

        summary = {
            "event_id":             event_id,
            "name":                 ev.name,
            "deadline":             ev.deadline,
            "outcome":              outcome,
            "hit":                  hit.upper(),
            "notes":                notes,
            "resolved_by":          resolved_by,
            "resolved_at":          now,
            "encyclopedia_trigger": ev.encyclopedia_trigger,
            "linked_deals":         deals,
            "days_warning":         days_warning,
        }

        if dry_run:
            print(f"\n  DRY RUN — resolve_event({event_id}):")
            print(f"    Name: {ev.name}")
            print(f"    Outcome: {outcome}")
            print(f"    Hit: {hit}")
            print(f"    Encyclopedia trigger: {ev.encyclopedia_trigger or 'none'}")
            print(f"    Linked deals: {deals}")
            print(f"    Would write to DB and Scoreboard")
            return summary

        # Update DB
        ev.status = "RESOLVED"
        ev.outcome = outcome
        ev.outcome_date = now
        ev.resolved_by = resolved_by
        session.add(ev)
        session.commit()
        print(f"  Resolved {event_id}: {ev.name}")

    # Log to Scoreboard
    try:
        from sheets.scoreboard import log_outcome as sb_log
        sb_log(
            event_id=event_id,
            event_name=ev.name,
            event_date=ev.deadline,
            predicted_impact=ev.name,
            actual_outcome=outcome,
            hit=hit.upper(),
            alert_level="RED",
            linked_deals=", ".join(deals),
            signal_ids=", ".join(signals),
            days_warning=days_warning,
            notes=notes,
            logged_by=resolved_by,
        )
    except Exception as e:
        print(f"  WARN: Scoreboard log failed: {e}")

    # Check encyclopedia trigger
    if ev.encyclopedia_trigger:
        print(f"  Encyclopedia trigger: {ev.encyclopedia_trigger} "
              f"pattern match now available for GI")

    return summary


# ── ADD EVENT ─────────────────────────────────────────────────────────────────

def add_event(event_id: str, name: str, deadline: str,
              linked_deals: list = None, impact: str = "",
              encyclopedia_trigger: str = None) -> bool:
    """
    Insert a new binary event to the database.

    Validates that deadline is not in the past and encyclopedia_trigger
    is a valid E-code if provided.

    Args:
        event_id:             Unique ID (e.g. BE-005).
        name:                 Human-readable event name.
        deadline:             ISO date string (YYYY-MM-DD).
        linked_deals:         List of deal names.
        impact:               Impact description.
        encyclopedia_trigger: E-code (E01-E08) if resolution triggers pattern.

    Returns:
        True if inserted, False on validation failure.
    """
    # Validate date
    try:
        dl = datetime.strptime(deadline, "%Y-%m-%d").date()
        if dl < date.today():
            print(f"  WARN: Deadline {deadline} is in the past — adding anyway "
                  f"(may be intentional for overdue events)")
    except ValueError:
        print(f"  ERROR: Invalid date format: {deadline} — expected YYYY-MM-DD")
        return False

    # Validate encyclopedia trigger
    if encyclopedia_trigger and encyclopedia_trigger not in VALID_ECODES:
        print(f"  ERROR: Invalid encyclopedia trigger: {encyclopedia_trigger} "
              f"— expected one of {VALID_ECODES}")
        return False

    engine = _engine()
    with Session(engine) as session:
        # Check for duplicate
        existing = session.exec(
            select(BinaryEvent).where(BinaryEvent.event_id == event_id)
        ).first()
        if existing:
            print(f"  WARN: {event_id} already exists — skipping")
            return False

        ev = BinaryEvent(
            event_id=event_id,
            name=name,
            deadline=deadline,
            linked_deals=json.dumps(linked_deals or []),
            status="OPEN",
            encyclopedia_trigger=encyclopedia_trigger,
        )
        session.add(ev)
        session.commit()
        print(f"  Added binary event: {event_id} — {name} ({deadline})")

    return True


# ── CHECK ENCYCLOPEDIA TRIGGERS ───────────────────────────────────────────────

def check_encyclopedia_triggers() -> list[dict]:
    """
    Scan all RESOLVED events with encyclopedia_trigger set.

    Returns list of triggered patterns for GI to use in matching.
    Called by orchestrator after each resolve sequence.

    Returns:
        List of dicts with event_id, encyclopedia_trigger, outcome.
    """
    engine = _engine()
    with Session(engine) as session:
        events = session.exec(
            select(BinaryEvent).where(
                BinaryEvent.status == "RESOLVED",
                BinaryEvent.encyclopedia_trigger.isnot(None),
            )
        ).all()

        triggers = []
        for ev in events:
            if ev.encyclopedia_trigger:
                triggers.append({
                    "event_id":             ev.event_id,
                    "encyclopedia_trigger": ev.encyclopedia_trigger,
                    "outcome":              ev.outcome,
                    "resolved_at":          ev.outcome_date,
                })

    if triggers:
        print(f"  Encyclopedia triggers active: {len(triggers)}")
        for t in triggers:
            print(f"    {t['event_id']} -> {t['encyclopedia_trigger']}")

    return triggers


# ── AUTO-DETECTION ────────────────────────────────────────────────────────────

# Keyword profiles for matching signals to binary events
EVENT_KEYWORDS = {
    "FOMC":  ["fomc", "federal reserve", "fed rate", "rate decision",
              "hike", "hold", "pause", "cut", "monetary policy", "powell"],
    "FERC":  ["ferc", "large load", "interconnection", "pjm queue",
              "generator interconnection", "ferc rule", "ferc order"],
    "OBBBA": ["obbba", "reconciliation", "itc", "ptc", "tax credit",
              "solar credit", "wind credit", "clean energy tax",
              "inflation reduction", "ira repeal"],
    "TRUMP": ["trump", "tariff", "ceasefire", "hormuz", "iran",
              "trade war", "steel tariff", "aluminum tariff"],
}


def _get_event_keywords(event: BinaryEvent) -> list[str]:
    """
    Build a keyword list for a binary event from its name and stored fields.

    Checks EVENT_KEYWORDS profiles first, falls back to splitting
    the event name into individual words.
    """
    name_upper = event.name.upper()
    for key, words in EVENT_KEYWORDS.items():
        if key.upper() in name_upper:
            return words

    # Fallback: split name into words, filter short/common words
    stop = {"the", "and", "for", "with", "from", "that", "this", "are"}
    return [
        w.lower() for w in event.name.split()
        if len(w) > 2 and w.lower() not in stop
    ]


def detect_resolutions() -> list[dict]:
    """
    Scan recent signals for content matching OPEN binary events.

    For each OPEN event, checks gs_signals created in last 48 hours
    for keyword matches in headline + summary. When match_score >= 0.4,
    creates a ResolutionProposal in gt_resolution_proposals.

    Returns:
        List of proposal dicts with event_id, signal_id, match_score,
        proposed_outcome, proposed_hit.
    """
    engine = _engine()
    cutoff = (datetime.utcnow() - timedelta(hours=48)).isoformat()

    with Session(engine) as session:
        # Get open events
        open_events = session.exec(
            select(BinaryEvent).where(BinaryEvent.status == "OPEN")
        ).all()

        if not open_events:
            return []

        # Get recent signals
        recent_signals = session.exec(
            select(Signal).where(Signal.created_at >= cutoff)
        ).all()

        if not recent_signals:
            print("  No signals in last 48h — nothing to match")
            return []

        proposals = []

        for event in open_events:
            keywords = _get_event_keywords(event)
            if not keywords:
                continue

            for signal in recent_signals:
                text = (
                    (signal.headline or "") + " " + (signal.summary or "")
                ).lower()

                # Count keyword hits
                hits = sum(1 for kw in keywords if kw in text)
                if hits == 0:
                    continue

                match_score = round(hits / len(keywords), 2)
                if match_score < 0.4:
                    continue

                # Extract proposed outcome from headline
                proposed_outcome = (signal.headline or "")[:200]

                # Simple hit inference: if signal text contains resolution
                # language, propose Y; if contradicts, N; else TBD
                positive_words = ["held", "hold", "pause", "approved",
                                  "passed", "extended", "ceasefire",
                                  "resolved", "confirmed"]
                negative_words = ["rejected", "failed", "collapsed",
                                  "cancelled", "withdrawn", "blocked"]
                proposed_hit = "TBD"
                for pw in positive_words:
                    if pw in text:
                        proposed_hit = "Y"
                        break
                for nw in negative_words:
                    if nw in text:
                        proposed_hit = "N"
                        break

                # Check for existing proposal (avoid duplicates)
                existing = session.exec(
                    select(ResolutionProposal).where(
                        ResolutionProposal.event_id == event.event_id,
                        ResolutionProposal.signal_id == signal.signal_id,
                    )
                ).first()
                if existing:
                    continue

                # Create proposal
                proposal = ResolutionProposal(
                    event_id=event.event_id,
                    signal_id=signal.signal_id,
                    match_score=match_score,
                    proposed_outcome=proposed_outcome,
                    proposed_hit=proposed_hit,
                )
                session.add(proposal)
                proposals.append({
                    "event_id":         event.event_id,
                    "event_name":       event.name,
                    "signal_id":        signal.signal_id,
                    "match_score":      match_score,
                    "proposed_outcome": proposed_outcome,
                    "proposed_hit":     proposed_hit,
                })

                print(f"  Proposal: {event.event_id} matched by "
                      f"{signal.signal_id} (score={match_score})")

        session.commit()

    if proposals:
        print(f"  {len(proposals)} resolution proposal(s) created")
    else:
        print("  No resolution proposals generated")

    return proposals


def get_pending_proposals() -> list[dict]:
    """
    Return all PENDING resolution proposals from DB.

    Used by get_countdown_block() to append PENDING CONFIRMATION section.
    """
    engine = _engine()
    with Session(engine) as session:
        props = session.exec(
            select(ResolutionProposal).where(
                ResolutionProposal.status == "PENDING"
            )
        ).all()

        result = []
        for p in props:
            # Look up event name
            event = session.exec(
                select(BinaryEvent).where(
                    BinaryEvent.event_id == p.event_id
                )
            ).first()
            event_name = event.name if event else p.event_id

            result.append({
                "event_id":         p.event_id,
                "event_name":       event_name,
                "signal_id":        p.signal_id,
                "match_score":      p.match_score,
                "proposed_outcome": p.proposed_outcome,
                "proposed_hit":     p.proposed_hit,
                "created_at":       p.created_at,
            })

    return result


def get_proposals_block() -> str:
    """
    Build formatted text block for pending proposals in Section 8.

    Appended below the countdown block when proposals exist.
    """
    pending = get_pending_proposals()
    if not pending:
        return ""

    lines = [
        "",
        f"RESOLUTION PROPOSALS -- {len(pending)} PENDING",
    ]

    for p in pending:
        lines.append(f"  [{p['event_id']}] {p['event_name']}")
        lines.append(f"    Signal: {p['signal_id']} -- \"{p['proposed_outcome'][:80]}\"")
        lines.append(f"    Proposed hit: {p['proposed_hit']}  "
                     f"Match score: {p['match_score']}")
        lines.append(f"    -> Reply CONFIRM {p['event_id']} or "
                     f"REJECT {p['event_id']} to log outcome.")

    return "\n".join(lines)


def confirm_resolution(event_id: str, dry_run: bool = False) -> dict:
    """
    Accept the latest PENDING proposal for a binary event.

    Calls resolve_event() with the proposed outcome and hit.
    Marks the proposal as ACCEPTED.

    Args:
        event_id: Binary event ID (e.g. BE-001).
        dry_run:  If True, print what would happen without writing.

    Returns:
        Resolution summary dict.
    """
    engine = _engine()
    with Session(engine) as session:
        proposal = session.exec(
            select(ResolutionProposal).where(
                ResolutionProposal.event_id == event_id,
                ResolutionProposal.status == "PENDING",
            ).order_by(ResolutionProposal.id.desc())
        ).first()

        if not proposal:
            print(f"  No pending proposal for {event_id}")
            return {"error": f"No pending proposal for {event_id}"}

        if dry_run:
            print(f"\n  DRY RUN — confirm_resolution({event_id}):")
            print(f"    Signal: {proposal.signal_id}")
            print(f"    Proposed outcome: {proposal.proposed_outcome[:80]}")
            print(f"    Proposed hit: {proposal.proposed_hit}")
            print(f"    Match score: {proposal.match_score}")
            print(f"    Would call resolve_event() and mark proposal ACCEPTED")
            return {
                "event_id": event_id,
                "signal_id": proposal.signal_id,
                "proposed_outcome": proposal.proposed_outcome,
                "proposed_hit": proposal.proposed_hit,
                "dry_run": True,
            }

        # Mark proposal accepted
        proposal.status = "ACCEPTED"
        session.add(proposal)
        session.commit()

    # Resolve the event
    summary = resolve_event(
        event_id=event_id,
        outcome=proposal.proposed_outcome,
        hit=proposal.proposed_hit,
        notes=f"Auto-confirmed from signal {proposal.signal_id} "
              f"(match={proposal.match_score})",
    )
    print(f"  Proposal accepted for {event_id}")
    return summary


def reject_resolution(event_id: str, reason: str = "") -> bool:
    """
    Reject the latest PENDING proposal for a binary event.

    Marks the proposal as REJECTED. Event stays OPEN.

    Args:
        event_id: Binary event ID.
        reason:   Rejection reason (optional).

    Returns:
        True if rejection recorded.
    """
    engine = _engine()
    with Session(engine) as session:
        proposal = session.exec(
            select(ResolutionProposal).where(
                ResolutionProposal.event_id == event_id,
                ResolutionProposal.status == "PENDING",
            ).order_by(ResolutionProposal.id.desc())
        ).first()

        if not proposal:
            print(f"  No pending proposal for {event_id}")
            return False

        proposal.status = "REJECTED"
        proposal.reject_reason = reason or "Rejected by Sri"
        session.add(proposal)
        session.commit()
        print(f"  Proposal rejected for {event_id}: {reason or 'no reason given'}")

    return True


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("GT BINARY EVENTS — MODULE TEST (v2 with auto-detection)")
    print("=" * 55)

    # Ensure DB tables exist (includes gt_resolution_proposals)
    init_database(DB_PATH)

    # Test 1: Confirm BE-004 corrected in DB and Sheets
    print("\n1. Verifying BE-004 outcome correction...")
    engine = _engine()
    with Session(engine) as session:
        be004 = session.exec(
            select(BinaryEvent).where(BinaryEvent.event_id == "BE-004")
        ).first()
        if be004:
            print(f"  Status: {be004.status}")
            print(f"  Outcome: {(be004.outcome or '')[:80]}...")
            print(f"  Resolved at: {be004.outcome_date}")
            assert be004.status == "RESOLVED", f"Expected RESOLVED, got {be004.status}"
            assert "ceasefire" in (be004.outcome or "").lower(), "Outcome not updated"
            print("  OK — BE-004 corrected")
        else:
            print("  WARN — BE-004 not found (may need seed)")
            seed_events()

    # Test 2: detect_resolutions() dry run against current signals
    print("\n2. Testing detect_resolutions()...")
    proposals = detect_resolutions()
    print(f"  Proposals generated: {len(proposals)}")
    for p in proposals:
        print(f"    {p['event_id']} matched by {p['signal_id']} "
              f"(score={p['match_score']}) — hit={p['proposed_hit']}")

    # Test 3: Print any proposals with match scores
    print("\n3. Pending proposals:")
    pending = get_pending_proposals()
    if pending:
        for p in pending:
            print(f"    [{p['event_id']}] {p['event_name']}")
            print(f"      Signal: {p['signal_id']}")
            print(f"      Outcome: {p['proposed_outcome'][:60]}...")
            print(f"      Hit: {p['proposed_hit']}, Score: {p['match_score']}")
    else:
        print("    No pending proposals (expected — limited signals in DB)")

    # Also print the proposals block
    pblock = get_proposals_block()
    if pblock:
        print(f"\n  Section 8 proposals block:")
        print(pblock)

    # Test 4: Confirm gt_resolution_proposals table exists
    print("\n4. Confirming gt_resolution_proposals table...")
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    conn.close()
    assert "gt_resolution_proposals" in tables, \
        f"Table not found. Tables: {tables}"
    print(f"  OK — gt_resolution_proposals exists in DB")
    print(f"  All tables: {tables}")

    # Test 5: confirm_resolution() dry run
    print("\n5. Testing confirm_resolution (dry run)...")
    if pending:
        first = pending[0]
        result = confirm_resolution(first["event_id"], dry_run=True)
        print(f"  OK — dry run for {first['event_id']}")
    else:
        print("  SKIP — no pending proposals to confirm")
        print("  (This is expected with only 2 test signals in DB)")

    # Show final state
    print("\n--- FINAL STATE ---")
    events = get_active_events()
    print(f"  Open binary events: {len(events)}")
    for e in events:
        days = e["days_remaining"]
        tag = " [URGENT]" if e["urgent"] else ""
        d = f"T-{days}d" if days >= 0 else f"T+{abs(days)}d OVERDUE"
        print(f"    {e['event_id']:8} {e['name']:30} {d}{tag}")

    triggers = check_encyclopedia_triggers()
    print(f"  Encyclopedia triggers: {len(triggers)}")
    for t in triggers:
        print(f"    {t['event_id']} -> {t['encyclopedia_trigger']}")

    print(f"\n  Countdown block:")
    print(get_countdown_block())

    print("\ngt/binary_events.py operational.")