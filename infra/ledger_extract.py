#!/usr/bin/env python
# ledger_extract.py — Scaffold alpha_ledger.md entries from a consolidated
# sector brief markdown file. Mechanical assistance inside the manual
# brief-writing workflow: pre-fills what can be pulled from the brief by
# regex, leaves judgment fields as TODO markers for human completion.
#
# This is NOT automation of brief production. The brief is still written by
# hand. This script only removes the typing-and-typo cost of the ledger
# append step per [feedback_alpha_ledger_discipline.md] memory.
#
# Usage:
#   python infra/ledger_extract.py outputs/sector_briefs_2026-04-15_1442ET.md
#   python infra/ledger_extract.py outputs/sector_briefs_2026-04-15_1442ET.md --append
#
# Without --append, prints scaffold to stdout for review/copy-paste.
# With --append, writes scaffold to outputs/alpha_ledger.md directly (still
# requires human to fill TODO fields afterward).

import sys
import os
import re
import argparse
from datetime import date, timedelta
from pathlib import Path

# Force UTF-8 on stdout so Unicode (→, —) survives Windows cp1252 consoles.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(r"C:\Users\nagar_7kszmu8\GroundTruth_v2")
LEDGER_PATH = PROJECT_ROOT / "outputs" / "alpha_ledger.md"

# ── Regex patterns ────────────────────────────────────────────────────────────
# Brief filename: sector_briefs_YYYY-MM-DD_HHMMET*.md
FILENAME_RE = re.compile(
    r"sector_briefs_(\d{4}-\d{2}-\d{2})_(\d{4})ET(?:_\w+)?\.md$"
)

# Alpha section header (the heading that contains "ALPHA —")
ALPHA_HEADER_RE = re.compile(r"^.*ALPHA\s*—", re.IGNORECASE)

# An Alpha finding inside the Alpha section looks like:
#   **1. Title text that may span the line.**
# or
#   **1. Title text**
# We capture the number and the title.
FINDING_HEAD_RE = re.compile(r"^\*\*(\d+)\.\s+(.+?)\.?\*\*\s*$")

# Inline field extractors (labels used in the 1442 brief template)
AXIS_RE      = re.compile(r"\*\*Axis:\*\*\s*(.+?)(?:\n|$)")
SIGNAL_RE    = re.compile(r"\*\*Signals?:\*\*\s*(.+?)(?:\n|$)")
MECH_RE      = re.compile(r"\*\*Mechanism:\*\*\s*(.+?)(?:\n\n|$)", re.DOTALL)
VL_RE        = re.compile(
    r"\*\*Estimated Verification Latency:?\*\*\s*\n?\s*(.+?)(?:\n\n|$)",
    re.DOTALL,
)
# Pull an N-to-M day range out of VL text
VL_RANGE_RE  = re.compile(r"(\d+)\s*[–-]\s*(\d+)\s*days?", re.IGNORECASE)
# Pull GS-NNN signal references
GSID_RE      = re.compile(r"GS-\d{3,4}")


def parse_brief_filename(path: Path):
    """Extract issue date and HHMM ET from filename. Returns (date_obj, hhmm_str)."""
    m = FILENAME_RE.search(path.name)
    if not m:
        raise ValueError(
            f"Filename does not match sector_briefs_YYYY-MM-DD_HHMMET*.md: "
            f"{path.name}"
        )
    issue_date = date.fromisoformat(m.group(1))
    hhmm = m.group(2)
    return issue_date, hhmm


def extract_alpha_section(text: str) -> str:
    """Return the substring of the brief from the Alpha header to the next top-level divider."""
    lines = text.splitlines()
    in_alpha = False
    out = []
    for line in lines:
        if ALPHA_HEADER_RE.search(line):
            in_alpha = True
            out.append(line)
            continue
        if in_alpha:
            # Stop at the next "====" divider that looks like a new top section
            if line.startswith("====") and out and not out[-1].startswith("===="):
                # Check if the preceding line is a section title (uppercase + ends with UTC/ET label)
                # Simpler: stop at the next RUN PROVENANCE or similar block divider
                # Heuristic: if we've already captured content and hit another "====", stop.
                # But we also want to ignore the closing "====" of the Alpha header itself.
                # Approach: ignore the first trailing "====" after the header, then stop at the next.
                pass
            if re.match(r"^RUN PROVENANCE|^DROPPED FROM|^MACRO OVERLAY", line):
                break
            out.append(line)
    return "\n".join(out)


def split_findings(alpha_text: str) -> list:
    """Split the Alpha section into one chunk per numbered finding.

    Returns a list of dicts: {num: str, title: str, body: str}
    """
    lines = alpha_text.splitlines()
    findings = []
    current = None

    for line in lines:
        m = FINDING_HEAD_RE.match(line.strip())
        if m:
            if current:
                findings.append(current)
            current = {
                "num": m.group(1),
                "title": m.group(2).strip(),
                "body_lines": [],
            }
            continue
        if current is not None:
            current["body_lines"].append(line)

    if current:
        findings.append(current)

    for f in findings:
        f["body"] = "\n".join(f["body_lines"])
        del f["body_lines"]
    return findings


def extract_field(body: str, pattern: re.Pattern) -> str:
    """Run a regex on the body, return the captured group or empty string."""
    m = pattern.search(body)
    if not m:
        return ""
    return m.group(1).strip()


def parse_vl_range(vl_text: str) -> tuple:
    """Find the widest day-range mentioned in the VL text. Returns (low, high) or (None, None)."""
    matches = list(VL_RANGE_RE.finditer(vl_text))
    if not matches:
        return (None, None)
    # Use the widest range mentioned (the outer bound of all ranges in the text)
    lows = [int(m.group(1)) for m in matches]
    highs = [int(m.group(2)) for m in matches]
    return (min(lows), max(highs))


def compute_window_close(issue_date: date, high_days: int) -> date:
    return issue_date + timedelta(days=high_days)


def format_ledger_entry(
    issue_date: date,
    hhmm: str,
    brief_filename: str,
    seq: int,
    finding: dict,
) -> str:
    """Render one finding as an ALF ledger entry with TODO markers for judgment fields."""
    body = finding["body"]

    axis = extract_field(body, AXIS_RE) or "TODO — axis reference"
    mech = extract_field(body, MECH_RE) or "TODO — compress mechanism to one line"
    # Compress mechanism to a single line if it spans multiple
    mech = re.sub(r"\s+", " ", mech).strip()
    if len(mech) > 400:
        mech = mech[:397] + "... TODO — compress further"

    vl_text = extract_field(body, VL_RE)
    low, high = parse_vl_range(vl_text)
    if high is None:
        vl_line = "TODO — VL window YYYY-MM-DD → YYYY-MM-DD (N days)"
    else:
        close = compute_window_close(issue_date, high)
        days = high
        vl_line = (
            f"{issue_date.isoformat()} → {close.isoformat()} "
            f"({days} days — outer bound of stated {low}–{high} day estimate)"
        )

    # Source signals: collect GS-IDs from body, plus anything in the Signal: field
    gs_ids = sorted(set(GSID_RE.findall(body)))
    src_field = extract_field(body, SIGNAL_RE)
    if src_field:
        sources = src_field
        if gs_ids:
            # Ensure GS-IDs are referenced
            missing = [g for g in gs_ids if g not in sources]
            if missing:
                sources = sources + " / " + " ".join(missing)
    else:
        sources = ", ".join(gs_ids) if gs_ids else "TODO — source signals"

    alf_id = f"ALF-{issue_date.strftime('%Y%m%d')}-{seq}"

    return (
        f"### {alf_id} — {finding['title']}\n"
        f"- **Issued:** {issue_date.isoformat()} {hhmm[:2]}:{hhmm[2:]} ET "
        f"({brief_filename})\n"
        f"- **Axis:** {axis}\n"
        f"- **Named deal / vehicle:** TODO — deal name if natural, else "
        f'"none — sector-level finding"\n'
        f"- **Mechanism (one line):** {mech}\n"
        f"- **VL window:** {vl_line}\n"
        f"- **Source signals:** {sources}\n"
        f"- **Outcome:** PENDING\n"
        f"- **Resolution note:**\n"
    )


def _next_seq_for_date(issue_date: date) -> int:
    """Scan the ledger for the highest existing ALF-YYYYMMDD-N sequence number
    for this date, and return the next unused N. This handles the multi-brief-
    per-day case — a 14:42 brief writes -1/-2/-3, and a 17:32 brief on the same
    day should pick up with -4 rather than colliding with -1/-2.
    """
    if not LEDGER_PATH.exists():
        return 1
    content = LEDGER_PATH.read_text(encoding="utf-8")
    prefix = f"ALF-{issue_date.strftime('%Y%m%d')}-"
    nums = re.findall(rf"{re.escape(prefix)}(\d+)", content)
    if not nums:
        return 1
    return max(int(n) for n in nums) + 1


def render_scaffold(brief_path: Path) -> str:
    """Read brief, extract Alpha findings, return ledger-format scaffold."""
    issue_date, hhmm = parse_brief_filename(brief_path)
    text = brief_path.read_text(encoding="utf-8")
    alpha = extract_alpha_section(text)
    if not alpha:
        raise ValueError("No Alpha section header found in brief")
    findings = split_findings(alpha)
    if not findings:
        return "# No Alpha findings detected in brief.\n"

    start_seq = _next_seq_for_date(issue_date)
    out = []
    for i, f in enumerate(findings):
        out.append(
            format_ledger_entry(
                issue_date, hhmm, brief_path.name, start_seq + i, f
            )
        )
    return "\n".join(out)


def append_to_ledger(scaffold: str, issue_date: date) -> None:
    """Append scaffold to alpha_ledger.md, inserting under the date header.

    Insertion anchors on the footer divider — the `====` line immediately
    preceding the `PENDING COUNT:` footer. The anchor regex matches a full
    line starting with `====` followed by a newline, so the inserted scaffold
    lands on its own lines rather than colliding with the divider mid-line.

    If today's date header does not already exist in the ledger, it is
    created before the footer divider.

    Side-effect: bumps the PENDING COUNT by the number of new findings in
    the scaffold (approximated by counting `### ALF-` headings).
    """
    if not LEDGER_PATH.exists():
        raise FileNotFoundError(f"Ledger not found: {LEDGER_PATH}")

    content = LEDGER_PATH.read_text(encoding="utf-8")
    date_header_text = f"{issue_date.isoformat()}"
    date_header_block = (
        f"================================================================\n"
        f"{date_header_text}\n"
        f"================================================================\n"
    )

    # Count findings being added (used for PENDING COUNT bump)
    n_findings = len(re.findall(r"^### ALF-", scaffold, re.MULTILINE))

    # Anchor on the full-line footer divider that immediately precedes
    # "PENDING COUNT:". Pattern: a line of ==== followed by a newline and
    # then the PENDING COUNT line. This ensures insertion happens BEFORE
    # the divider and on its own lines.
    footer_anchor = re.compile(
        r"(\n={10,}\n)(PENDING COUNT:[^\n]*)",
        re.MULTILINE,
    )
    m = footer_anchor.search(content)
    if not m:
        # Fallback: no recognizable footer — append at end
        LEDGER_PATH.write_text(content + "\n\n" + scaffold, encoding="utf-8")
        print(f"Appended scaffold to end of {LEDGER_PATH.name} (no footer found)")
        return

    # Insertion point: right before the divider preceding the footer line
    divider_start = m.start(1) + 1  # +1 to preserve the leading newline
    before = content[:divider_start]
    after = content[divider_start:]

    # Ensure today's date header exists in the content we're preserving
    if date_header_text not in before:
        # Add a fresh date header block before the scaffold
        insert_block = "\n" + date_header_block + "\n" + scaffold + "\n"
    else:
        # Date header exists — just insert findings with surrounding newlines
        insert_block = "\n" + scaffold + "\n"

    new_content = before + insert_block + after

    # Bump PENDING COUNT
    def _bump_pending(match):
        line = match.group(0)
        m2 = re.search(r"PENDING COUNT:\s*(\d+)", line)
        if not m2:
            return line
        new_pending = int(m2.group(1)) + n_findings
        return re.sub(
            r"PENDING COUNT:\s*\d+",
            f"PENDING COUNT: {new_pending}",
            line,
        )
    new_content = re.sub(
        r"^PENDING COUNT:.*$",
        _bump_pending,
        new_content,
        count=1,
        flags=re.MULTILINE,
    )

    LEDGER_PATH.write_text(new_content, encoding="utf-8")
    print(f"Appended {n_findings} entries for {issue_date.isoformat()} "
          f"to {LEDGER_PATH}")
    print("REMINDER: TODO markers in the scaffold still need human completion.")


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold alpha_ledger.md entries from a sector brief."
    )
    parser.add_argument("brief", help="Path to sector_briefs_*.md file")
    parser.add_argument(
        "--append", action="store_true",
        help="Append scaffold to outputs/alpha_ledger.md. Without this flag, "
             "the scaffold is printed to stdout for review.",
    )
    args = parser.parse_args()

    brief_path = Path(args.brief)
    if not brief_path.is_absolute():
        brief_path = PROJECT_ROOT / brief_path
    if not brief_path.exists():
        print(f"ERROR: brief not found: {brief_path}", file=sys.stderr)
        sys.exit(1)

    try:
        scaffold = render_scaffold(brief_path)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.append:
        issue_date, _ = parse_brief_filename(brief_path)
        append_to_ledger(scaffold, issue_date)
    else:
        print(scaffold)
        print("\n# Review above. To append to ledger:")
        print(f"#   python infra/ledger_extract.py {args.brief} --append")


if __name__ == "__main__":
    main()
