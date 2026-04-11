import subprocess
import signal
import os
from pathlib import Path


class WindowMonitor:

    def __init__(self):
        self.process = None
        self._pgid = None
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
        # sauvegarder le PGID immédiatement après le lancement
        self._pgid = os.getpgid(self.process.pid)

    def stop(self):
        if self.process and self.is_running():
            print("Monitoring stopped...")
            try:
                os.killpg(self._pgid, signal.SIGTERM)
                self.process.wait(timeout=2)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(self._pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            finally:
                self.process = None

    def is_running(self):
        return self.process is not None and self.process.poll() is None