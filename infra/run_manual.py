# GroundTruth V2 — infra/run_manual.py
# Manual trigger for Sri from command line or Claude Desktop.
#
# Workflow (post-brief-integration, 2026-04-15):
#   1. python infra/run_manual.py              → capture only, no email sent
#   2. Claude hand-writes the consolidated sector brief and appends to ledger
#   3. python infra/send_email.py              → resend email with the
#                                                 just-written brief as Section 1
#
# The default behaviour is NOW to suppress email on run_manual. The brief is a
# manual synthesis step that happens after capture, and the email is the
# delivery vehicle for the brief — so auto-sending on capture completion would
# always produce a stale or placeholder Section 1. Explicit --email flag
# restores the legacy auto-send behaviour.
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
import argparse

# Force UTF-8 on stdout so Unicode (→, —) survives Windows cp1252 consoles.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)


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

        # Next-step reminder for the brief-integrated workflow
        if not args.email:
            print()
            print("=" * 58)
            print("  CAPTURE COMPLETE — email NOT sent")
            print("  Next steps for the brief-integrated workflow:")
            print("    1. Claude hand-writes the consolidated sector brief")
            print("       to outputs/sector_briefs_<date>_<HHMM>ET.md")
            print("    2. Append Alpha findings to outputs/alpha_ledger.md")
            print("       (use infra/ledger_extract.py for scaffold)")
            print("    3. python infra/send_email.py")
            print("       → rebuilds email with brief as Section 1 and sends")
            print("=" * 58)


if __name__ == "__main__":
    main()