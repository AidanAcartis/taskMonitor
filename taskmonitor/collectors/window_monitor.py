import subprocess
import signal
import os
from pathlib import Path


class WindowMonitor:

    def __init__(self):
        self.process = None
        self.script_path = Path(__file__).parent / "window_monitor.sh"

    def start(self):
        if self.process and self.is_running():
            print("Monitoring already in progress")
            return

        print("Starting monitoring (bash)...")

        self.process = subprocess.Popen(
            ["bash", str(self.script_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )

    def stop(self):
        if self.process and self.is_running():
            print("Monitoring stopped...")
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process = None

    def is_running(self):
        return self.process is not None and self.process.poll() is None