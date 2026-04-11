from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QHBoxLayout, QComboBox
from PyQt6.QtCore import Qt

from .heatmap_calendar import HeatmapCalendarWidget
from .timeline import TimelineWidget
from taskmonitor.core.db_reader import (
    load_all_sessions, load_activity_counts,
    load_clusters_by_date, load_available_dates
)

COMBO_STYLE = """
    QComboBox {
        background: #1e1e1e;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        min-width: 180px;
    }
    QComboBox QAbstractItemView {
        background: #1e1e1e;
        color: #c9d1d9;
        selection-background-color: #30363d;
    }
"""

class Dashboard(QWidget):
    def __init__(self, data=None):
        super().__init__()

        self.sessions = load_all_sessions()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # ===== HEATMAP CALENDAR =====
        activity = load_activity_counts()

        heatmap_label = QLabel("Activity")
        heatmap_label.setStyleSheet("font-size: 13px; color: #8b949e; font-weight: 500;")

        self.heatmap = HeatmapCalendarWidget(activity)
        self.heatmap.on_day_clicked = self._on_heatmap_day_clicked

        layout.addWidget(heatmap_label)
        layout.addWidget(self.heatmap, alignment=Qt.AlignmentFlag.AlignLeft)

        # ===== TIMELINE HEADER =====
        timeline_header = QHBoxLayout()
        timeline_header.setContentsMargins(0, 0, 0, 0)

        timeline_label = QLabel("Timeline")
        timeline_label.setStyleSheet("font-size: 13px; color: #8b949e; font-weight: 500;")
        timeline_header.addWidget(timeline_label)
        timeline_header.addStretch()

        # ── sélecteur de session (existant) ──
        self.session_selector = QComboBox()
        self.session_selector.setStyleSheet(COMBO_STYLE)
        self.session_selector.addItem("— par session —", userData=None)
        for sid, session_date, _ in self.sessions:
            self.session_selector.addItem(session_date, userData=sid)
        self.session_selector.currentIndexChanged.connect(self._on_session_changed)
        timeline_header.addWidget(self.session_selector)

        # ── sélecteur de date (nouveau) ──
        self.date_selector = QComboBox()
        self.date_selector.setStyleSheet(COMBO_STYLE)
        self.date_selector.addItem("— par date —", userData=None)
        for date_str in load_available_dates():
            self.date_selector.addItem(date_str, userData=date_str)
        self.date_selector.currentIndexChanged.connect(self._on_date_changed)
        timeline_header.addWidget(self.date_selector)

        layout.addLayout(timeline_header)

        # ===== TIMELINE =====
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        if self.sessions:
            self._load_timeline(self.sessions[0][2])

        layout.addWidget(self.scroll)
        self.setLayout(layout)

    def _load_timeline(self, data: dict):
        self.scroll.setWidget(TimelineWidget(data))

    def _on_session_changed(self, index: int):
        # index 0 = placeholder "— par session —"
        if index == 0:
            return
        # réinitialiser le date selector sans déclencher son signal
        self.date_selector.blockSignals(True)
        self.date_selector.setCurrentIndex(0)
        self.date_selector.blockSignals(False)

        session_index = index - 1  # compenser le placeholder
        if 0 <= session_index < len(self.sessions):
            _, _, data = self.sessions[session_index]
            self._load_timeline(data)

    def _on_date_changed(self, index: int):
        # index 0 = placeholder "— par date —"
        if index == 0:
            return
        # réinitialiser le session selector sans déclencher son signal
        self.session_selector.blockSignals(True)
        self.session_selector.setCurrentIndex(0)
        self.session_selector.blockSignals(False)

        date_str = self.date_selector.currentData()
        if date_str:
            data = load_clusters_by_date(date_str)
            self._load_timeline(data)

    def _on_heatmap_day_clicked(self, day):
        print(f"Selected day: {day}")

    def change_view(self, mode):
        print(f"🔁 Mode: {mode}")