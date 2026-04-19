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
    sources_attempted: int = 37
    sources_succeeded: int = 0
    sources_failed: list = field(default_factory=list)
    signals_fetched: int = 0
    signals_filtered: int = 0                 # legacy = dedupes + irrelevance
    signals_deduped: int = 0                  # url/headline dupes, not stored
    signals_irrelevance_filtered: int = 0     # stored with status=FILTERED
    signals_classified: int = 0
    signals_new: int = 0
    email_sent: bool = False
    email_sent_at: str = ""
    email_error: str = None
    email_deferred: bool = False              # split workflow: send happens in send_email.py
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
    """GS-1: Fetch Coverage. Proportional to active source count."""
    succeeded = ctx.sources_succeeded
    attempted = max(ctx.sources_attempted, 1)
    failed_names = ", ".join(ctx.sources_failed[:4]) if ctx.sources_failed else "none"

    pct = succeeded / attempted
    if pct >= 0.95:
        status = "GREEN"
    elif pct >= 0.85:
        status = "AMBER"
    else:
        status = "RED"

    return SubsystemResult(
        code="GS-1", name="Fetch Coverage",
        ideal=">=95%",
        actual=f"{succeeded}/{attempted} ({round(pct*100)}%)",
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
    """GS-3: Relevance Filter Rate.

    Measures the irrelevance-filter share of fresh (post-dedupe) items —
    i.e. classifier recall quality. Excludes dedupes from the denominator:
    dedupe rate runs 80-95% on Saturday/Sunday tape because feeds haven't
    refreshed, and conflating the two made GS-3 fire RED every weekend.
    """
    filtered = ctx.signals_irrelevance_filtered
    classified = ctx.signals_classified
    denom = filtered + classified

    if denom == 0:
        # No fresh items post-dedupe — can't evaluate; don't penalize.
        return SubsystemResult(
            code="GS-3", name="Relevance Filter",
            ideal="5-40% of fresh",
            actual=f"{ctx.signals_deduped} dedupes, 0 fresh",
            status="AMBER",
            note="nothing new after dedupe — typical on low-refresh windows",
        )

    rate = round((filtered / denom) * 100)

    # 5-40% is a wide-but-honest band. Too low = gate is missing irrelevant items
    # (poor recall). Too high = gate is dropping real signal (poor precision).
    if 5 <= rate <= 40:
        status = "GREEN"
    elif rate <= 60:
        status = "AMBER"
    else:
        status = "RED"

    return SubsystemResult(
        code="GS-3", name="Relevance Filter",
        ideal="5-40% of fresh",
        actual=f"{rate}% ({filtered}/{denom} fresh; {ctx.signals_deduped} dedupes)",
        status=status,
    )


def _check_ge1_distribution(ctx: RunContext) -> SubsystemResult:
    """GE-1: Alert Distribution across ACTIVE signals.

    Regime-conditional bands. The original fixed bands (R10-20 A40-60 G25-45)
    assumed a steady-state crisis distribution and fired RED in R0-R2 normal
    operation where most signals correctly decay GREEN and RED is a narrow
    escalation tier. Bands now scale with regime.
    """
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

    regime = (ctx.current_regime or "R0").upper()

    # Bands per regime: (red_lo, red_hi, amber_lo, amber_hi, green_lo, green_hi)
    REGIME_BANDS = {
        "R0": (0, 5,  0, 25, 70, 100),
        "R1": (0, 5,  0, 25, 70, 100),
        "R2": (2, 15, 15, 40, 45, 80),
        "R3": (10, 30, 40, 60, 25, 50),
        "R4": (10, 30, 40, 60, 25, 50),
    }
    r_lo, r_hi, a_lo, a_hi, g_lo, g_hi = REGIME_BANDS.get(regime, REGIME_BANDS["R0"])
    ideal = f"{regime}: R{r_lo}-{r_hi}% A{a_lo}-{a_hi}% G{g_lo}-{g_hi}%"

    if total == 0:
        return SubsystemResult("GE-1", "Alert Distribution",
                               ideal, "no signals", "AMBER")

    r_pct = round(red / total * 100)
    a_pct = round(amber / total * 100)
    g_pct = round(green / total * 100)

    bands_ok = 0
    if r_lo <= r_pct <= r_hi: bands_ok += 1
    if a_lo <= a_pct <= a_hi: bands_ok += 1
    if g_lo <= g_pct <= g_hi: bands_ok += 1

    if bands_ok == 3:
        status = "GREEN"
    elif bands_ok >= 2:
        status = "AMBER"
    else:
        status = "RED"

    return SubsystemResult(
        code="GE-1", name="Alert Distribution",
        ideal=ideal,
        actual=f"R{r_pct}% A{a_pct}% G{g_pct}%",
        status=status,
    )


def _check_ge2_deal_match() -> SubsystemResult:
    """GE-2: Deal Match Rate on RED/AMBER signals.

    Recalibrated to match the alpha-not-portfolio-review operating model:
    briefs are deal-free; deal overlay lives at the email-level off the
    44-deal Sheet, not on individual classifier tags. A high classifier
    match rate means over-matching, which contaminates alpha reads. A
    very low rate means the classifier has lost deal awareness. Target
    the middle band.
    """
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
                               "5-30%", "no RED/AMBER", "AMBER")

    rate = round(matched / red_amber * 100)

    # GREEN: classifier shows deal awareness without over-matching.
    # AMBER: either under-recognition (<5%) or drifting toward contamination (30-50%).
    # RED: severe under-recognition (0%) or over-matching (>50%).
    if 5 <= rate <= 30:
        status = "GREEN"
    elif rate == 0 or rate > 50:
        status = "RED"
    else:
        status = "AMBER"

    return SubsystemResult(
        code="GE-2", name="Deal Match Rate",
        ideal="5-30%",
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
    """GPi-2: HOT Deal Detection.

    Recalibrated: in R0-R2 normal operation, zero HOT deals is the
    expected baseline — HOT is a crisis-regime tier by design. Previously
    fired RED every run outside R3/R4. Now:
      R0-R2: 0 HOT is GREEN (expected); >=1 HOT is GREEN with an attention note;
             AMBER only if scoring produces no variance (all deals identical).
      R3-R4: >=1 HOT is GREEN; 0 HOT is RED (missed a crisis-tier deal).
    """
    regime = (ctx.current_regime or "R0").upper()
    scores = ctx.deal_scores

    hot = sum(1 for d in scores if getattr(d, "heat_level", "") == "HOT")
    warm_65 = sum(1 for d in scores
                  if getattr(d, "heat_level", "") == "WARM"
                  and getattr(d, "heat_score", 0) >= 65)

    has_metals_pending = any(
        "METALS_PENDING" in getattr(d, "data_flags", [])
        for d in scores
    )

    # Detect dead-scorer: all deals on identical heat_score (no differentiation).
    heat_values = {round(getattr(d, "heat_score", 0), 1) for d in scores}
    scorer_dead = len(scores) > 5 and len(heat_values) <= 1

    if regime in ("R3", "R4"):
        if hot >= 1:
            status, actual = "GREEN", f"{hot} HOT (regime {regime})"
        else:
            status, actual = "RED", f"0 HOT in crisis regime {regime}"
    else:
        if scorer_dead:
            status = "AMBER"
            actual = f"0 HOT | {len(scores)} deals on identical heat score — scorer suspect"
        elif hot >= 1:
            status = "GREEN"
            actual = f"{hot} HOT | attention: crisis-tier deal in {regime}"
        else:
            status = "GREEN"
            actual = f"0 HOT | {warm_65} WARM>65 — expected in {regime}"

    note = ""
    if has_metals_pending:
        note = "METALS_PENDING — commodity scores may be understated"

    return SubsystemResult(
        code="GPi-2", name="HOT Deal Detection",
        ideal=f"R0-R2: any; R3-R4: >=1 HOT",
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
    """GT-1: Email Delivery.

    Handles the split manual workflow: DRY_RUN suppresses the in-orchestrator
    send because the brief is hand-written and shipped via infra/send_email.py
    after. In that mode the health panel can't observe delivery; report
    'deferred' rather than the misleading 'failed: unknown'.
    """
    if ctx.email_sent:
        return SubsystemResult(
            code="GT-1", name="Email Delivery",
            ideal="Sent or deferred", actual=f"sent {ctx.email_sent_at or 'OK'}",
            status="GREEN",
        )
    if ctx.email_deferred:
        return SubsystemResult(
            code="GT-1", name="Email Delivery",
            ideal="Sent or deferred",
            actual="deferred — split workflow (send via infra/send_email.py)",
            status="GREEN",
        )
    return SubsystemResult(
        code="GT-1", name="Email Delivery",
        ideal="Sent or deferred",
        actual=f"failed: {ctx.email_error or 'unknown'}",
        status="RED",
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
        _check_ge1_distribution(ctx),
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