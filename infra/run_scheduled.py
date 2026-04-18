# GroundTruth V2 — infra/run_scheduled.py
# Called by Windows Task Scheduler at 06:00 ET daily.
# Do not run manually — use infra/run_manual.py or orchestrator.py directly.
# Last Updated: April 2026

import sys
import os
import traceback
from datetime import datetime
import pytz

# ── SETUP ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
LOG_FILE     = os.path.join(PROJECT_ROOT, "logs", "scheduler.log")

os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

ET = pytz.timezone("America/New_York")


def _log(message: str):
    """Append a timestamped line to logs/scheduler.log."""
    ts = datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S ET")
    line = f"{ts} | {message}\n"
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _log("START | scheduled")

    try:
        from gt.orchestrator import run
        import gt.orchestrator as orch
        orch.DRY_RUN = False  # Scheduled runs always send email

        summary = run(trigger="scheduled")

        _log(
            f"COMPLETE | "
            f"signals:{summary.get('signals_classified', 0)} "
            f"red:{summary.get('red_count', 0)} "
            f"amber:{summary.get('amber_count', 0)} "
            f"runtime:{summary.get('runtime_seconds', 0)}s"
        )
        _log(f"EMAIL | sent:{summary.get('email_sent', False)}")
        sys.exit(0)

    except Exception as e:
        _log(f"FAILED | Error: {e}")
        traceback.print_exc()
        sys.exit(1)