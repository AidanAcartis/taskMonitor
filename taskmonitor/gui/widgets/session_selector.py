"""
Reusable session selector widget.
Displays a QComboBox with all sessions from the DB, most recent first.
Emits session_changed(data: dict) when the user picks a different session.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal
from taskmonitor.core.db_reader import load_all_sessions


class SessionSelector(QWidget):
    session_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sessions = load_all_sessions()  # [(id, session_date, data), ...]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel("Session :")
        lbl.setStyleSheet("font-size: 12px; color: #8b949e;")
        layout.addWidget(lbl)

        self.combo = QComboBox()
        self.combo.setStyleSheet("""
            QComboBox {
                background: #1e1e1e;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                min-width: 200px;
            }
            QComboBox QAbstractItemView {
                background: #1e1e1e;
                color: #c9d1d9;
                selection-background-color: #30363d;
            }
        """)

        for _, session_date, _ in self.sessions:
            self.combo.addItem(session_date)

        self.combo.currentIndexChanged.connect(self._on_changed)
        layout.addWidget(self.combo)

    def _on_changed(self, index: int):
        if 0 <= index < len(self.sessions):
            _, _, data = self.sessions[index]
            self.session_changed.emit(data)

    def current_data(self) -> dict:
        idx = self.combo.currentIndex()
        if 0 <= idx < len(self.sessions):
            return self.sessions[idx][2]
        return {"clusters": []}