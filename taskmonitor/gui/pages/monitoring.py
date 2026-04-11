"""
Monitoring page — tails window_changes.log in real time.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QFileSystemWatcher
from PyQt6.QtGui import QFont, QColor, QPalette
from taskmonitor.core.config import WINDOW_LOG_FILE


class MonitoringPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._log_path = str(WINDOW_LOG_FILE)
        self._last_pos = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # ── header ────────────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Monitoring — window_changes.log")
        title.setStyleSheet("font-size: 14px; font-weight: 500; color: #ddd;")
        header.addWidget(title)
        header.addStretch()

        self._status = QLabel("● Live")
        self._status.setStyleSheet("font-size: 12px; color: #26a641;")
        header.addWidget(self._status)

        btn_clear = QPushButton("Clear")
        btn_clear.setFixedHeight(24)
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
        self._viewer.setMaximumBlockCount(2000)
        layout.addWidget(self._viewer)

        # ── file watcher ──────────────────────────────────────────────────────
        self._watcher = QFileSystemWatcher([self._log_path])
        self._watcher.fileChanged.connect(self._on_file_changed)

        # ── initial load ──────────────────────────────────────────────────────
        self._load_initial()

    def _load_initial(self):
        try:
            with open(self._log_path, "r") as f:
                content = f.read()
                self._viewer.setPlainText(content)
                self._last_pos = len(content.encode("utf-8"))
                self._scroll_bottom()
        except FileNotFoundError:
            self._viewer.setPlainText(f"[File not found: {self._log_path}]")

    def _on_file_changed(self, path: str):
        try:
            with open(self._log_path, "rb") as f:
                f.seek(self._last_pos)
                new_bytes = f.read()
                self._last_pos = f.tell()

            if new_bytes:
                new_text = new_bytes.decode("utf-8", errors="replace")
                self._viewer.appendPlainText(new_text.rstrip())
                self._scroll_bottom()

            # re-watch (some editors replace the file)
            if path not in self._watcher.files():
                self._watcher.addPath(path)

        except FileNotFoundError:
            pass

    def _scroll_bottom(self):
        sb = self._viewer.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear(self):
        self._viewer.clear()