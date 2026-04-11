"""
Processing page — runs the orchestrator and streams stdout in real time.
"""

import subprocess
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import os

class _ProcessingThread(QThread):
    line_ready  = pyqtSignal(str)
    finished_ok = pyqtSignal()
    finished_err = pyqtSignal(int)

    def run(self):
        env = os.environ.copy()
        env["MKL_THREADING_LAYER"] = "GNU"        # fix MKL/libgomp conflict
        env["MKL_SERVICE_FORCE_INTEL"] = "0"

        try:
            proc = subprocess.Popen(
                [sys.executable, "-m", "taskmonitor.orchestrator", "process"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,                           # <-- passer l'env corrigé
            )
            for line in proc.stdout:
                self.line_ready.emit(line.rstrip())
            proc.wait()
            if proc.returncode == 0:
                self.finished_ok.emit()
            else:
                self.finished_err.emit(proc.returncode)
        except Exception as e:
            self.line_ready.emit(f"[ERROR] {e}")
            self.finished_err.emit(-1)


class ProcessingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # ── header ────────────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Processing")
        title.setStyleSheet("font-size: 14px; font-weight: 500; color: #ddd;")
        header.addWidget(title)
        header.addStretch()

        self._status = QLabel("Idle")
        self._status.setStyleSheet("font-size: 12px; color: #888;")
        header.addWidget(self._status)

        self._btn_run = QPushButton("▶  Start processing")
        self._btn_run.setFixedHeight(28)
        self._btn_run.setStyleSheet("""
            QPushButton { color:#fff; background:#1a6b3a; border:none;
                          border-radius:4px; padding:0 12px; font-size:12px; }
            QPushButton:hover { background:#26a641; }
            QPushButton:disabled { background:#2a2a2a; color:#555; }
        """)
        self._btn_run.clicked.connect(self.start_processing)
        header.addWidget(self._btn_run)

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

        # ── log viewer ────────────────────────────────────────────────────────
        self._viewer = QPlainTextEdit()
        self._viewer.setReadOnly(True)
        self._viewer.setFont(QFont("Monospace", 10))
        self._viewer.setStyleSheet("""
            QPlainTextEdit {
                background: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self._viewer.setMaximumBlockCount(5000)
        layout.addWidget(self._viewer)

    def start_processing(self):
        if self._thread and self._thread.isRunning():
            return
        self._viewer.clear()
        self._btn_run.setEnabled(False)
        self._status.setText("● Running...")
        self._status.setStyleSheet("font-size: 12px; color: #EF9F27;")

        self._thread = _ProcessingThread()
        self._thread.line_ready.connect(self._append)
        self._thread.finished_ok.connect(self._on_ok)
        self._thread.finished_err.connect(self._on_err)
        self._thread.start()

    def _append(self, line: str):
        self._viewer.appendPlainText(line)
        sb = self._viewer.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_ok(self):
        self._status.setText("✔ Completed")
        self._status.setStyleSheet("font-size: 12px; color: #26a641;")
        self._btn_run.setEnabled(True)

    def _on_err(self, code: int):
        self._status.setText(f"✘ Error (code {code})")
        self._status.setStyleSheet("font-size: 12px; color: #F09595;")
        self._btn_run.setEnabled(True)

    def _clear(self):
        self._viewer.clear()