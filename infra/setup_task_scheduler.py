# GroundTruth V2 — infra/setup_task_scheduler.py
# Run once to register the Windows Task Scheduler job.
# Registers GroundTruth_DailyRun to execute at 06:00 ET daily.
# Last Updated: April 2026

import sys
import os
import subprocess

PROJECT_ROOT = r"C:\Users\nagar_7kszmu8\GroundTruth_v2"
PYTHON_PATH  = sys.executable
TASK_NAME    = "GroundTruth_DailyRun"
SCRIPT       = r"infra\run_scheduled.py"
BAT_WRAPPER  = os.path.join(PROJECT_ROOT, r"infra\run_daily.bat")
TRIGGER_TIME = "06:00"


def main():
    """
    Register a Windows Task Scheduler job for daily GroundTruth runs.

    Prints the schtasks command for verification, asks for confirmation,
    then executes. On failure, prints manual fallback instructions.
    """
    # Use batch wrapper for reliable working directory resolution.
    # schtasks /Create does not support a working directory parameter.
    # The batch file handles cd /d to PROJECT_ROOT before calling Python.
    cmd = [
        "schtasks", "/Create",
        "/TN", TASK_NAME,
        "/TR", BAT_WRAPPER,
        "/SC", "DAILY",
        "/ST", TRIGGER_TIME,
        "/F",  # Force overwrite if task exists
    ]

    cmd_str = " ".join(cmd)

    print("=" * 58)
    print("  GROUNDTRUTH V2 — TASK SCHEDULER SETUP")
    print("=" * 58)
    print()
    print(f"  Task name:    {TASK_NAME}")
    print(f"  Schedule:     Daily at {TRIGGER_TIME} ET")
    print(f"  Python:       {PYTHON_PATH}")
    print(f"  Script:       {SCRIPT}")
    print(f"  Working dir:  {PROJECT_ROOT}")
    print()
    print("  Command to execute:")
    print(f"    {cmd_str}")
    print()

    confirm = input("  Register this task? (y/n): ").strip().lower()
    if confirm != "y":
        print("  Aborted — task not registered.")
        _print_manual_fallback()
        return

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.returncode == 0:
            print()
            print("  Task registered. GroundTruth will run daily at 06:00 ET.")
            print(f"  To verify: schtasks /Query /TN {TASK_NAME}")
            print(f"  To delete:  schtasks /Delete /TN {TASK_NAME} /F")
        else:
            print()
            print(f"  ERROR: schtasks failed (exit code {result.returncode})")
            if result.stderr:
                print(f"  {result.stderr.strip()}")
            if result.stdout:
                print(f"  {result.stdout.strip()}")
            _print_manual_fallback()

    except Exception as e:
        print(f"\n  ERROR: {e}")
        _print_manual_fallback()

    _print_manual_fallback()


def _print_manual_fallback():
    """Print manual Task Scheduler instructions."""
    print()
    print("  Manual fallback -- if schtasks fails, open Task Scheduler and create:")
    print(f"    Program:    {PYTHON_PATH}")
    print(f"    Arguments:  {SCRIPT}")
    print(f"    Start in:   {PROJECT_ROOT}")
    print(f"    Trigger:    Daily {TRIGGER_TIME}")
    print()


if __name__ == "__main__":
    main()