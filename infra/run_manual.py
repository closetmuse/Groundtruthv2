# GroundTruth V2 — infra/run_manual.py
# Manual trigger for Sri from command line or Claude Desktop.
#
# Workflow (post-finalize-capture, 2026-04-20):
#   1. python infra/run_manual.py              → capture only, writes
#                                                 .gt_capture_pending marker
#   2. Claude hand-writes the consolidated sector brief to the exact path
#      given in the NEXT STEP block
#   3. python infra/finalize_capture.py        → verifies brief exists,
#                                                 git adds day folder +
#                                                 alpha_ledger, commits,
#                                                 clears marker. No push.
#
# The marker file is the state handoff between (1) and (3). Claude does not
# need to "remember" to commit — the marker forces a terminal step.
#
# Usage:
#   python infra/run_manual.py                      # capture, no email (default)
#   python infra/run_manual.py --email              # capture and auto-send email
#   python infra/run_manual.py --breaking "..."     # fast path, T1 only (auto-sends)
#   python infra/run_manual.py --dry                # legacy alias for no-email
#
# Last Updated: April 2026

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# Force UTF-8 on stdout so Unicode (→, —) survives Windows cp1252 consoles.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)


def _et_now():
    """Return current ET datetime, handling DST via zoneinfo."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        # Fallback: naive local time. Will still work on boxes already in ET.
        return datetime.now()


def _infer_slot(et_dt):
    """Infer AM / PM / EOD capture slot from ET hour.

    Loose convention:
      AM  — 00:00 to 11:30 ET (early-morning to lunch)
      PM  — 11:30 to 17:30 ET (afternoon through US market close window)
      EOD — 17:30 onward     (post-close synthesis)
    """
    minutes = et_dt.hour * 60 + et_dt.minute
    if minutes < 11 * 60 + 30:
        return "AM"
    if minutes < 17 * 60 + 30:
        return "PM"
    return "EOD"


def _write_pending_marker(summary):
    """Persist state for infra/finalize_capture.py to consume.

    Called at the end of a successful no-email capture. The marker lives at
    project root and is gitignored — transient workflow state only.
    """
    et = _et_now()
    slot = _infer_slot(et)
    ts_compact = et.strftime("%Y-%m-%d_%H%MET")     # 2026-04-20_0522ET
    ts_display = et.strftime("%Y-%m-%d %H:%M ET")   # 2026-04-20 05:22 ET
    day_folder_rel = f"outputs/daily/{et.strftime('%Y-%m')}/{et.strftime('%m-%d')}"
    brief_rel = f"{day_folder_rel}/sector_briefs_{ts_compact}.md"
    dashboard_rel = f"{day_folder_rel}/dashboard_{ts_compact}.html"

    marker = {
        "capture_ts_iso": et.isoformat(),
        "capture_ts_display": ts_display,
        "capture_ts_compact": ts_compact,
        "slot": slot,
        "day_folder": day_folder_rel,
        "expected_brief": brief_rel,
        "dashboard": dashboard_rel,
        "signals_classified": summary.get("signals_classified", 0),
        "red_count": summary.get("red_count", 0),
        "amber_count": summary.get("amber_count", 0),
        "green_count": summary.get("green_count", 0),
        "runtime_seconds": summary.get("runtime_seconds", 0),
        "encyclopedia_top": summary.get("top_precedent", "") or "",
    }

    marker_path = Path(PROJECT_ROOT) / ".gt_capture_pending"
    with open(marker_path, "w", encoding="utf-8") as f:
        json.dump(marker, f, indent=2)
    return marker


def main():
    """Parse args and dispatch to orchestrator."""
    parser = argparse.ArgumentParser(
        description="GroundTruth V2 manual run. Default: capture only, no "
                    "email. Use --email to restore legacy auto-send."
    )
    parser.add_argument("--breaking", type=str, default=None,
                        help="Breaking signal description — fast path, T1 only. "
                             "Always auto-sends email regardless of --email flag.")
    parser.add_argument("--email", action="store_true",
                        help="Auto-send email at end of capture (legacy behaviour). "
                             "Default is to suppress email — brief is synthesized "
                             "manually afterward and emailed via infra/send_email.py.")
    parser.add_argument("--dry", action="store_true",
                        help="Legacy alias for the new default (no email). Kept "
                             "for backward compatibility with older invocations.")
    args = parser.parse_args()

    import gt.orchestrator as orch

    # New default: suppress email unless --email explicitly passed.
    # --dry is the legacy alias and has the same effect as the default.
    if args.email:
        orch.DRY_RUN = False
        print("  Email mode: AUTO-SEND (legacy --email flag)")
    else:
        orch.DRY_RUN = True
        if args.dry:
            print("  Email mode: SUPPRESSED (--dry flag, legacy alias for default)")
        else:
            print("  Email mode: SUPPRESSED (default — resend via "
                  "infra/send_email.py after writing brief)")

    if args.breaking:
        signal_id = orch.run_breaking_signal(
            headline=args.breaking[:120],
            content=args.breaking,
            source="ANECDOTAL",
        )
        if signal_id:
            print(f"\nBreaking signal stored: {signal_id}")
        else:
            print("\nBreaking signal failed — check output above.")
    else:
        summary = orch.run(trigger="manual")

        # Log to scheduler.log for consistency
        from infra.run_scheduled import _log
        _log(
            f"COMPLETE | manual | "
            f"signals:{summary.get('signals_classified', 0)} "
            f"red:{summary.get('red_count', 0)} "
            f"amber:{summary.get('amber_count', 0)} "
            f"runtime:{summary.get('runtime_seconds', 0)}s"
        )

        # State-handoff marker + NEXT STEP block for finalize_capture.py
        if not args.email:
            marker = _write_pending_marker(summary or {})
            print()
            print("=" * 68)
            print("  CAPTURE COMPLETE — pending-brief marker written")
            print("=" * 68)
            print(f"  Slot:      {marker['slot']}  ({marker['capture_ts_display']})")
            print(f"  RED/AMBER: {marker['red_count']} / {marker['amber_count']}")
            print(f"  Precedent: {marker['encyclopedia_top']}")
            print()
            print("  NEXT STEP — write the sector brief to this EXACT path:")
            print(f"    {marker['expected_brief']}")
            print()
            print("  When the brief is written, run:")
            print("    python infra/finalize_capture.py --headline \"<one-line theme>\"")
            print()
            print("  finalize_capture will verify the brief, git-commit the")
            print("  day folder + alpha_ledger (if touched), and clear the")
            print("  pending marker. Push is deferred to manual.")
            print("=" * 68)


if __name__ == "__main__":
    main()