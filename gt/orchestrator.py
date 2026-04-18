# GT — GroundTruth Orchestrator
# PRD Section 11 — Daily run sequence 06:00-09:00 ET
# Single entry point for scheduled runs, manual triggers, and breaking signals.
# Each stage wrapped in try/except — one failure never aborts the chain.
# Last Updated: April 2026

import sys
import os
import json
import uuid
from datetime import datetime

import pytz

# ── DRY RUN FLAG ──────────────────────────────────────────────────────────────
# Production default: False (email sends).
# Override with run_manual.py --dry for testing.
# run_scheduled.py always sets False explicitly.

DRY_RUN = False

# ── PATHS ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
DB_PATH      = os.path.join(PROJECT_ROOT, "groundtruth.db")
FALLBACK_HTML = os.path.join(PROJECT_ROOT, "email_fallback.html")

# Ensure project root is on sys.path for imports
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── TIMEZONE ──────────────────────────────────────────────────────────────────

ET = pytz.timezone("America/New_York")


def _now_et() -> str:
    """Return current time in ET as ISO string."""
    return datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S ET")


def _banner(stage: str):
    """Print a stage banner for readable Claude Desktop output."""
    print(f"\n{'--'*2} {stage} {'--'*(25 - len(stage)//2)}")


# ── MASTER ORCHESTRATOR ───────────────────────────────────────────────────────

def run(trigger: str = "scheduled") -> dict:
    """
    Master orchestrator. Runs the full GroundTruth chain in order.

    Chain sequence:
        1. prices.py     — fetch latest price snapshots, write to DB
        2. fetch.py      — fetch all P1 sources, collect raw items
        3. classify.py   — classify_batch() on all new raw items
        4. scorer.py     — score all newly classified signals
        5. encyclopedia  — match scored signals to historical precedents
        6. email_builder — send daily digest with all outputs
        7. store.py      — log run summary to gs_fetch_runs table

    Each stage wrapped in try/except. One stage failing does not abort
    the chain. Always returns run_summary even on partial failure.

    Args:
        trigger: "scheduled" | "manual" | "breaking"

    Returns:
        run_summary dict with all runtime stats.
    """
    run_id = str(uuid.uuid4())[:12]
    start = datetime.now(ET)

    summary = {
        "run_id":              run_id,
        "trigger":             trigger,
        "started_at":          start.strftime("%Y-%m-%d %H:%M:%S ET"),
        "completed_at":        "",
        "runtime_seconds":     0,
        "prices_fetched":      0,
        "sources_fetched":     0,
        "raw_items":           0,
        "signals_classified":  0,
        "red_count":           0,
        "amber_count":         0,
        "green_count":         0,
        "fetch_failures":      [],
        "regime":              "R0 — Compound Stress",
        "crisis_day":          (datetime.now(ET).date() - datetime(2026, 2, 28).date()).days,
        "top_precedent":       "",
        "email_sent":          False,
    }

    print("=" * 58)
    print(f"  GROUNDTRUTH V2 — {trigger.upper()} RUN")
    print(f"  {_now_et()}  |  Run ID: {run_id}")
    print(f"  DRY_RUN: {DRY_RUN} — "
          f"{'email suppressed' if DRY_RUN else 'email LIVE'}")
    print("=" * 58)

    # ── 1. PRICES ─────────────────────────────────────────────────────────
    _banner("PRICES")
    series_data = {}
    breaches = []
    try:
        from gs.prices import run_price_fetch
        series_data, breaches = run_price_fetch()
        summary["prices_fetched"] = len([
            v for v in series_data.values() if v is not None
        ])
        print(f"  Prices: {summary['prices_fetched']} series, "
              f"{len(breaches)} breaches")
    except Exception as e:
        print(f"  WARN: Prices failed — using stale snapshot. Error: {e}")

    # ── 2. FETCH ──────────────────────────────────────────────────────────
    _banner("FETCH")
    raw_items = []
    fetch_failures = []
    try:
        from gs.fetch import fetch_all_sources
        raw_items, fetch_failures = fetch_all_sources(max_items_per_source=5)
        summary["sources_fetched"] = len(
            [s for s in raw_items if s]  # count non-empty
        )
        summary["raw_items"] = len(raw_items)
        summary["fetch_failures"] = fetch_failures
        print(f"  Fetch: {len(raw_items)} items, "
              f"{len(fetch_failures)} source failures")
    except Exception as e:
        print(f"  WARN: Fetch failed. Error: {e}")
        summary["fetch_failures"] = [f"FETCH_FATAL: {e}"]

    # ── 3. CLASSIFY ───────────────────────────────────────────────────────
    _banner("CLASSIFY")
    signal_ids = []
    fetch_run_id = None

    # Clean stale DRAFTs from prior incomplete runs
    try:
        from gs.store import cleanup_stale_drafts
        cleanup_stale_drafts(max_age_hours=2)
    except Exception as e:
        print(f"  WARN: DRAFT cleanup failed: {e}")

    try:
        from gs.classify import classify_batch, update_live_context
        from gs.store import start_fetch_run

        # Update live context with fresh prices
        update_live_context(series_data)

        # Start fetch run for audit trail
        fetch_run_id = start_fetch_run("CONTENT")

        # classify_batch generates prompts for Claude Desktop
        # In automated mode, classification happens inline
        signal_ids = classify_batch(raw_items, fetch_run_id=fetch_run_id)
        summary["signals_classified"] = len(signal_ids)
        print(f"  Classify: {len(signal_ids)} signals written")

    except Exception as e:
        print(f"  WARN: Classification failed. Error: {e}")

    # ── 4. SCORE ──────────────────────────────────────────────────────────
    _banner("SCORE")
    scored_signals = []
    try:
        from ge.scorer import score_batch
        from gs.store import get_active_signals, update_signal

        # Get all active signals for batch scoring context
        active = get_active_signals(limit=500)
        if active:
            scored_signals = score_batch(active, current_regime="R0")

            # Write scores back to DB
            for s in scored_signals:
                # NOTE: affected_deals NOT included — owned by classify.py only
                update_signal(s.signal_id, {
                    "raw_score":       s.raw_score,
                    "weighted_score":  s.weighted_score,
                    "alert_level":     s.alert_level,
                    "scored_at":       s.scored_at,
                    "regime_at_score": s.regime_at_score,
                    "confidence":      s.confidence,
                    "pipeline_risk_alert": s.pipeline_risk_alert,
                })

            summary["red_count"] = sum(
                1 for s in scored_signals if s.alert_level == "RED"
            )
            summary["amber_count"] = sum(
                1 for s in scored_signals if s.alert_level == "AMBER"
            )
            summary["green_count"] = sum(
                1 for s in scored_signals if s.alert_level == "GREEN"
            )
            print(f"  Score: {len(scored_signals)} signals — "
                  f"RED {summary['red_count']} | "
                  f"AMBER {summary['amber_count']} | "
                  f"GREEN {summary['green_count']}")
        else:
            print("  Score: no active signals to score")

    except Exception as e:
        print(f"  WARN: Scoring failed. Error: {e}")

    # ── 4b. GPi DEAL ENGINE ─────────────────────────────────────────────
    _banner("GPi DEALS")
    deal_scores = []
    try:
        from gpi.pipeline_agent import score_all_deals, write_deal_watch_to_sheets
        deal_scores = score_all_deals(current_regime="R0")
        if deal_scores:
            write_deal_watch_to_sheets(deal_scores)
            hot = sum(1 for d in deal_scores if d.heat_level == "HOT")
            warm = sum(1 for d in deal_scores if d.heat_level == "WARM")
            print(f"  GPi: {len(deal_scores)} deals — HOT {hot} | WARM {warm}")
    except Exception as e:
        print(f"  WARN: GPi deal engine failed. Error: {e}")

    # ── 5. ENCYCLOPEDIA ───────────────────────────────────────────────────
    _banner("ENCYCLOPEDIA")
    encyclopedia_match = {
        "top_match": None, "second_match": None, "third_match": None
    }
    try:
        from gi.encyclopedia import load_encyclopedia, match_signals_to_encyclopedia

        enc = load_encyclopedia()

        # Build signal dicts for matching
        match_input = []
        for s in scored_signals:
            match_input.append({
                "c_tags": s.c_tags,
                "a_tags": getattr(s, "a_tags", "[]"),
            })

        if match_input:
            encyclopedia_match = match_signals_to_encyclopedia(
                match_input, enc, current_regime="R0"
            )
            top = encyclopedia_match.get("top_match")
            if top:
                summary["top_precedent"] = (
                    f"{top['code']} {top['event'][:30]} ({top['match_score']}%)"
                )
                print(f"  Encyclopedia: top match = {summary['top_precedent']}")
            else:
                print("  Encyclopedia: no match")
        else:
            print("  Encyclopedia: no signals to match")

    except Exception as e:
        print(f"  WARN: Encyclopedia matching failed. Error: {e}")

    # ── 6. EMAIL ──────────────────────────────────────────────────────────
    _banner("EMAIL")
    try:
        if DRY_RUN:
            from gt.email_builder import build_email, build_subject
            html = build_email(
                [_signal_to_dict(s) for s in scored_signals],
                encyclopedia_match,
                summary,
            )
            subject = build_subject(
                [_signal_to_dict(s) for s in scored_signals],
                summary,
            )
            print(f"  DRY RUN — email suppressed")
            print(f"  Subject: {subject}")
            print(f"  HTML: {len(html)} chars")
            # Write to fallback file for review
            with open(FALLBACK_HTML, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  Written to: {FALLBACK_HTML}")
            summary["email_sent"] = False
        else:
            from gt.email_builder import send_digest
            sent = send_digest(
                [_signal_to_dict(s) for s in scored_signals],
                encyclopedia_match,
                summary,
            )
            summary["email_sent"] = sent

    except Exception as e:
        print(f"  ERROR: Email failed. Error: {e}")
        # Write fallback HTML
        try:
            from gt.email_builder import build_email
            html = build_email(
                [_signal_to_dict(s) for s in scored_signals],
                encyclopedia_match,
                summary,
            )
            with open(FALLBACK_HTML, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  Fallback HTML written to: {FALLBACK_HTML}")
        except Exception as e2:
            print(f"  Fallback HTML also failed: {e2}")

    # ── 6b. SAVE DIGEST TO DRIVE ─────────────────────────────────────────
    try:
        from gt.email_builder import build_email, save_digest_to_drive
        html = build_email(
            [_signal_to_dict(s) for s in scored_signals],
            encyclopedia_match,
            summary,
        )
        drive_url = save_digest_to_drive(html)
        if drive_url:
            summary["digest_url"] = drive_url
    except Exception as e:
        print(f"  WARN: Drive digest save failed: {e}")

    # ── 7. CLOSE FETCH RUN ──────────────────────────────────────────────
    _banner("LOG")
    end = datetime.now(ET)
    summary["completed_at"] = end.strftime("%Y-%m-%d %H:%M:%S ET")
    summary["runtime_seconds"] = int((end - start).total_seconds())

    if fetch_run_id:
        try:
            from gs.store import close_fetch_run
            close_fetch_run(fetch_run_id, {
                "created":  summary["signals_classified"],
                "active":   summary["signals_classified"],
                "red":      summary["red_count"],
                "amber":    summary["amber_count"],
                "regime":   summary.get("regime", "R0"),
            }, summary["fetch_failures"])
        except Exception as e:
            print(f"  WARN: close_fetch_run failed: {e}")
    else:
        print("  No fetch_run_id — classify stage may have been skipped")

    # ── 8. SHEETS SYNC — always runs ─────────────────────────────────────
    _banner("SHEETS SYNC")
    try:
        from sheets.interface import sync_all
        sync_result = sync_all(run_id=run_id, trigger=trigger)
        print(f"  Sheets sync: {sync_result.signals_written} signals written")
        if sync_result.errors:
            print(f"  Sync errors: {sync_result.errors}")
    except Exception as e:
        print(f"  WARN: Sheets sync failed: {e}")

    # ── 9. HEALTH CHECK ──────────────────────────────────────────────────
    _banner("HEALTH")
    try:
        from infra.health_monitor import run_health_check, write_health_to_sheets, RunContext
        health_ctx = RunContext(
            run_id=run_id,
            run_started_at=summary["started_at"],
            run_completed_at=summary["completed_at"],
            sources_attempted=18,
            sources_succeeded=18 - len(summary["fetch_failures"]),
            sources_failed=summary["fetch_failures"],
            signals_fetched=summary.get("raw_items", 0),
            signals_filtered=summary.get("raw_items", 0) - summary["signals_classified"],
            signals_classified=summary["signals_classified"],
            signals_new=summary["signals_classified"],
            email_sent=summary["email_sent"],
            email_sent_at=summary["completed_at"],
            current_regime="R0",
            deals_active=len(deal_scores) if deal_scores else 0,
            deals_scored=len(deal_scores) if deal_scores else 0,
            deal_scores=deal_scores,
        )
        health_report = run_health_check(health_ctx)
        write_health_to_sheets(health_report)
        # Pass health HTML to email builder via summary
        from infra.health_monitor import build_health_html
        summary["_health_html"] = build_health_html(health_report)
    except Exception as e:
        print(f"  WARN: Health check failed. Error: {e}")

    # ── SUMMARY ───────────────────────────────────────────────────────────
    print(f"\n{'='*58}")
    print(f"  RUN COMPLETE — {summary['completed_at']}")
    print(f"  Runtime:    {summary['runtime_seconds']}s")
    print(f"  Prices:     {summary['prices_fetched']} series")
    print(f"  Sources:    {summary['sources_fetched']} items fetched")
    print(f"  Classified: {summary['signals_classified']}")
    print(f"  RED:        {summary['red_count']}")
    print(f"  AMBER:      {summary['amber_count']}")
    print(f"  GREEN:      {summary['green_count']}")
    print(f"  Precedent:  {summary['top_precedent'] or 'none'}")
    print(f"  Email:      {'sent' if summary['email_sent'] else 'not sent'}")
    print(f"  Failures:   {len(summary['fetch_failures'])}")
    print(f"{'='*58}")

    # Print permanent digest URL if available
    marker = os.path.join(PROJECT_ROOT, ".drive_digest_id")
    if os.path.exists(marker):
        with open(marker) as f:
            fid = f.read().strip()
        print(f"\n{'='*58}")
        print(f"  DIGEST URL (bookmark this):")
        print(f"  https://drive.google.com/file/d/{fid}/view")
        print(f"{'='*58}\n")

    return summary


# ── PRICES ONLY ───────────────────────────────────────────────────────────────

def run_prices_only() -> dict:
    """
    Price fetch only — no content fetch, classify, or email.

    Used by scheduler between full runs to keep the price snapshot
    fresh in groundtruth.db. Lightweight and fast.

    Returns:
        Dict with prices_fetched count and any breaches.
    """
    _banner("PRICES ONLY")
    result = {"prices_fetched": 0, "breaches": []}

    try:
        from gs.prices import run_price_fetch
        series_data, breaches = run_price_fetch()
        result["prices_fetched"] = len([
            v for v in series_data.values() if v is not None
        ])
        result["breaches"] = breaches
        print(f"  Prices: {result['prices_fetched']} series, "
              f"{len(breaches)} breaches")
    except Exception as e:
        print(f"  ERROR: Price fetch failed: {e}")

    return result


# ── BREAKING SIGNAL ───────────────────────────────────────────────────────────

def run_breaking_signal(headline: str, content: str,
                        source: str = "ANECDOTAL") -> str:
    """
    Fast path for 'Flag breaking signal' trigger phrase.

    Skips fetch. Builds a single raw dict, classifies, scores, and
    sends email if RED. T1 signals only — logs warning if classified
    T2 or T3 because breaking signals should have immediate value.

    Args:
        headline: Signal headline (max 120 chars).
        content: Signal content / observation text.
        source: Source name (default "ANECDOTAL" for desk observations).

    Returns:
        Signal ID if written, empty string on failure.
    """
    print(f"\n{'='*58}")
    print(f"  BREAKING SIGNAL — {_now_et()}")
    print(f"  {headline[:80]}")
    print(f"{'='*58}")

    try:
        from ge.scorer import score_signal
        from gs.store import get_active_signals, update_signal
        from core.schema import Signal, SourceType, SignalStatus

        # Build raw dict
        raw = {
            "source_name":      source,
            "url":              "",
            "publication_date": _now_et(),
            "headline":         headline[:120],
            "raw_content":      content[:3000],
            "summary":          content[:500],
            "c_tags":           [],
        }

        # For ANECDOTAL signals, build directly and write to DB
        if source == "ANECDOTAL":
            from gs.store import write_signal, get_next_signal_id, get_db

            signal = Signal(
                source_type  = SourceType.ANECDOTAL,
                status       = SignalStatus.ACTIVE,
                headline     = headline[:120],
                summary      = content[:500],
                raw_content  = content[:3000],
                source_name  = source,
                publication_date = _now_et(),
                t_tag        = "T1",
                confidence   = 0.75,
                is_verified  = 1,
            )
            written = write_signal(signal)
            signal_id = written.signal_id

            # Score it
            active = get_active_signals(limit=50)
            scored = score_signal(written, current_regime="R0",
                                 recent_signals=active)
            update_signal(signal_id, {
                "raw_score":       scored.raw_score,
                "weighted_score":  scored.weighted_score,
                "alert_level":     scored.alert_level,
                "scored_at":       scored.scored_at,
                "regime_at_score": scored.regime_at_score,
            })

            # Warn if not T1
            if scored.t_tag and scored.t_tag != "T1":
                print(f"  WARNING: Breaking signal classified as {scored.t_tag} "
                      f"— expected T1. Value may degrade quickly.")

            print(f"  Signal written: {signal_id}")
            print(f"  Score: {scored.weighted_score} | "
                  f"Alert: {scored.alert_level}")

            # Send email if RED and not dry run
            if scored.alert_level == "RED" and not DRY_RUN:
                try:
                    from gt.email_builder import send_digest
                    from gi.encyclopedia import (
                        load_encyclopedia, match_signals_to_encyclopedia
                    )
                    enc = load_encyclopedia()
                    match = match_signals_to_encyclopedia(
                        [{"c_tags": scored.c_tags}], enc, "R0"
                    )
                    send_digest(
                        [_signal_to_dict(scored)],
                        match,
                        {"regime": "R0 — Compound Stress",
                         "crisis_day": 42,
                         "trigger": "breaking"},
                    )
                except Exception as e:
                    print(f"  Email send failed: {e}")
            elif scored.alert_level == "RED":
                print(f"  DRY RUN — RED alert email suppressed")

            return signal_id

        # For FETCH signals, return the prompt and wait for response
        return ""

    except Exception as e:
        print(f"  ERROR: Breaking signal failed: {e}")
        return ""


# ── RUN SUMMARY READER ────────────────────────────────────────────────────────

def get_run_summary() -> dict:
    """
    Read the last completed run from gs_fetch_runs table.

    Returns dict with run_id, trigger, timestamps, signal counts,
    failures, and regime. Returns empty defaults if no runs exist.
    """
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM gs_fetch_runs "
        "WHERE status IN ('COMPLETE', 'PARTIAL') "
        "ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if not row:
        return {
            "run_id": None,
            "trigger": "none",
            "started_at": "",
            "completed_at": "",
            "signals_classified": 0,
            "red_count": 0,
            "amber_count": 0,
            "green_count": 0,
            "fetch_failures": [],
            "regime": "R0",
        }

    row = dict(row)
    failures = []
    try:
        failures = json.loads(row.get("failures", "[]") or "[]")
    except Exception:
        pass

    return {
        "run_id":              row.get("run_id", ""),
        "trigger":             row.get("run_type", ""),
        "started_at":          row.get("started_at", ""),
        "completed_at":        row.get("completed_at", ""),
        "signals_classified":  row.get("signals_created", 0),
        "red_count":           row.get("red_count", 0),
        "amber_count":         row.get("amber_count", 0),
        "green_count":         0,
        "fetch_failures":      failures,
        "regime":              row.get("regime_code", "R0"),
    }


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _signal_to_dict(signal) -> dict:
    """
    Convert a Signal SQLModel object to a plain dict for email builder.

    Handles both Signal objects and dicts (passthrough).
    """
    if isinstance(signal, dict):
        return signal

    fields = [
        "signal_id", "headline", "summary", "second_order",
        "c_tags", "f_tags", "t_tag", "o_tag",
        "alert_level", "weighted_score", "raw_score", "confidence",
        "pipeline_risk_alert", "affected_deals",
        "risk_alert_confidence", "risk_alert_rationale",
        "opportunity_alert", "opportunity_sector",
        "opportunity_type", "opportunity_urgency",
        "opportunity_rationale", "linkedin_candidate",
        "theme_tags", "source_name", "url", "publication_date",
        "anchor_commodity", "anchor_value", "anchor_unit",
        "anchor_delta_7d", "anchor_delta_30d", "anchor_delta_90d",
    ]
    d = {}
    for f in fields:
        d[f] = getattr(signal, f, None)
    return d


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    DRY_RUN = True
    summary = run(trigger="manual")

    print("\n\nFINAL RUN SUMMARY:")
    print(json.dumps(summary, indent=2, default=str))