#!/usr/bin/env python
# send_email.py — Rebuild and send the GroundTruth daily email using the
# CURRENT state of the database and the LATEST consolidated sector brief
# for today as Section 1.
#
# Manual resend step for the brief-integrated email workflow:
#
#   1. python infra/run_manual.py             → runs capture, auto-sends email
#                                                 (Section 1 will be placeholder
#                                                 or prior brief, whichever is
#                                                 most recent for today)
#   2. I hand-write today's consolidated brief to outputs/sector_briefs_*.md
#   3. python infra/send_email.py             → rebuilds & resends email with
#                                                 the just-written brief as
#                                                 Section 1
#
# This script does NOT run a capture. It only rebuilds the email from the
# current DB state and resends. Safe to run multiple times per day.
#
# Usage:
#   python infra/send_email.py                # resend with current state
#   python infra/send_email.py --dry          # build & save HTML, do not send

import sys
import os
import json
import argparse
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(r"C:\Users\nagar_7kszmu8\GroundTruth_v2")
DB_PATH = PROJECT_ROOT / "groundtruth.db"
FALLBACK_HTML = PROJECT_ROOT / "email_fallback.html"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _get_latest_run_summary() -> dict:
    """Read the most recent completed run from gs_fetch_runs for email context."""
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
            "regime": "R0 — Compound Stress",
            "crisis_day": 0,
            "runtime_seconds": 0,
            "sources_fetched": 0,
            "signals_classified": 0,
            "red_count": 0,
            "amber_count": 0,
            "green_count": 0,
            "fetch_failures": [],
            "email_sent": False,
        }

    row = dict(row)
    failures = []
    try:
        failures = json.loads(row.get("failures", "[]") or "[]")
    except Exception:
        pass

    return {
        "run_id":              row.get("run_id", ""),
        "trigger":             row.get("run_type", "manual-resend"),
        "started_at":          row.get("started_at", ""),
        "completed_at":        row.get("completed_at", ""),
        "runtime_seconds":     row.get("runtime_seconds", 0) or 0,
        "sources_fetched":     row.get("sources_attempted", 0) or 0,
        "signals_classified":  row.get("signals_created", 0) or 0,
        "red_count":           row.get("red_count", 0) or 0,
        "amber_count":         row.get("amber_count", 0) or 0,
        "green_count":         0,
        "fetch_failures":      failures,
        "regime":              row.get("regime_code", "R0 — Compound Stress"),
        "crisis_day":          0,
        "email_sent":          False,
    }


def _get_scored_signals(limit: int = 500) -> list:
    """Fetch active scored signals for the email body."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM gs_signals WHERE status = 'ACTIVE' "
        "ORDER BY CASE alert_level WHEN 'RED' THEN 1 "
        "WHEN 'AMBER' THEN 2 ELSE 3 END, "
        "weighted_score DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_encyclopedia_match(signals: list) -> dict:
    """Run encyclopedia matching on the current signals for Section 4."""
    try:
        from gi.encyclopedia import load_encyclopedia, match_signals_to_encyclopedia
        enc = load_encyclopedia()
        match_input = []
        for s in signals[:100]:
            match_input.append({
                "c_tags": s.get("c_tags", "[]"),
                "a_tags": s.get("a_tags", "[]"),
            })
        if match_input:
            return match_signals_to_encyclopedia(match_input, enc, "R0")
    except Exception as e:
        print(f"  WARN: encyclopedia match failed: {e}")
    return {"top_match": None, "second_match": None, "third_match": None}


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild and resend the GroundTruth email with the latest brief."
    )
    parser.add_argument(
        "--dry", action="store_true",
        help="Build the HTML and save to email_fallback.html without sending.",
    )
    args = parser.parse_args()

    print("=" * 58)
    print("  GROUNDTRUTH EMAIL RESEND — brief-integrated")
    print("=" * 58)

    # Gather state
    run_summary = _get_latest_run_summary()
    print(f"  Run summary: {run_summary.get('run_id', 'none')} "
          f"({run_summary.get('completed_at', 'unknown')})")

    signals = _get_scored_signals()
    print(f"  Active signals loaded: {len(signals)}")

    encyclopedia_match = _get_encyclopedia_match(signals)
    top = encyclopedia_match.get("top_match")
    if top:
        print(f"  Encyclopedia top match: {top.get('code', '')} "
              f"({top.get('match_score', 0)}%)")

    # Build email
    from gt.email_builder import build_email, build_subject, send_digest, _find_latest_brief_for_today

    brief_path = _find_latest_brief_for_today()
    if brief_path:
        print(f"  Brief for Section 1: {brief_path.name}")
    else:
        print(f"  Brief for Section 1: none found — placeholder will be used")

    html = build_email(signals, encyclopedia_match, run_summary)
    subject = build_subject(signals, run_summary)
    print(f"  Subject: {subject}")
    print(f"  HTML length: {len(html)} chars")

    # Archive the dashboard HTML to the dated outputs folder every run
    # (gitignored root fallback + git-tracked dated archive). Mirrors
    # orchestrator.py's _archive_dashboard_html — 2026-04-19 email workflow
    # change; see docs/CHANGELOG.md.
    def _archive_dashboard(html_str: str) -> Path | None:
        try:
            from datetime import datetime as _dt
            import pytz as _pytz
            now_et = _dt.now(_pytz.timezone("America/New_York"))
            day_dir = PROJECT_ROOT / "outputs" / "daily" / now_et.strftime("%Y-%m") / now_et.strftime("%m-%d")
            day_dir.mkdir(parents=True, exist_ok=True)
            fname = f"dashboard_{now_et.strftime('%Y-%m-%d_%H%M')}ET.html"
            dated = day_dir / fname
            dated.write_text(html_str, encoding="utf-8")
            FALLBACK_HTML.write_text(html_str, encoding="utf-8")
            return dated
        except Exception as e:
            print(f"  WARN: Dashboard archive failed: {e}")
            return None

    archived = _archive_dashboard(html)
    if archived:
        print(f"  Dashboard archived: {archived}")

    if args.dry:
        print(f"  DRY RUN — email NOT sent. Root fallback: {FALLBACK_HTML}")
        return

    sent = send_digest(signals, encyclopedia_match, run_summary)
    if sent:
        print(f"  Email SENT")
    else:
        print(f"  Send failed — dashboard archive still written (see above)")


if __name__ == "__main__":
    main()
