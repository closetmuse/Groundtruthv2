"""
GroundTruth V2 — infra/health_monitor.py
System Health Dashboard. Runs after every capture.
Tests 8 subsystems, scores against ideals, produces structured report.
Outputs to email Section 10, Google Sheets Health tab, and console.

Last Updated: April 2026
"""

import sys
import os
import json
import sqlite3
from datetime import datetime, date
from dataclasses import dataclass, field
from typing import Optional

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "groundtruth.db")


# ── RUN CONTEXT ───────────────────────────────────────────────────────────────

@dataclass
class RunContext:
    """Populated by orchestrator as it runs each stage."""
    run_id: str = ""
    run_started_at: str = ""
    run_completed_at: str = ""
    sources_attempted: int = 18
    sources_succeeded: int = 0
    sources_failed: list = field(default_factory=list)
    signals_fetched: int = 0
    signals_filtered: int = 0
    signals_classified: int = 0
    signals_new: int = 0
    email_sent: bool = False
    email_sent_at: str = ""
    email_error: str = None
    current_regime: str = "R0"
    deals_active: int = 0
    deals_scored: int = 0
    deal_scores: list = field(default_factory=list)


# ── SUBSYSTEM CHECK RESULT ────────────────────────────────────────────────────

@dataclass
class SubsystemResult:
    code: str           # GS-1, GE-1, etc.
    name: str           # "Fetch Coverage"
    ideal: str          # "18/18"
    actual: str         # "16/18"
    status: str         # GREEN / AMBER / RED
    note: str = ""      # Optional footnote


# ── HEALTH REPORT ─────────────────────────────────────────────────────────────

@dataclass
class HealthReport:
    subsystems: list = field(default_factory=list)  # list[SubsystemResult]
    score: float = 0.0
    max_score: int = 18
    level: str = "UNKNOWN"     # HEALTHY / DEGRADED / FAILING
    timestamp: str = ""
    run_id: str = ""
    notes: list = field(default_factory=list)


# ── 8 SUBSYSTEM CHECKS ───────────────────────────────────────────────────────

def _check_gs1_fetch(ctx: RunContext) -> SubsystemResult:
    """GS-1: Fetch Coverage."""
    succeeded = ctx.sources_succeeded
    attempted = ctx.sources_attempted
    failed_names = ", ".join(ctx.sources_failed[:4]) if ctx.sources_failed else "none"

    if succeeded >= 16:
        status = "GREEN"
    elif succeeded >= 12:
        status = "AMBER"
    else:
        status = "RED"

    return SubsystemResult(
        code="GS-1", name="Fetch Coverage",
        ideal=f"{attempted}/{attempted}",
        actual=f"{succeeded}/{attempted}",
        status=status,
        note=f"Failed: {failed_names}" if ctx.sources_failed else "",
    )


def _check_gs2_volume(ctx: RunContext) -> SubsystemResult:
    """GS-2: Signal Volume."""
    n = ctx.signals_new

    if 15 <= n <= 40:
        status = "GREEN"
    elif 8 <= n <= 60:
        status = "AMBER"
    else:
        status = "RED"

    return SubsystemResult(
        code="GS-2", name="Signal Volume",
        ideal="15-40/run",
        actual=f"{n}/run",
        status=status,
    )


def _check_gs3_filter(ctx: RunContext) -> SubsystemResult:
    """GS-3: Relevance Filter Rate."""
    total = ctx.signals_fetched
    filtered = ctx.signals_filtered

    if total == 0:
        rate = 0
    else:
        rate = round((filtered / total) * 100)

    if 20 <= rate <= 35:
        status = "GREEN"
    elif 10 <= rate <= 50:
        status = "AMBER"
    else:
        status = "RED"

    return SubsystemResult(
        code="GS-3", name="Relevance Filter",
        ideal="20-35%",
        actual=f"{rate}% ({filtered}/{total})",
        status=status,
    )


def _check_ge1_distribution() -> SubsystemResult:
    """GE-1: Alert Distribution across ACTIVE signals."""
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute(
        "SELECT COUNT(*) FROM gs_signals WHERE status='ACTIVE'"
    ).fetchone()[0]
    red = conn.execute(
        "SELECT COUNT(*) FROM gs_signals WHERE status='ACTIVE' AND alert_level='RED'"
    ).fetchone()[0]
    amber = conn.execute(
        "SELECT COUNT(*) FROM gs_signals WHERE status='ACTIVE' AND alert_level='AMBER'"
    ).fetchone()[0]
    green = conn.execute(
        "SELECT COUNT(*) FROM gs_signals WHERE status='ACTIVE' AND alert_level='GREEN'"
    ).fetchone()[0]
    conn.close()

    if total == 0:
        return SubsystemResult("GE-1", "Alert Distribution",
                               "R10-20% A40-60% G25-45%", "no signals", "RED")

    r_pct = round(red / total * 100)
    a_pct = round(amber / total * 100)
    g_pct = round(green / total * 100)

    bands_ok = 0
    if 10 <= r_pct <= 20:
        bands_ok += 1
    if 40 <= a_pct <= 60:
        bands_ok += 1
    if 25 <= g_pct <= 45:
        bands_ok += 1

    if bands_ok == 3:
        status = "GREEN"
    elif bands_ok >= 2:
        status = "AMBER"
    else:
        status = "RED"

    return SubsystemResult(
        code="GE-1", name="Alert Distribution",
        ideal="R10-20% A40-60% G25-45%",
        actual=f"R{r_pct}% A{a_pct}% G{g_pct}%",
        status=status,
    )


def _check_ge2_deal_match() -> SubsystemResult:
    """GE-2: Deal Match Rate on RED/AMBER signals."""
    conn = sqlite3.connect(DB_PATH)
    red_amber = conn.execute(
        "SELECT COUNT(*) FROM gs_signals "
        "WHERE status='ACTIVE' AND alert_level IN ('RED','AMBER')"
    ).fetchone()[0]
    matched = conn.execute(
        "SELECT COUNT(*) FROM gs_signals "
        "WHERE status='ACTIVE' AND alert_level IN ('RED','AMBER') "
        "AND affected_deals IS NOT NULL AND affected_deals != '[]' "
        "AND affected_deals != ''"
    ).fetchone()[0]
    conn.close()

    if red_amber == 0:
        return SubsystemResult("GE-2", "Deal Match Rate",
                               ">=40%", "no RED/AMBER", "AMBER")

    rate = round(matched / red_amber * 100)

    if rate >= 40:
        status = "GREEN"
    elif rate >= 20:
        status = "AMBER"
    else:
        status = "RED"

    return SubsystemResult(
        code="GE-2", name="Deal Match Rate",
        ideal=">=40%",
        actual=f"{rate}% ({matched}/{red_amber})",
        status=status,
    )


def _check_gpi1_coverage(ctx: RunContext) -> SubsystemResult:
    """GPi-1: Deal Heat Coverage."""
    active = ctx.deals_active
    scored = ctx.deals_scored

    if active == 0:
        return SubsystemResult("GPi-1", "Deal Heat Coverage",
                               "100%", "no deals", "AMBER")

    pct = round(scored / active * 100)

    if pct == 100:
        status = "GREEN"
    elif pct >= 90:
        status = "AMBER"
    else:
        status = "RED"

    return SubsystemResult(
        code="GPi-1", name="Deal Heat Coverage",
        ideal="100%",
        actual=f"{scored}/{active} ({pct}%)",
        status=status,
    )


def _check_gpi2_hot(ctx: RunContext) -> SubsystemResult:
    """GPi-2: HOT Deal Detection."""
    regime = ctx.current_regime
    scores = ctx.deal_scores

    hot = sum(1 for d in scores if getattr(d, "heat_level", "") == "HOT")
    warm_65 = sum(1 for d in scores
                  if getattr(d, "heat_level", "") == "WARM"
                  and getattr(d, "heat_score", 0) >= 65)

    # Check for METALS_PENDING
    has_metals_pending = any(
        "METALS_PENDING" in getattr(d, "data_flags", [])
        for d in scores
    )

    if regime in ("R3", "R4"):
        status = "GREEN"
        actual = f"{hot} HOT | regime {regime} — any distribution OK"
    elif hot >= 1:
        status = "GREEN"
        actual = f"{hot} HOT"
    elif warm_65 >= 5:
        status = "AMBER"
        actual = f"0 HOT | {warm_65} WARM>65"
    else:
        status = "RED"
        actual = f"0 HOT | {warm_65} WARM>65"

    note = ""
    if has_metals_pending:
        note = "METALS_PENDING — commodity scores may be understated"

    return SubsystemResult(
        code="GPi-2", name="HOT Deal Detection",
        ideal=f">=1 HOT ({regime})",
        actual=actual,
        status=status,
        note=note,
    )


def _check_ge3_sil() -> SubsystemResult:
    """GE-3: Sector Intelligence Filter Rate (unique misses, not cumulative)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        total_active = conn.execute(
            "SELECT COUNT(*) FROM gs_signals WHERE status='ACTIVE'"
        ).fetchone()[0]
        # Count unique signal-deal pairs (deduped), not cumulative rows
        sil_filtered = conn.execute(
            "SELECT COUNT(DISTINCT signal_id || '|' || deal_name) "
            "FROM ge_sil_misses"
        ).fetchone()[0]
        conn.close()

        if total_active == 0:
            return SubsystemResult("GE-3", "SIL Filter", "<50", "no data", "AMBER")

        # Metric: total unique SIL misses — target is reasonable count
        # GREEN = <20 unique misses | AMBER = 20-50 | RED = >50
        if sil_filtered < 20:
            status = "GREEN"
        elif sil_filtered <= 50:
            status = "AMBER"
        else:
            status = "RED"

        return SubsystemResult(
            code="GE-3", name="SIL Filter",
            ideal="<20 unique",
            actual=f"{sil_filtered} unique misses",
            status=status,
        )
    except Exception:
        return SubsystemResult("GE-3", "SIL Filter", "15-40%", "unavailable", "AMBER")


def _check_gt1_email(ctx: RunContext) -> SubsystemResult:
    """GT-1: Email Delivery."""
    if ctx.email_sent:
        status = "GREEN"
        actual = f"sent {ctx.email_sent_at or 'OK'}"
    else:
        status = "RED"
        actual = f"failed: {ctx.email_error or 'unknown'}"

    return SubsystemResult(
        code="GT-1", name="Email Delivery",
        ideal="Sent <5min",
        actual=actual,
        status=status,
    )


# ── MAIN HEALTH CHECK ────────────────────────────────────────────────────────

STATUS_POINTS = {"GREEN": 2, "AMBER": 1, "RED": 0}


def run_health_check(ctx: RunContext) -> HealthReport:
    """
    Run all 8 subsystem checks and produce a HealthReport.

    Args:
        ctx: RunContext populated by the orchestrator.

    Returns:
        HealthReport with subsystem results, score, and level.
    """
    report = HealthReport(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M ET"),
        run_id=ctx.run_id,
    )

    checks = [
        _check_gs1_fetch(ctx),
        _check_gs2_volume(ctx),
        _check_gs3_filter(ctx),
        _check_ge1_distribution(),
        _check_ge2_deal_match(),
        _check_gpi1_coverage(ctx),
        _check_gpi2_hot(ctx),
        _check_ge3_sil(),
        _check_gt1_email(ctx),
    ]

    report.subsystems = checks

    # Compute score
    points = sum(STATUS_POINTS.get(c.status, 0) for c in checks)
    report.score = round((points / report.max_score) * 100)

    if report.score >= 80:
        report.level = "HEALTHY"
    elif report.score >= 50:
        report.level = "DEGRADED"
    else:
        report.level = "FAILING"

    # Collect notes
    for c in checks:
        if c.note:
            report.notes.append(f"{c.code}: {c.note}")

    # Console output
    for c in checks:
        icon = {"GREEN": "G", "AMBER": "A", "RED": "R"}.get(c.status, "?")
        print(f"[HEALTH] {c.code} {c.name}: {c.actual} -- {c.status}")
    print(f"[HEALTH] OVERALL: {report.level} {points}/{report.max_score} "
          f"({report.score}%)")

    return report


# ── HEALTH EMAIL HTML ─────────────────────────────────────────────────────────

def build_health_html(report: HealthReport) -> str:
    """Build HTML table for email Section 10."""
    if not report or not report.subsystems:
        return "<tr><td>Health check not available.</td></tr>"

    STATUS_EMOJI = {"GREEN": "&#x1F7E2;", "AMBER": "&#x1F7E1;", "RED": "&#x1F534;"}
    DIM = "#666666"
    TEXT = "#e8e8e8"
    BORDER = "#333333"

    rows = ""
    for c in report.subsystems:
        emoji = STATUS_EMOJI.get(c.status, "?")
        rows += (
            f"<tr>"
            f"<td style='padding:3px 8px;border:1px solid {BORDER};font-size:11px;'>"
            f"{c.code} {c.name}</td>"
            f"<td style='padding:3px 8px;border:1px solid {BORDER};font-size:11px;"
            f"color:{DIM};'>{c.ideal}</td>"
            f"<td style='padding:3px 8px;border:1px solid {BORDER};font-size:11px;'>"
            f"{c.actual}</td>"
            f"<td style='padding:3px 8px;border:1px solid {BORDER};font-size:11px;"
            f"text-align:center;'>{emoji}</td>"
            f"</tr>"
        )

    notes_html = ""
    if report.notes:
        notes_html = "<br>".join(report.notes)
        notes_html = (
            f"<div style='padding:6px 0;font-size:10px;color:{DIM};'>"
            f"{notes_html}</div>"
        )

    html = (
        f"<div style='font-size:12px;font-weight:bold;padding:4px 0;'>"
        f"Overall: {report.level} &mdash; {report.score}%</div>"
        f"<table style='width:100%;border-collapse:collapse;margin:4px 0;'>"
        f"<tr style='background:#1a1a2e;'>"
        f"<th style='padding:4px 8px;font-size:10px;color:white;text-align:left;'>"
        f"Subsystem</th>"
        f"<th style='padding:4px 8px;font-size:10px;color:white;text-align:left;'>"
        f"Ideal</th>"
        f"<th style='padding:4px 8px;font-size:10px;color:white;text-align:left;'>"
        f"Actual</th>"
        f"<th style='padding:4px 8px;font-size:10px;color:white;text-align:center;'>"
        f"Status</th></tr>"
        f"{rows}</table>{notes_html}"
    )
    return html


# ── GOOGLE SHEETS HEALTH TAB ─────────────────────────────────────────────────

def write_health_to_sheets(report: HealthReport):
    """Write health report to Google Sheets Health tab."""
    try:
        from sheets.interface import _get_sheets_service, _get_sheet_id, _ensure_tab
    except ImportError:
        print("  Health: Sheets interface not available")
        return

    service = _get_sheets_service()
    sheet_id = _get_sheet_id()
    if not service or not sheet_id:
        return

    tab_name = "Health"
    tab_id = _ensure_tab(service, sheet_id, tab_name)

    # Read existing data to find where Section B starts
    existing = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"'{tab_name}'!A:A",
    ).execute()
    existing_rows = existing.get("values", [])

    if len(existing_rows) <= 1:
        # First write — create Section A header + data + Section B header
        section_a_header = [["Subsystem", "Code", "Ideal", "Actual", "Status", "Run Timestamp"]]
        section_a_data = [
            [c.name, c.code, c.ideal, c.actual, c.status, report.timestamp]
            for c in report.subsystems
        ]
        separator = [[""], [f"Overall: {report.level} — {report.score}%"], [""]]
        section_b_header = [[
            "Run Timestamp", "Health Score", "GS1", "GS2", "GS3",
            "GE1", "GE2", "GPi1", "GPi2", "GT1", "Notes"
        ]]
        section_b_row = _build_history_row(report)

        all_data = section_a_header + section_a_data + separator + section_b_header + [section_b_row]

        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A1",
            valueInputOption="RAW",
            body={"values": all_data},
        ).execute()

        # Update Section A data (overwrite rows 2-9)
        print(f"  Health: tab created with {len(report.subsystems)} subsystems + history")
    else:
        # Update Section A (rows 2-9, keeping header)
        section_a_data = [
            [c.name, c.code, c.ideal, c.actual, c.status, report.timestamp]
            for c in report.subsystems
        ]
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A2:F10",  # 9 subsystems: GS1-3, GE1-3, GPi1-2, GT1
            valueInputOption="RAW",
            body={"values": section_a_data},
        ).execute()

        # Append to Section B (history)
        section_b_row = _build_history_row(report)
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A13",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [section_b_row]},
        ).execute()
        print(f"  Health: updated Section A, appended history row")

    # Format header
    BG_HEADER = {"red": 0.10, "green": 0.10, "blue": 0.18}
    TXT_WHITE = {"red": 1, "green": 1, "blue": 1}
    reqs = [
        {
            "repeatCell": {
                "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": BG_HEADER,
                    "textFormat": {"foregroundColor": TXT_WHITE, "bold": True,
                                   "fontFamily": "Calibri", "fontSize": 12},
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat)",
            }
        },
        {
            "updateSheetProperties": {
                "properties": {"sheetId": tab_id,
                               "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        },
    ]
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": reqs},
    ).execute()


def _build_history_row(report: HealthReport) -> list:
    """Build one row for Section B history."""
    statuses = {c.code: c.status for c in report.subsystems}
    return [
        report.timestamp,
        f"{report.score}%",
        statuses.get("GS-1", ""),
        statuses.get("GS-2", ""),
        statuses.get("GS-3", ""),
        statuses.get("GE-1", ""),
        statuses.get("GE-2", ""),
        statuses.get("GPi-1", ""),
        statuses.get("GPi-2", ""),
        statuses.get("GT-1", ""),
        "; ".join(report.notes) if report.notes else "",
    ]


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 58)
    print("HEALTH MONITOR — MODULE TEST")
    print("=" * 58)

    # Test 1: Mock context — normal run
    print("\nTest 1: Normal run health check")
    ctx = RunContext(
        run_id="TEST-001",
        run_started_at="2026-04-12 14:27 ET",
        run_completed_at="2026-04-12 14:28 ET",
        sources_attempted=18,
        sources_succeeded=14,
        sources_failed=["IEA News", "FERC News", "Recharge News", "Natural Gas Intelligence"],
        signals_fetched=65,
        signals_filtered=18,
        signals_classified=47,
        signals_new=23,
        email_sent=True,
        email_sent_at="14:28 ET",
        current_regime="R0",
        deals_active=45,
        deals_scored=45,
    )
    report = run_health_check(ctx)
    print(f"\n  Level: {report.level}")
    print(f"  Score: {report.score}%")

    # Test 2: Write to Sheets
    print("\nTest 2: Writing to Health tab...")
    write_health_to_sheets(report)

    # Test 3: HTML output
    print("\nTest 3: HTML output (first 500 chars):")
    html = build_health_html(report)
    print(html[:500])

    # Test 4: Will test append on second run (covered by orchestrator)

    # Test 5: Simulate RED condition
    print("\nTest 5: Simulated RED condition (5 sources succeeded)")
    ctx_red = RunContext(
        run_id="TEST-RED",
        sources_attempted=18, sources_succeeded=5,
        sources_failed=["many sources"],
        signals_fetched=10, signals_filtered=1,
        signals_new=2, email_sent=False,
        email_error="Gmail auth failed",
        current_regime="R0",
        deals_active=45, deals_scored=45,
    )
    report_red = run_health_check(ctx_red)
    print(f"  Level: {report_red.level}")
    print(f"  Score: {report_red.score}%")

    print("\ninfra/health_monitor.py operational.")