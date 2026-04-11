"""
Monitoring page — launches orchestrator monitor and tails window_changes.log.
"""

import os
import sys
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton
)
from PyQt6.QtCore import QThread, pyqtSignal, QFileSystemWatcher
from PyQt6.QtGui import QFont
from taskmonitor.core.config import WINDOW_LOG_FILE
import signal


# ── Thread qui lance orchestrator monitor ─────────────────────────────────────

class _MonitoringThread(QThread):
    line_ready = pyqtSignal(str)
    stopped    = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._proc = None

    def run(self):
        env = os.environ.copy()
        env["MKL_THREADING_LAYER"]     = "GNU"
        env["MKL_SERVICE_FORCE_INTEL"] = "0"

        try:
            self._proc = subprocess.Popen(
                [sys.executable, "-m", "taskmonitor.orchestrator", "monitor"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                start_new_session=True,
            )
            for line in self._proc.stdout:
                self.line_ready.emit(line.rstrip())
            self._proc.wait()
        except Exception as e:
            self.line_ready.emit(f"[ERROR] {e}")
        finally:
            self.stopped.emit()

    def stop(self):
        if self._proc and self._proc.poll() is None:
            try:
                # tuer tout le groupe de processus (Python + bash fils)
                os.killpg(os.getpgid(self._proc.pid), signal.SIGINT)
                self._proc.wait(timeout=5)
            except ProcessLookupError:
                pass
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self._proc.pid), signal.SIGKILL)


# ── Page principale ───────────────────────────────────────────────────────────

class MonitoringPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._log_path = str(WINDOW_LOG_FILE)
        self._last_pos = 0
        self._thread   = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # ── header ────────────────────────────────────────────────────────────
        header = QHBoxLayout()

        title = QLabel("Monitoring — window_changes.log")
        title.setStyleSheet("font-size: 14px; font-weight: 500; color: #ddd;")
        header.addWidget(title)
        header.addStretch()

        self._status = QLabel("● Stopped")
        self._status.setStyleSheet("font-size: 12px; color: #888;")
        header.addWidget(self._status)

        self._btn_start = QPushButton("▶  Start")
        self._btn_start.setFixedHeight(28)
        self._btn_start.setStyleSheet("""
            QPushButton { color:#fff; background:#1a6b3a; border:none;
                          border-radius:4px; padding:0 12px; font-size:12px; }
            QPushButton:hover { background:#26a641; }
            QPushButton:disabled { background:#2a2a2a; color:#555; }
        """)
        self._btn_start.clicked.connect(self.start_monitoring)
        header.addWidget(self._btn_start)

        self._btn_stop = QPushButton("■  Stop")
        self._btn_stop.setFixedHeight(28)
        self._btn_stop.setEnabled(False)
        self._btn_stop.setStyleSheet("""
            QPushButton { color:#fff; background:#6b1a1a; border:none;
                          border-radius:4px; padding:0 12px; font-size:12px; }
            QPushButton:hover { background:#a63232; }
            QPushButton:disabled { background:#2a2a2a; color:#555; }
        """)
        self._btn_stop.clicked.connect(self.stop_monitoring)
        header.addWidget(self._btn_stop)

        btn_clear = QPushButton("Clear")
        btn_clear.setFixedHeight(28)
        btn_clear.setStyleSheet("""
            QPushButton { color:#aaa; background:#2a2a2a; border:1px solid #444;
                          border-radius:4px; padding:0 8px; font-size:11px; }
            QPushButton:hover { background:#333; }
        """)
        btn_clear.clicked.connect(self._clear)
        header.addWidget(btn_clear)

        layout.addLayout(header)

        # ── deux viewers côte à côte ──────────────────────────────────────────
        viewers_layout = QHBoxLayout()
        viewers_layout.setSpacing(8)

        # stdout du processus
        left_col = QVBoxLayout()
        left_label = QLabel("Process output")
        left_label.setStyleSheet("font-size: 11px; color: #666;")
        left_col.addWidget(left_label)
        self._stdout_viewer = self._make_viewer()
        left_col.addWidget(self._stdout_viewer)
        viewers_layout.addLayout(left_col)

        # window_changes.log
        right_col = QVBoxLayout()
        right_label = QLabel("window_changes.log")
        right_label.setStyleSheet("font-size: 11px; color: #666;")
        right_col.addWidget(right_label)
        self._log_viewer = self._make_viewer()
        right_col.addWidget(self._log_viewer)
        viewers_layout.addLayout(right_col)

        layout.addLayout(viewers_layout)

        # ── file watcher sur window_changes.log ───────────────────────────────
        self._watcher = QFileSystemWatcher()
        if WINDOW_LOG_FILE.exists():
            self._watcher.addPath(self._log_path)
        self._watcher.fileChanged.connect(self._on_log_changed)

        # charger le log existant
        self._load_log_initial()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _make_viewer(self) -> QPlainTextEdit:
        v = QPlainTextEdit()
        v.setReadOnly(True)
        v.setFont(QFont("Monospace", 10))
        v.setStyleSheet("""
            QPlainTextEdit {
                background: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        v.setMaximumBlockCount(2000)
        return v

    def _scroll_bottom(self, viewer: QPlainTextEdit):
        sb = viewer.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── log file ──────────────────────────────────────────────────────────────

    def _load_log_initial(self):
        try:
            with open(self._log_path, "r") as f:
                content = f.read()
            self._log_viewer.setPlainText(content)
            self._last_pos = len(content.encode("utf-8"))
            self._scroll_bottom(self._log_viewer)
        except FileNotFoundError:
            self._log_viewer.setPlainText(f"[File not found: {self._log_path}]")

    def _on_log_changed(self, path: str):
        try:
            with open(self._log_path, "rb") as f:
                f.seek(self._last_pos)
                new_bytes = f.read()
                self._last_pos = f.tell()
            if new_bytes:
                self._log_viewer.appendPlainText(
                    new_bytes.decode("utf-8", errors="replace").rstrip()
                )
                self._scroll_bottom(self._log_viewer)
            if path not in self._watcher.files():
                self._watcher.addPath(path)
        except FileNotFoundError:
            pass

    # ── monitoring control ────────────────────────────────────────────────────

    def start_monitoring(self):
        if self._thread and self._thread.isRunning():
            return

        self._stdout_viewer.clear()
        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._status.setText("● Running")
        self._status.setStyleSheet("font-size: 12px; color: #26a641;")

        # re-watch le log au cas où il a été recréé
        if self._log_path not in self._watcher.files():
            self._watcher.addPath(self._log_path)

        self._thread = _MonitoringThread()
        self._thread.line_ready.connect(
            lambda line: (
                self._stdout_viewer.appendPlainText(line),
                self._scroll_bottom(self._stdout_viewer)
            )
        )
        self._thread.stopped.connect(self._on_stopped)
        self._thread.start()

    def stop_monitoring(self):
        if self._thread:
            self._thread.stop()

    def _on_stopped(self):
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._status.setText("● Stopped")
        self._status.setStyleSheet("font-size: 12px; color: #888;")

    def _clear(self):
        self._stdout_viewer.clear()
        self._log_viewer.clear()