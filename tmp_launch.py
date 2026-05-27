"""
Phase 1 Launcher — starts run_phase1 in a background subprocess,
writing stdio to phase_1/run.log.
"""
import subprocess
import sys
import os

os.makedirs("phase_1", exist_ok=True)

cmd = [sys.executable, "src/run_phase1.py"]

with open("phase_1/run.log", "w") as out:
    proc = subprocess.Popen(cmd, stdout=out, stderr=out)
    print(f"Started PID {proc.pid}")

print("Process launched. Check phase_1/run.log for progress.")
