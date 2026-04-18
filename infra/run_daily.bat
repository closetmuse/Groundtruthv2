@echo off
cd /d "C:\Users\nagar_7kszmu8\GroundTruth_v2"
"C:\Program Files\Python312\python.exe" infra\run_scheduled.py >> logs\task_output.log 2>&1
