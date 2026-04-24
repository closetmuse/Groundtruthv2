# GT — GroundTruth Email Builder
# PRD Section 11.2 — 10-section daily email
# Assembles from all agent outputs. No live fetches at email time —
# all data pulled from SQLite groundtruth.db.
# Gmail OAuth pattern from V1 email_builder.py — proven approach.
# Last Updated: April 2026

import os
import re
import glob
import json
import base64
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

OUTPUT_DIR = r"C:\Users\nagar_7kszmu8\GroundTruth_v2\outputs"
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(r"C:\Users\nagar_7kszmu8\GroundTruth_v2\.env", override=True)

# ── CONFIG ────────────────────────────────────────────────────────────────────

DB_PATH          = r"C:\Users\nagar_7kszmu8\GroundTruth_v2\groundtruth.db"
GMAIL_SCOPES     = ["https://www.googleapis.com/auth/gmail.send"]
GMAIL_SENDER     = "GroundTruth <thybysproject@gmail.com>"
GMAIL_RECIPIENTS = [
    "mail2anurag@gmail.com",
    "nagarajan.sridhar@outlook.com",
]
CREDENTIALS_FILE = r"C:\Users\nagar_7kszmu8\GroundTruth_v2\gmail-credentials.json"
TOKEN_FILE       = r"C:\Users\nagar_7kszmu8\GroundTruth_v2\gmail-token.json"

# ── COLORS ────────────────────────────────────────────────────────────────────

BG       = "#0a0a0a"
TEXT     = "#e8e8e8"
RED      = "#ff4444"
AMBER    = "#ffaa00"
GREEN    = "#44bb44"
ACCENT   = "#4a9eff"
DIM      = "#666666"
BORDER   = "#222222"

# ── GMAIL AUTH ────────────────────────────────────────────────────────────────

def _get_gmail_service():
    """
    Authenticate with Gmail API using OAuth.

    First run opens browser for authorization. Subsequent runs use saved
    token. If token missing or expired, prints instruction and returns None.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("  Gmail dependencies not installed. Run: "
              "pip install google-auth google-auth-oauthlib "
              "google-api-python-client")
        return None

    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"  Token refresh failed: {e}")
                print(f"  Delete {TOKEN_FILE} and rerun to reauthorize.")
                return None
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"  Gmail credentials file not found: {CREDENTIALS_FILE}")
                print("  Copy gmail-credentials.json from V1 GroundTruth folder.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ── DB HELPERS ────────────────────────────────────────────────────────────────

def _get_latest_price_snapshot() -> dict:
    """
    Pull the most recent price snapshot from gs_price_snapshots.

    Returns dict with series_data, deltas, and breaches parsed from JSON.
    Returns empty dict if no snapshots exist.
    """
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT series_data, deltas_7d, deltas_30d, breaches, deltas_90d "
        "FROM gs_price_snapshots ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if not row:
        return {}

    return {
        "series":     json.loads(row[0] or "{}"),
        "deltas_7d":  json.loads(row[1] or "{}"),
        "deltas_30d": json.loads(row[2] or "{}"),
        "breaches":   json.loads(row[3] or "[]"),
        "deltas_90d": json.loads(row[4] or "{}") if row[4] else {},
    }


def _get_binary_events() -> list:
    """
    Pull all binary events from gt_binary_events table.

    Returns list of dicts with event fields.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM gt_binary_events ORDER BY deadline ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_latency_count() -> int:
    """Count of verification latency events logged."""
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute(
        "SELECT COUNT(*) FROM ge_latency_events"
    ).fetchone()[0]
    conn.close()
    return count


# ── SECTION BUILDERS ──────────────────────────────────────────────────────────

def _section_header(title: str) -> str:
    """Render a section header with subtle top border and small caps."""
    return (
        f'<tr><td style="padding:24px 0 8px 0;border-top:1px solid {BORDER};">'
        f'<span style="font-size:11px;letter-spacing:2px;'
        f'text-transform:uppercase;color:{DIM};">{title}</span>'
        f'</td></tr>'
    )


def _find_latest_brief_for_today() -> Path | None:
    """
    Find the most recent sector_briefs_YYYY-MM-DD_HHMMET*.md file for today.

    Recursive glob — looks in outputs/ and any subfolder (e.g. the
    chronological daily/2026-04/04-19/ layout established 2026-04-19).
    Returns the one with the latest modification time, or None if no brief
    exists for today yet.

    Note: returns None (placeholder rendered upstream) if the latest brief
    is from a prior day — stale briefs are not surfaced, so the email shows
    "brief pending" on the first capture of each day until I write one.
    """
    today = date.today().isoformat()
    pattern = os.path.join(OUTPUT_DIR, "**", f"sector_briefs_{today}_*.md")
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        return None
    latest = max(matches, key=lambda p: os.path.getmtime(p))
    return Path(latest)


_NUMERIC_CELL_RE = re.compile(
    r"^[+\-]?\$?\d[\d,.]*\s*"
    r"(%|bps|pp|x|d\d+|/\w+|\$/\w+|MMBtu|MWh|MT|ST|bbl|EUR/MWh|index)?$"
)


def _is_numeric_cell(cell: str) -> bool:
    """Heuristic: does this table cell hold a number (for right-align + monospace)?"""
    # Strip **bold** markers for the test only.
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", cell).strip()
    if s in ("", "—", "-", "n/a", "N/A", "—"):
        return True  # render aligned with numeric column
    return bool(_NUMERIC_CELL_RE.match(s))


def _markdown_to_email_html(md: str) -> str:
    """
    Minimal markdown → email-safe inline HTML converter.

    Handles the subset of markdown used in consolidated sector briefs:
    - ### headings and plain-text divider lines (====) as section breaks
    - **bold** runs
    - - bullet lists
    - blank-line paragraph breaks
    - `inline code` monospace spans
    - | pipe | tables | with auto-detected numeric columns

    Produces email-safe HTML with inline styles (no classes, no scripts).
    Deliberately limited — this is NOT a general-purpose markdown renderer.
    """
    lines = md.splitlines()
    out = []
    in_list = False
    paragraph_buf = []
    table_buf = []  # list of list-of-cells; first row is header

    def flush_paragraph():
        nonlocal paragraph_buf
        if paragraph_buf:
            text = " ".join(paragraph_buf).strip()
            if text:
                out.append(
                    f'<p style="margin:6px 0;font-size:13px;'
                    f'line-height:1.55;color:{TEXT};'
                    f'text-align:justify;hyphens:auto;">{_inline_md(text)}</p>'
                )
            paragraph_buf = []

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def flush_table():
        nonlocal table_buf
        if not table_buf:
            return
        # Header is the first buffered row.
        header = table_buf[0]
        body_rows = table_buf[1:]
        n_cols = max([len(header)] + [len(r) for r in body_rows]) if body_rows else len(header)

        # Determine per-column alignment from body cells (right for numeric, left otherwise).
        align = []
        for ci in range(n_cols):
            if not body_rows:
                align.append("left")
                continue
            col_cells = [r[ci] if ci < len(r) else "" for r in body_rows]
            num_count = sum(1 for c in col_cells if _is_numeric_cell(c))
            align.append("right" if num_count >= len(col_cells) / 2 else "left")

        HDR_CELL = (
            f"font-size:10px;letter-spacing:1px;color:{DIM};"
            f"text-transform:uppercase;border-bottom:1px solid {BORDER};"
            f"padding:6px 10px 6px 0;"
        )
        out.append(
            f'<table role="presentation" style="width:100%;'
            f'border-collapse:collapse;margin:8px 0 14px 0;">'
        )
        # Header
        hdr_cells = []
        for ci in range(n_cols):
            cell = header[ci] if ci < len(header) else ""
            hdr_cells.append(
                f'<td style="{HDR_CELL}text-align:{align[ci]};">'
                f'{_inline_md(cell)}</td>'
            )
        out.append(f'<tr>{"".join(hdr_cells)}</tr>')
        # Body
        for r in body_rows:
            row_cells = []
            for ci in range(n_cols):
                cell = r[ci] if ci < len(r) else ""
                num = _is_numeric_cell(cell)
                font = (
                    "font-family:monospace;font-size:12px;"
                    if num else "font-size:13px;"
                )
                row_cells.append(
                    f'<td style="padding:4px 10px 4px 0;color:{TEXT};'
                    f'{font}text-align:{align[ci]};'
                    f'border-bottom:1px solid {BORDER};">'
                    f'{_inline_md(cell)}</td>'
                )
            out.append(f'<tr>{"".join(row_cells)}</tr>')
        out.append('</table>')
        table_buf = []

    for raw in lines:
        line = raw.rstrip()

        # Markdown table row — buffer for one combined <table> block.
        # Must come BEFORE other handlers because table rows start with '|'
        # which doesn't collide, but tables must flush other state first.
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            flush_list()
            # Skip the |---|---| divider row.
            if re.match(r"^\|[\s\-:|]+\|$", stripped):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            table_buf.append(cells)
            continue
        # Any non-table line ends a table block.
        if table_buf:
            flush_table()

        # Skip plain divider lines (the ==== bars)
        if re.match(r"^=+\s*$", line):
            flush_paragraph()
            flush_list()
            continue

        # Tape tone footer line — render in small dim caps
        if re.match(r"^Tape tone \d{4}-\d{2}-\d{2}:", line):
            flush_paragraph()
            flush_list()
            out.append(
                f'<p style="margin:16px 0 4px 0;font-size:11px;'
                f'letter-spacing:1px;text-transform:uppercase;color:{DIM};">'
                f'{_inline_md(line)}</p>'
            )
            continue

        # GroundTruth provenance footer (last line)
        if line.startswith("GroundTruth  |"):
            flush_paragraph()
            flush_list()
            out.append(
                f'<p style="margin:12px 0 4px 0;font-size:10px;'
                f'color:{DIM};">{_inline_md(line)}</p>'
            )
            continue

        # Heading: ###
        m = re.match(r"^###\s+(.+)$", line)
        if m:
            flush_paragraph()
            flush_list()
            out.append(
                f'<h4 style="margin:14px 0 6px 0;font-size:13px;'
                f'font-weight:bold;color:{ACCENT};">{_inline_md(m.group(1))}</h4>'
            )
            continue

        # Heading: ##
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            flush_paragraph()
            flush_list()
            out.append(
                f'<h3 style="margin:16px 0 8px 0;font-size:14px;'
                f'font-weight:bold;color:{TEXT};">{_inline_md(m.group(1))}</h3>'
            )
            continue

        # Heading: # (rare in briefs, but handle)
        m = re.match(r"^#\s+(.+)$", line)
        if m:
            flush_paragraph()
            flush_list()
            out.append(
                f'<h2 style="margin:18px 0 8px 0;font-size:15px;'
                f'font-weight:bold;color:{TEXT};">{_inline_md(m.group(1))}</h2>'
            )
            continue

        # Bullet list item
        m = re.match(r"^-\s+(.+)$", line)
        if m:
            flush_paragraph()
            if not in_list:
                out.append(
                    f'<ul style="margin:6px 0 6px 0;padding-left:18px;'
                    f'font-size:13px;line-height:1.55;color:{TEXT};'
                    f'text-align:justify;hyphens:auto;">'
                )
                in_list = True
            out.append(f"<li style=\"margin:3px 0;\">{_inline_md(m.group(1))}</li>")
            continue

        # Blank line → paragraph break
        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        # Accumulate into current paragraph
        paragraph_buf.append(line)

    flush_paragraph()
    flush_list()
    flush_table()

    return "\n".join(out)


def _inline_md(text: str) -> str:
    """Render inline **bold** and `code` within a single line of text."""
    # Escape HTML-unsafe characters first (minimal — briefs are trusted content)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # **bold**
    text = re.sub(
        r"\*\*(.+?)\*\*",
        rf'<strong style="color:{TEXT};">\1</strong>',
        text,
    )
    # `inline code`
    text = re.sub(
        r"`([^`]+)`",
        rf'<code style="font-family:monospace;font-size:11px;color:{ACCENT};">\1</code>',
        text,
    )
    return text


def _section_1_brief(run_summary: dict) -> str:
    """
    Section 1: Consolidated Sector Brief.

    Looks for the most recent sector_briefs_YYYY-MM-DD_HHMMET*.md file for
    today in outputs/. If found, renders it as the first section of the email.
    If not found (i.e., no brief written yet for today — typically the first
    capture of the day before manual synthesis), renders a compact placeholder
    telling the reader the brief is pending.

    This is the new dominant section — the reason to open the email. The
    remaining sections below (2-11) are the system-monitoring rollup.
    """
    brief_path = _find_latest_brief_for_today()

    if brief_path is None:
        return (
            _section_header("1. Sector Brief") +
            f'<tr><td style="padding:4px 0 12px 0;font-size:12px;'
            f'color:{DIM};line-height:1.55;">'
            f'<em>Brief pending — manual synthesis step. '
            f'Will be included in the next email after the brief is written.</em>'
            f'<br><br>'
            f'In the meantime, see sections 2-11 below for the full capture '
            f'monitoring view — regime status, prices, RED/AMBER signals, '
            f'deal watch, binary events, scoreboard, and system health.'
            f'</td></tr>'
        )

    try:
        md = brief_path.read_text(encoding="utf-8")
    except Exception as e:
        return (
            _section_header("1. Sector Brief") +
            f'<tr><td style="padding:4px 0 12px 0;font-size:12px;color:{AMBER};">'
            f'Brief file found at {brief_path.name} but could not be read: {e}'
            f'</td></tr>'
        )

    brief_html = _markdown_to_email_html(md)

    return (
        _section_header(f"1. Sector Brief — {brief_path.name}") +
        f'<tr><td style="padding:4px 0 12px 0;">'
        f'{brief_html}'
        f'</td></tr>'
    )


def _section_2_regime(run_summary: dict) -> str:
    """
    Section 2: Regime + Binary Events.

    Current regime label, days into crisis, and binary event deadlines.
    (Previously Section 1 before the consolidated brief was added as Section 1.)
    """
    regime = run_summary.get("regime", "R0 — Compound Stress")
    crisis_day = run_summary.get("crisis_day", 42)

    events = _get_binary_events()
    event_lines = ""
    if events:
        for ev in events:
            days_left = ""
            try:
                dl = datetime.strptime(ev["deadline"], "%Y-%m-%d").date()
                days_left = f" ({(dl - date.today()).days}d remaining)"
            except Exception:
                pass
            status_color = GREEN if ev.get("status") == "RESOLVED" else AMBER
            event_lines += (
                f'<div style="padding:2px 0;color:{status_color};">'
                f'  {ev.get("name", "")} — {ev.get("deadline", "")}{days_left}'
                f'</div>'
            )
    else:
        # Hardcoded active events until gt_binary_events populated
        event_lines = (
            f'<div style="padding:2px 0;color:{AMBER};">FOMC April 28-29 — hold or hike</div>'
            f'<div style="padding:2px 0;color:{AMBER};">FERC Large Load Rule — April 30</div>'
            f'<div style="padding:2px 0;color:{AMBER};">OBBBA BOC Deadline — July 4</div>'
        )

    return (
        _section_header("2. Regime + Binary Events") +
        f'<tr><td style="padding:4px 0 12px 0;">'
        f'<div style="font-size:16px;font-weight:bold;color:{RED};">'
        f'{regime} — Day {crisis_day}</div>'
        f'{event_lines}'
        f'</td></tr>'
    )


def _section_2_prices() -> str:
    """
    Section 2: Price Snapshot.

    All series with column headers, 7d/30d/90d deltas, delta color logic,
    and divergence footnotes when credit markets lag commodity stress.
    """
    snap = _get_latest_price_snapshot()
    series = snap.get("series", {})
    d7 = snap.get("deltas_7d", {})
    d30 = snap.get("deltas_30d", {})
    d90 = snap.get("deltas_90d", {})
    breaches = {b["field"] for b in snap.get("breaches", [])}

    # Series classification for delta color and suffix logic
    SPREAD_FIELDS = {"bbb_oas_bps", "hy_spread_bps"}
    RATE_FIELDS   = {"ust_10y_pct", "ust_2y_pct", "ust_5y_pct",
                     "ust_30y_pct", "sofr_pct"}
    # Everything else is commodity/price (oil, gas, power, fx)

    # Column widths for alignment
    COL_LABEL   = "padding:3px 12px 3px 0;min-width:100px;"
    COL_VALUE   = "padding:3px 12px 3px 0;min-width:110px;"
    COL_DELTA   = "padding:3px 8px;min-width:80px;text-align:right;"
    HDR_STYLE   = f"padding:4px 8px 6px 0;font-size:10px;letter-spacing:1px;color:{DIM};text-transform:uppercase;border-bottom:1px solid {BORDER};"

    display_order = [
        ("wti_usd_bbl",                "WTI Crude"),
        ("brent_usd_bbl",              "Brent Crude"),
        ("henry_hub_usd_mmbtu",        "Henry Hub"),
        ("ust_10y_pct",                "UST 10Y"),
        ("sofr_pct",                   "SOFR"),
        ("bbb_oas_bps",                "BBB OAS"),
        ("hy_spread_bps",              "HY Spread"),
        ("ercot_hb_north_da",          "ERCOT North"),
        ("ercot_hb_west_da",           "ERCOT West"),
        ("ercot_hb_houston_da",        "ERCOT Houston"),
        ("miso_illinoishub_da",        "MISO Illinois"),
        ("nyiso_nyc_da",               "NYISO NYC"),
        ("caiso_th_sp15_gen-apnd_da",  "CAISO SP15"),
        ("isone_hinternal_hub_da",     "ISO-NE Hub"),
        ("aluminum_usd_mt",            "Aluminum"),
        ("copper_usd_mt",              "Copper"),
        ("steel_hrc_usd_st",           "Steel HRC (CME)"),
        ("steel_hrc_index",            "Steel HRC (PPI)"),
    ]

    # Column header row
    header_row = (
        f'<tr>'
        f'<td style="{HDR_STYLE}{COL_LABEL}">Series</td>'
        f'<td style="{HDR_STYLE}{COL_VALUE}">Current</td>'
        f'<td style="{HDR_STYLE}{COL_DELTA}">7d</td>'
        f'<td style="{HDR_STYLE}{COL_DELTA}">30d</td>'
        f'<td style="{HDR_STYLE}{COL_DELTA}">90d</td>'
        f'</tr>'
    )

    rows = header_row
    spread_footnote = ""

    # Check WTI 30d for divergence detection
    wti_30d = d30.get("wti_usd_bbl")
    wti_30d_positive = isinstance(wti_30d, (int, float)) and wti_30d > 0

    def _delta_color(val, field):
        """Determine color for a delta value based on series type."""
        if val is None or val == 0:
            return DIM
        is_spread = field in SPREAD_FIELDS
        is_rate = field in RATE_FIELDS
        if is_spread:
            # Spread widening (positive) = stress pricing in = normal
            # Spread tightening (negative) in stress regime = lagging = red
            return RED if val < 0 else TEXT
        elif is_rate:
            # Rate rising = stress, show red; falling = relief, show green
            return RED if val > 0 else GREEN
        else:
            # Commodity/price: rising = stress red; falling = relief green
            return RED if val > 0 else GREEN

    def _fmt_delta(val, field):
        """Format a delta value with appropriate suffix and color."""
        if val is None:
            return f'<span style="color:{DIM};">&mdash;</span>'
        is_spread = field in SPREAD_FIELDS
        is_rate = field in RATE_FIELDS
        color = _delta_color(val, field)
        if is_spread or is_rate:
            txt = f"{val:+.2f}pp"
        else:
            txt = f"{val:+.1f}"
        return f'<span style="color:{color};">{txt}</span>'

    for field, label in display_order:
        data = series.get(field)
        if not data:
            continue
        val = data.get("value", "N/A")
        unit = data.get("unit", "")
        delta7 = d7.get(field)
        delta30 = d30.get(field)
        delta90 = d90.get(field)

        is_spread = field in SPREAD_FIELDS
        is_breached = field in breaches
        is_stale = bool(data.get("stale")) or data.get("staleness_days", 0) > 2
        stale_days = data.get("staleness_days", 0)
        stale_flag_html = (
            f' <span style="color:{AMBER};font-weight:bold;font-size:10px;">'
            f'STALE {stale_days}d</span>'
            if is_stale else ""
        )

        # Value display
        if is_spread:
            val_display = f"{val}%"
            val_color = TEXT
            # Divergence color override for spread value cell
            d30_val = delta30 if isinstance(delta30, (int, float)) else 0
            d90_val = delta90 if isinstance(delta90, (int, float)) else 0

            if d30_val < 0 and d90_val < 0:
                val_color = RED
                if "90 days" not in spread_footnote:
                    spread_footnote = (
                        f'<div style="padding:6px 0 2px 0;font-size:11px;color:{RED};">'
                        f'&#9888; IG credit has not priced R0 stress over 90 days '
                        f'&mdash; latency window open</div>'
                    )
            elif d30_val < 0 and wti_30d_positive:
                val_color = AMBER
                if not spread_footnote:
                    spread_footnote = (
                        f'<div style="padding:6px 0 2px 0;font-size:11px;color:{AMBER};">'
                        f'&#9888; Credit spreads compressing while commodity stress '
                        f'accelerates &mdash; verification latency signal active</div>'
                    )
        else:
            val_display = f"{val} {unit}"
            val_color = RED if is_breached else TEXT

        breach_flag = (
            f' <span style="color:{RED};font-weight:bold;">BREACHED</span>'
            if is_breached else ""
        )

        # 90d column: populated for spreads and rates, dash for others
        if is_spread or field in RATE_FIELDS:
            d90_cell = _fmt_delta(delta90, field)
        else:
            d90_cell = f'<span style="color:{DIM};">&mdash;</span>'

        rows += (
            f'<tr>'
            f'<td style="{COL_LABEL}color:{DIM};font-size:12px;">{label}</td>'
            f'<td style="{COL_VALUE}color:{val_color};font-size:13px;font-weight:bold;">'
            f'{val_display}{breach_flag}{stale_flag_html}</td>'
            f'<td style="{COL_DELTA}font-size:11px;">{_fmt_delta(delta7, field)}</td>'
            f'<td style="{COL_DELTA}font-size:11px;">{_fmt_delta(delta30, field)}</td>'
            f'<td style="{COL_DELTA}font-size:11px;">{d90_cell}</td>'
            f'</tr>'
        )

    return (
        _section_header("3. Price Snapshot") +
        f'<tr><td><table style="width:100%;border-collapse:collapse;">{rows}</table>'
        f'{spread_footnote}</td></tr>'
    )


def _section_3_pattern(encyclopedia_match: dict) -> str:
    """
    Section 3: Historical Pattern Match.

    3-line block from gi/encyclopedia.py build_pattern_match_block().
    """
    try:
        from gi.encyclopedia import build_pattern_match_block
        block = build_pattern_match_block(encyclopedia_match)
    except Exception:
        block = "Pattern match unavailable — encyclopedia not loaded."

    lines = block.replace("\n", "<br>")
    return (
        _section_header("4. Historical Pattern Match") +
        f'<tr><td style="padding:4px 0 12px 0;font-size:13px;'
        f'color:{ACCENT};line-height:1.6;">{lines}</td></tr>'
    )


def _section_4_red(signals: list) -> str:
    """
    Section 4: RED Signals.

    Signals with weighted_score >= 75 or alert_level RED. Max 5.
    Red left border. Headline, mechanism, deal, action deadline.
    """
    red_signals = [
        s for s in signals
        if _get_field(s, "alert_level") == "RED"
        or (_get_field(s, "weighted_score") and float(_get_field(s, "weighted_score", 0)) >= 75)
    ][:5]

    if not red_signals:
        return (
            _section_header("5. RED Signals") +
            f'<tr><td style="padding:4px 0;color:{DIM};font-style:italic;">'
            f'No RED signals this run.</td></tr>'
        )

    rows = ""
    for s in red_signals:
        headline = _get_field(s, "headline", "")
        second_order = _get_field(s, "second_order", "")
        mechanism = second_order.split(".")[0] + "." if "." in second_order else second_order[:150]
        deals = _get_field(s, "affected_deals", "")
        try:
            deal_list = json.loads(deals) if deals else []
        except Exception:
            deal_list = []
        deal_str = f'<span style="color:{ACCENT};">Deals: {", ".join(deal_list)}</span>' if deal_list else ""
        score = _get_field(s, "weighted_score", "")
        score_str = f' [{score}]' if score else ""

        rows += (
            f'<tr><td style="padding:8px 0 8px 12px;border-left:3px solid {RED};">'
            f'<div style="font-size:13px;font-weight:bold;color:{TEXT};">'
            f'{headline}{score_str}</div>'
            f'<div style="font-size:12px;color:{DIM};padding-top:4px;">{mechanism}</div>'
            f'{f"<div style=&quot;font-size:11px;padding-top:3px;&quot;>{deal_str}</div>" if deal_str else ""}'
            f'</td></tr>'
        )

    return _section_header("5. RED Signals") + rows


def _section_5_amber(signals: list) -> str:
    """
    Section 5: AMBER Signals.

    Signals with weighted_score 45-74 or alert_level AMBER. Max 8.
    Amber left border. Headline + one-line watch item.
    """
    amber_signals = [
        s for s in signals
        if _get_field(s, "alert_level") == "AMBER"
        or (45 <= float(_get_field(s, "weighted_score", 0) or 0) < 75)
    ][:8]

    if not amber_signals:
        return (
            _section_header("6. AMBER Signals") +
            f'<tr><td style="padding:4px 0;color:{DIM};font-style:italic;">'
            f'No AMBER signals this run.</td></tr>'
        )

    rows = ""
    for s in amber_signals:
        headline = _get_field(s, "headline", "")
        second_order = _get_field(s, "second_order", "")
        watch = second_order.split(".")[0] + "." if "." in second_order else second_order[:120]

        rows += (
            f'<tr><td style="padding:6px 0 6px 12px;border-left:3px solid {AMBER};">'
            f'<div style="font-size:13px;color:{TEXT};">{headline}</div>'
            f'<div style="font-size:11px;color:{DIM};padding-top:2px;">{watch}</div>'
            f'</td></tr>'
        )

    return _section_header("6. AMBER Signals") + rows


def _section_6_portfolio() -> str:
    """
    Section 6: Deal Watch — GPi live deal exposure scores.

    Shows HOT/WARM/COOL deal breakdown from gpi/pipeline_agent.py.
    Falls back to placeholder if GPi not available.
    """
    try:
        from gpi.pipeline_agent import get_deal_watch_block
        block = get_deal_watch_block()
        lines = block.replace("\n", "<br>")
        return (
            _section_header("7. Deal Watch") +
            f'<tr><td style="padding:4px 0 12px 0;font-size:12px;'
            f'color:{TEXT};line-height:1.7;font-family:monospace;">'
            f'{lines}</td></tr>'
        )
    except Exception:
        return (
            _section_header("7. Deal Watch") +
            f'<tr><td style="padding:8px 0;color:{DIM};font-style:italic;opacity:0.4;">'
            f'GPi agent loading — deal exposure scores will appear here.</td></tr>'
        )


def _section_7_prospects() -> str:
    """Section 7: Prospect Watch — Phase 5 placeholder."""
    return (
        _section_header("8. Prospect Watch") +
        f'<tr><td style="padding:8px 0;color:{DIM};font-style:italic;opacity:0.4;">'
        f'GC agent active at Phase 5 — compliance gate required before '
        f'activation.</td></tr>'
    )


def _section_8_binary() -> str:
    """
    Section 8: Binary Events Countdown.

    Table of events with deadline, days remaining, linked deals,
    and encyclopedia trigger.
    """
    events = _get_binary_events()

    if not events:
        # Hardcoded until gt_binary_events populated
        hardcoded = [
            ("FOMC April 28-29", "2026-04-28", "All floating rate deals",
             "E08 Volcker if hike"),
            ("FERC Large Load Rule", "2026-04-30", "GT-108 SB Energy Ohio",
             None),
            ("OBBBA BOC Deadline", "2026-07-04", "Project Vega",
             None),
        ]
        rows = ""
        for name, deadline, deals, trigger in hardcoded:
            try:
                dl = datetime.strptime(deadline, "%Y-%m-%d").date()
                days = (dl - date.today()).days
            except Exception:
                days = "?"
            trigger_str = f'<span style="color:{RED};">{trigger}</span>' if trigger else ""
            rows += (
                f'<tr>'
                f'<td style="padding:4px 8px 4px 0;font-size:12px;color:{TEXT};">{name}</td>'
                f'<td style="padding:4px 8px;font-size:12px;color:{AMBER};">{deadline}</td>'
                f'<td style="padding:4px 8px;font-size:12px;color:{TEXT};">{days}d</td>'
                f'<td style="padding:4px 8px;font-size:11px;color:{DIM};">{deals}</td>'
                f'<td style="padding:4px 8px;font-size:11px;">{trigger_str}</td>'
                f'</tr>'
            )
        return (
            _section_header("9. Binary Events Countdown") +
            f'<tr><td><table style="width:100%;border-collapse:collapse;">{rows}</table></td></tr>'
        )

    rows = ""
    for ev in events:
        days = "?"
        try:
            dl = datetime.strptime(ev["deadline"], "%Y-%m-%d").date()
            days = (dl - date.today()).days
        except Exception:
            pass
        trigger = ev.get("encyclopedia_trigger", "")
        trigger_str = f'<span style="color:{RED};">{trigger}</span>' if trigger else ""
        deals = ev.get("linked_deals", "")
        try:
            deal_list = ", ".join(json.loads(deals)) if deals else ""
        except Exception:
            deal_list = str(deals)

        rows += (
            f'<tr>'
            f'<td style="padding:4px 8px 4px 0;font-size:12px;color:{TEXT};">{ev.get("name","")}</td>'
            f'<td style="padding:4px 8px;font-size:12px;color:{AMBER};">{ev.get("deadline","")}</td>'
            f'<td style="padding:4px 8px;font-size:12px;color:{TEXT};">{days}d</td>'
            f'<td style="padding:4px 8px;font-size:11px;color:{DIM};">{deal_list}</td>'
            f'<td style="padding:4px 8px;font-size:11px;">{trigger_str}</td>'
            f'</tr>'
        )

    return (
        _section_header("9. Binary Events Countdown") +
        f'<tr><td><table style="width:100%;border-collapse:collapse;">{rows}</table></td></tr>'
    )


def _section_9_scoreboard() -> str:
    """
    Section 9: Alpha Scoreboard Delta.

    Total alerts, open, resolved, hit rate. Pulls from ge_latency_events.
    Shows zeros if empty.
    """
    latency_count = _get_latency_count()

    conn = sqlite3.connect(DB_PATH)
    total_signals = conn.execute(
        "SELECT COUNT(*) FROM gs_signals WHERE status='ACTIVE'"
    ).fetchone()[0]
    red_count = conn.execute(
        "SELECT COUNT(*) FROM gs_signals WHERE alert_level='RED' AND status='ACTIVE'"
    ).fetchone()[0]
    conn.close()

    return (
        _section_header("10. Alpha Scoreboard") +
        f'<tr><td style="padding:4px 0 12px 0;font-size:12px;line-height:1.8;">'
        f'<span style="color:{TEXT};">Total active alerts: {total_signals}</span><br>'
        f'<span style="color:{RED};">RED alerts open: {red_count}</span><br>'
        f'<span style="color:{ACCENT};">Latency events logged: {latency_count}</span><br>'
        f'<span style="color:{DIM};">Hit rate: pending — requires 10+ resolved events</span>'
        f'</td></tr>'
    )


def _section_10_status(run_summary: dict) -> str:
    """
    Section 10: System Health.

    Full health dashboard with 8 subsystem checks.
    Falls back to plain text if health report not available.
    """
    # Try to get health report HTML
    health_html = run_summary.get("_health_html")
    if health_html:
        return (
            _section_header("11. System Health") +
            f'<tr><td style="padding:4px 0 12px 0;">{health_html}</td></tr>'
        )

    # Fallback: plain text
    return (
        _section_header("11. System Status") +
        f'<tr><td style="padding:4px 0 12px 0;font-size:11px;color:{DIM};line-height:1.8;">'
        f'Sources fetched: {run_summary.get("sources_fetched", 0)}<br>'
        f'Signals classified: {run_summary.get("signals_classified", 0)}<br>'
        f'RED: {run_summary.get("red_count", 0)} | '
        f'AMBER: {run_summary.get("amber_count", 0)} | '
        f'GREEN: {run_summary.get("green_count", 0)}<br>'
        f'Runtime: {run_summary.get("runtime_seconds", 0)}s<br>'
        f'Failures: {run_summary.get("failures", "none")}<br>'
        f'Next run: {run_summary.get("next_run", "manual trigger")}'
        f'</td></tr>'
    )


# ── FIELD HELPER ──────────────────────────────────────────────────────────────

def _get_field(signal, field, default=""):
    """
    Get a field from a Signal object or dict, with fallback default.

    Handles both SQLModel Signal objects and plain dicts.
    """
    if isinstance(signal, dict):
        return signal.get(field, default)
    return getattr(signal, field, default)


# ── MASTER BUILDERS ───────────────────────────────────────────────────────────

def build_email(signals: list, encyclopedia_match: dict,
                run_summary: dict) -> str:
    """
    Assemble all 10 sections into a single HTML email string.

    Pulls price snapshot from gs_price_snapshots (latest row). Pulls
    binary events from gt_binary_events. All data from SQLite — no
    live fetches at email time.

    Args:
        signals: List of Signal objects or dicts from this run.
        encyclopedia_match: Dict from match_signals_to_encyclopedia().
        run_summary: Dict with runtime stats (regime, counts, failures).

    Returns:
        Complete HTML string ready for email sending.
    """
    sections = (
        _section_1_brief(run_summary) +
        _section_2_regime(run_summary) +
        _section_2_prices() +
        _section_3_pattern(encyclopedia_match) +
        _section_4_red(signals) +
        _section_5_amber(signals) +
        _section_6_portfolio() +
        _section_7_prospects() +
        _section_8_binary() +
        _section_9_scoreboard() +
        _section_10_status(run_summary)
    )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:{BG};font-family:system-ui,-apple-system,Arial,sans-serif;">
<table role="presentation" style="width:100%;background:{BG};">
<tr><td align="center" style="padding:20px 10px;">
<table role="presentation" style="max-width:680px;width:100%;background:{BG};color:{TEXT};">

<!-- Header -->
<tr><td style="padding:16px 0 8px 0;">
<span style="font-size:20px;font-weight:bold;color:{TEXT};letter-spacing:1px;">GROUNDTRUTH</span>
<span style="font-size:12px;color:{DIM};padding-left:12px;">{datetime.now().strftime('%B %d, %Y %H:%M ET')}</span>
</td></tr>

{sections}

<!-- Footer -->
<tr><td style="padding:24px 0 16px 0;border-top:1px solid {BORDER};text-align:center;">
<span style="font-size:10px;color:{DIM};">
GroundTruth V2 — PRD Schema v2.0 | Internal Use Only<br>
SC Compliance: Public sources only. No client data in system.
</span>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    return html


def build_email_brief_only(brief_path: Path | None = None) -> str:
    """
    Brief-only email build — renders the latest sector brief as the ENTIRE
    email body, no auto-generated sections. Added 2026-04-23 when Sri
    restarted emails and asked for brief-only content.

    If brief_path is None, uses _find_latest_brief_for_today(). If no brief
    exists for today, returns an HTML placeholder explaining the situation.
    """
    if brief_path is None:
        brief_path = _find_latest_brief_for_today()

    if brief_path is None:
        body_html = (
            f'<p style="font-size:13px;color:{DIM};line-height:1.55;">'
            f'<em>No sector brief found for today. Email suppressed until a '
            f'brief is written. Run <code>python infra/run_manual.py</code> '
            f'then write the brief, then <code>python infra/send_email.py '
            f'--brief-only</code>.</em></p>'
        )
        brief_name = "pending"
    else:
        try:
            md = brief_path.read_text(encoding="utf-8")
            body_html = _markdown_to_email_html(md)
            brief_name = brief_path.name
        except Exception as e:
            body_html = (
                f'<p style="font-size:13px;color:{AMBER};">'
                f'Brief file found at {brief_path.name} but could not be '
                f'read: {e}</p>'
            )
            brief_name = brief_path.name

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:{BG};font-family:system-ui,-apple-system,Arial,sans-serif;">
<table role="presentation" style="width:100%;background:{BG};">
<tr><td align="center" style="padding:20px 10px;">
<table role="presentation" style="max-width:720px;width:100%;background:{BG};color:{TEXT};">

<!-- Header -->
<tr><td style="padding:16px 0 8px 0;border-bottom:1px solid {BORDER};">
<span style="font-size:20px;font-weight:bold;color:{TEXT};letter-spacing:1px;">GROUNDTRUTH</span>
<span style="font-size:12px;color:{DIM};padding-left:12px;">{datetime.now().strftime('%B %d, %Y %H:%M ET')}</span>
<span style="font-size:11px;color:{DIM};float:right;padding-top:4px;">{brief_name}</span>
</td></tr>

<!-- Brief body -->
<tr><td style="padding:16px 0;">
{body_html}
</td></tr>

<!-- Footer -->
<tr><td style="padding:24px 0 16px 0;border-top:1px solid {BORDER};text-align:center;">
<span style="font-size:10px;color:{DIM};">
GroundTruth V2 | Brief-only delivery | Internal Use Only<br>
SC Compliance: Public sources only. No client data in system.
</span>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return html


def build_subject_brief_only(brief_path: Path | None = None) -> str:
    """
    Subject for brief-only email. Per the v2 brief template (2026-04-24),
    the Tape Tone line from the executive card is the email subject.

    Extraction priority:
      1. v2 executive-card line:  `TAPE TONE : <text>`
      2. v1 EOD-only line:        `**TAPE TONE (EOD...): <text>**`
      3. Fallback: generic.
    """
    if brief_path is None:
        brief_path = _find_latest_brief_for_today()
    date_str = datetime.now().strftime("%b %d")
    if brief_path is None:
        return f"GroundTruth | {date_str} | Brief pending"
    try:
        md = brief_path.read_text(encoding="utf-8")
        slot_match = re.search(r"(AM|MIDDAY|midday|PM|EOD)", md[:500])
        slot = slot_match.group(1).upper() if slot_match else "brief"

        # v2 executive-card tape tone — single line starting with TAPE TONE
        m = re.search(r"^\s*TAPE\s*TONE\s*:\s*(.+?)\s*$", md, re.MULTILINE)
        if m is None:
            # v1 EOD format — bolded tape tone at bottom of brief
            m = re.search(r"\*\*TAPE TONE[^:]*:\s*(.+?)\.?\*\*", md)
        tape_tone = m.group(1).strip() if m else "brief delivered"
        # Trim trailing punctuation other than ? ! for subject aesthetics
        tape_tone = tape_tone.rstrip(". ")
        if len(tape_tone) > 100:
            tape_tone = tape_tone[:97] + "..."
        return f"GroundTruth | {date_str} | {slot} | {tape_tone}"
    except Exception:
        return f"GroundTruth | {date_str} | {brief_path.name}"


def build_subject(signals: list, run_summary: dict) -> str:
    """
    Build the email subject line.

    Format: GroundTruth | [DATE] | [N] signals | [N] RED alerts | WTI $[price]

    Args:
        signals: List of signals from this run.
        run_summary: Dict with runtime stats.

    Returns:
        Subject line string.
    """
    date_str = datetime.now().strftime("%b %d")
    n_signals = len(signals)
    n_red = sum(
        1 for s in signals
        if _get_field(s, "alert_level") == "RED"
    )

    # Get WTI from latest snapshot
    snap = _get_latest_price_snapshot()
    wti_data = snap.get("series", {}).get("wti_usd_bbl", {})
    wti_str = f"WTI ${wti_data.get('value', 'N/A')}" if wti_data else ""

    parts = [
        "GroundTruth",
        date_str,
        f"{n_signals} signals",
        f"{n_red} RED alerts",
    ]
    if wti_str:
        parts.append(wti_str)

    return " | ".join(parts)


def send_email(html: str, subject: str) -> bool:
    """
    Send HTML email via Gmail OAuth.

    Uses exact credentials pattern from V1 email_builder.py. Token
    refresh handled automatically. If token missing or expired, prints
    instruction — does not crash.

    Args:
        html: Complete HTML email body.
        subject: Email subject line.

    Returns:
        True if sent successfully, False otherwise.
    """
    service = _get_gmail_service()
    if not service:
        print("  Gmail service unavailable — email not sent.")
        return False

    try:
        message = MIMEMultipart("alternative")
        message["to"] = ", ".join(GMAIL_RECIPIENTS)
        message["from"] = GMAIL_SENDER
        message["subject"] = subject

        plain = MIMEText(
            "GroundTruth daily digest — view in HTML-capable email client.",
            "plain",
        )
        html_part = MIMEText(html, "html")
        message.attach(plain)
        message.attach(html_part)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

        print(f"  Email sent to {', '.join(GMAIL_RECIPIENTS)}")
        return True

    except Exception as e:
        print(f"  Email send failed: {e}")
        return False


def send_digest(signals: list, encyclopedia_match: dict,
                run_summary: dict) -> bool:
    """
    Orchestrate the full email send: build HTML, build subject, send.

    Args:
        signals: List of Signal objects or dicts from this run.
        encyclopedia_match: Dict from match_signals_to_encyclopedia().
        run_summary: Dict with runtime stats.

    Returns:
        True if email sent successfully, False otherwise.
    """
    print("\nBuilding email digest...")
    html = build_email(signals, encyclopedia_match, run_summary)
    subject = build_subject(signals, run_summary)
    print(f"  Subject: {subject}")
    print(f"  HTML length: {len(html)} chars")
    return send_email(html, subject)


# ── DRIVE DIGEST ──────────────────────────────────────────────────────────────

def save_digest_to_drive(html_content: str,
                         credentials_path: str = None) -> str:
    """
    Save the email HTML to a fixed file in Google Drive.
    File is created on first run, overwritten on every subsequent run.
    Returns the permanent shareable URL (never changes after first run).
    """
    import os as _os
    PROJECT_ROOT_L = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"

    from dotenv import load_dotenv as _ld
    _ld(_os.path.join(PROJECT_ROOT_L, ".env"), override=True)

    if not credentials_path:
        credentials_path = _os.getenv("GROUNDTRUTH_SHEETS_CREDENTIALS", "")

    if not credentials_path or not _os.path.exists(credentials_path):
        print("  WARN: Drive credentials not found — skipping HTML save")
        return ""

    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build as _build
        from googleapiclient.http import MediaInMemoryUpload

        scopes = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ]
        creds = Credentials.from_service_account_file(
            credentials_path, scopes=scopes
        )
        drive_service = _build("drive", "v3", credentials=creds)

        FILE_NAME = "GroundTruth_Latest_Digest.html"
        MARKER_FILE = _os.path.join(PROJECT_ROOT_L, ".drive_digest_id")

        file_id = None
        if _os.path.exists(MARKER_FILE):
            with open(MARKER_FILE, "r") as f:
                file_id = f.read().strip()

        if file_id:
            try:
                drive_service.files().get(fileId=file_id).execute()
            except Exception:
                file_id = None

        media = MediaInMemoryUpload(
            html_content.encode("utf-8"),
            mimetype="text/html",
            resumable=False,
        )

        if file_id:
            drive_service.files().update(
                fileId=file_id, media_body=media,
            ).execute()
            print(f"  Drive digest updated: {file_id}")
        else:
            created = drive_service.files().create(
                body={"name": FILE_NAME, "mimeType": "text/html"},
                media_body=media, fields="id",
            ).execute()
            file_id = created["id"]

            drive_service.permissions().create(
                fileId=file_id,
                body={"role": "reader", "type": "anyone"},
            ).execute()

            with open(MARKER_FILE, "w") as f:
                f.write(file_id)

            print(f"  Drive digest created: {file_id}")

        url = f"https://drive.google.com/file/d/{file_id}/view"
        print(f"  Permanent digest URL: {url}")
        return url

    except Exception as e:
        print(f"  WARN: Drive digest save failed: {e}")
        return ""


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("="*55)
    print("GT EMAIL BUILDER — MODULE TEST")
    print("="*55)

    # Mock signals
    mock_signals = [
        {
            "signal_id": "GS-010",
            "headline": "OBBBA reconciliation bill advances — solar ITC elimination confirmed",
            "summary": "Solar ITC/PTC elimination language passed committee markup.",
            "second_order": (
                "Mechanism: ITC elimination post July 4 2026 removes 30% tax credit "
                "from Project Vega economics. Timeline: 84 days to cutoff. Deal impact: "
                "Project Vega construction sprint accelerates — Moody's kill zone 8.5x "
                "default rate applies under compressed timeline with simultaneous tariff "
                "cost inflation on aluminum and steel."
            ),
            "c_tags": '["C04", "C06"]',
            "f_tags": '["F1"]',
            "t_tag": "T1",
            "alert_level": "RED",
            "weighted_score": 87.5,
            "pipeline_risk_alert": 1,
            "affected_deals": '["Project Vega"]',
            "risk_alert_rationale": "Project Vega ITC eligibility depends on July 4 cutoff.",
            "opportunity_alert": 0,
            "linkedin_candidate": 1,
        },
        {
            "signal_id": "GS-011",
            "headline": "BDC gate expansion — two additional firms restrict redemptions",
            "summary": "Two more private credit funds activated redemption gates.",
            "second_order": (
                "Mechanism: BDC gate expansion reduces private credit capacity — "
                "E01 GFC pattern confirmed. Infrastructure debt available only to "
                "relationship clients. Timeline: weeks to deal-level repricing."
            ),
            "c_tags": '["C12", "C02"]',
            "f_tags": '["F1"]',
            "t_tag": "T2",
            "alert_level": "AMBER",
            "weighted_score": 62.0,
            "pipeline_risk_alert": 0,
            "affected_deals": "[]",
            "opportunity_alert": 0,
            "linkedin_candidate": 0,
        },
        {
            "signal_id": "GS-012",
            "headline": "EIA weekly petroleum status report — inventories flat",
            "summary": "US crude inventories unchanged week-over-week.",
            "second_order": "Neutral inventory signal. No capital stack transmission.",
            "c_tags": '["C05"]',
            "f_tags": '["F5"]',
            "t_tag": "T3",
            "alert_level": "GREEN",
            "weighted_score": 28.0,
            "pipeline_risk_alert": 0,
            "affected_deals": "[]",
            "opportunity_alert": 0,
            "linkedin_candidate": 0,
        },
    ]

    # Mock encyclopedia match
    mock_enc_match = {
        "top_match": {
            "code": "E06",
            "event": "Oil Price Crash 2014-16",
            "primary_regime": "R3 — Commodity Shock",
            "match_score": 62.0,
            "matched_c_tags": ["C08", "C09", "C12"],
            "verification_latency": "Verification latency — contracts: Near-zero",
        },
        "second_match": {
            "code": "E03",
            "event": "Ukraine/Energy Crisis",
            "match_score": 58.5,
        },
        "third_match": {
            "code": "E08",
            "event": "Volcker Rate Shock",
            "match_score": 55.0,
        },
    }

    # Mock run summary
    mock_run = {
        "regime": "R0 — Compound Stress",
        "crisis_day": 42,
        "sources_fetched": 14,
        "signals_classified": 3,
        "red_count": 1,
        "amber_count": 1,
        "green_count": 1,
        "runtime_seconds": 45,
        "failures": "IEA, FERC, Recharge, NGI",
        "next_run": "manual trigger",
    }

    # Build HTML
    print("\nBuilding email HTML...")
    html = build_email(mock_signals, mock_enc_match, mock_run)
    subject = build_subject(mock_signals, mock_run)
    print(f"  Subject: {subject}")
    print(f"  HTML length: {len(html)} chars")

    # Write to file for browser preview
    output_path = r"C:\Users\nagar_7kszmu8\GroundTruth_v2\test_email_output.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  Email HTML written to test_email_output.html — open in browser to review.")
    print(f"  Path: {output_path}")
    print("\ngt/email_builder.py operational.")