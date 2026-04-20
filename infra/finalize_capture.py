# GroundTruth V2 — infra/finalize_capture.py
# Second half of the capture workflow. Runs AFTER Claude writes the sector
# brief. Reads the .gt_capture_pending marker written by run_manual.py,
# verifies the brief file exists at the expected path, git-adds the day
# folder + alpha_ledger (if modified), commits with an auto-generated
# message, and clears the marker.
#
# Does NOT push. Push cadence is manual per 2026-04-20 hold-local protocol.
#
# Workflow:
#   python infra/run_manual.py              (writes marker + NEXT STEP)
#   [Claude writes the brief to marker.expected_brief]
#   python infra/finalize_capture.py        (verifies, commits, clears marker)
#
# Usage:
#   python infra/finalize_capture.py                    # default auto-msg
#   python infra/finalize_capture.py --headline "..."   # refined one-liner
#   python infra/finalize_capture.py --force            # commit if brief short
#   python infra/finalize_capture.py --dry              # preview, no commit
#
# Last Updated: April 2026

import sys
import os
import json
import argparse
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(r"C:\Users\nagar_7kszmu8\GroundTruth_v2")
MARKER = PROJECT_ROOT / ".gt_capture_pending"
LEDGER_REL = "outputs/alpha_ledger.md"

# Heuristic minimum-brief size below which we treat as "probably a stub and
# the author forgot to actually write it." Can be overridden with --force.
MIN_BRIEF_BYTES = 2000

CO_AUTHOR = "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"


def _git(args, check=True, capture=True):
    """Thin git wrapper — always runs from PROJECT_ROOT."""
    return subprocess.run(
        ["git"] + args,
        cwd=str(PROJECT_ROOT),
        check=check,
        capture_output=capture,
        text=True,
    )


def _ledger_was_touched():
    """True iff alpha_ledger.md has unstaged or untracked changes."""
    r = _git(["status", "--porcelain", "--", LEDGER_REL], check=False)
    return bool(r.stdout.strip())


def _build_message(ctx, headline):
    """Shape the commit title + body from marker context."""
    title = f"{ctx['slot']} capture {ctx['capture_ts_display']} — {headline}"
    body_lines = [
        f"Signals: {ctx.get('signals_classified', '?')} classified | "
        f"RED {ctx.get('red_count', '?')} | "
        f"AMBER {ctx.get('amber_count', '?')} | "
        f"GREEN {ctx.get('green_count', '?')}",
        f"Precedent: {ctx.get('encyclopedia_top') or 'none'}",
        f"Runtime: {ctx.get('runtime_seconds', '?')}s",
        "",
        "Committed by infra/finalize_capture.py — brief + dashboard",
        "+ alpha_ledger (if touched). Push deferred (hold-local protocol).",
        "",
        CO_AUTHOR,
    ]
    return title + "\n\n" + "\n".join(body_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Finalize a GroundTruth capture: verify brief, commit."
    )
    parser.add_argument(
        "--headline", type=str, default=None,
        help="One-line theme for the commit title. Strongly recommended.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Commit even if brief file is shorter than the heuristic "
             f"minimum ({MIN_BRIEF_BYTES} bytes).",
    )
    parser.add_argument(
        "--dry", action="store_true",
        help="Print what would happen; do not commit or touch the marker.",
    )
    args = parser.parse_args()

    # ── 1. Marker present? ──────────────────────────────────────────────
    if not MARKER.exists():
        print("ERROR: no .gt_capture_pending marker at project root.")
        print("       Either no capture has run since last finalize,")
        print("       or finalize has already run for the current capture.")
        print("       Run `python infra/run_manual.py` first.")
        sys.exit(1)

    with open(MARKER, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    # ── 2. Brief exists at expected path? ───────────────────────────────
    brief_rel = ctx["expected_brief"]
    brief_abs = PROJECT_ROOT / brief_rel
    if not brief_abs.exists():
        print(f"ERROR: expected brief not found:")
        print(f"       {brief_rel}")
        print()
        print("Write the sector brief to that exact path before running")
        print("finalize_capture. The path is determined by the capture")
        print("timestamp and must match what the marker recorded.")
        sys.exit(1)

    size = brief_abs.stat().st_size
    if size < MIN_BRIEF_BYTES and not args.force:
        print(f"WARN: brief is only {size} bytes (min {MIN_BRIEF_BYTES}).")
        print("      Looks too short to be a real capture brief.")
        print("      If this is intentional, re-run with --force.")
        sys.exit(1)

    # ── 3. Build commit message ─────────────────────────────────────────
    headline = args.headline or "capture complete"
    message = _build_message(ctx, headline)

    # ── 4. Preview mode ─────────────────────────────────────────────────
    if args.dry:
        print("=" * 68)
        print("  DRY RUN — no commit, no marker deletion")
        print("=" * 68)
        print(f"  Would add: {ctx['day_folder']}")
        if _ledger_was_touched():
            print(f"  Would add: {LEDGER_REL}")
        print()
        print("  Commit message:")
        print("  " + "-" * 66)
        for line in message.splitlines():
            print(f"  {line}")
        print("  " + "-" * 66)
        sys.exit(0)

    # ── 5. Stage + commit ───────────────────────────────────────────────
    try:
        _git(["add", ctx["day_folder"]])
        if _ledger_was_touched():
            _git(["add", LEDGER_REL])
            print(f"  Staged: {ctx['day_folder']}, {LEDGER_REL}")
        else:
            print(f"  Staged: {ctx['day_folder']}")
    except subprocess.CalledProcessError as e:
        print("ERROR: git add failed:")
        print(e.stderr)
        sys.exit(2)

    # Check there is actually something to commit (brief may already be
    # in a prior commit; finalize is idempotent-ish).
    diff = _git(["diff", "--cached", "--name-only"], check=False)
    if not diff.stdout.strip():
        print("NOTE: nothing staged for commit — brief may already be in")
        print("      a prior commit. Clearing marker without committing.")
        MARKER.unlink()
        sys.exit(0)

    try:
        _git(["commit", "-m", message])
    except subprocess.CalledProcessError as e:
        print("ERROR: git commit failed:")
        print(e.stdout)
        print(e.stderr)
        sys.exit(3)

    # ── 6. Clear marker, confirm ────────────────────────────────────────
    MARKER.unlink()

    head = _git(["log", "--oneline", "-1"], check=False).stdout.strip()
    ahead = _git(["rev-list", "--count", "@{u}..HEAD"], check=False).stdout.strip()
    print()
    print("=" * 68)
    print("  COMMITTED — marker cleared")
    print("=" * 68)
    print(f"  {head}")
    if ahead and ahead != "0":
        print(f"  Local is {ahead} commit(s) ahead of origin. Push when ready.")
    print("=" * 68)


if __name__ == "__main__":
    main()
