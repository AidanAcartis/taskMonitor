from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QHBoxLayout, QComboBox
from PyQt6.QtCore import Qt

from .heatmap_calendar import HeatmapCalendarWidget
from .timeline import TimelineWidget
from taskmonitor.core.db_reader import load_all_sessions, load_activity_counts


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

        self.session_selector = QComboBox()
        self.session_selector.setStyleSheet("""
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

        for sid, session_date, _ in self.sessions:
            self.session_selector.addItem(session_date, userData=sid)

        self.session_selector.currentIndexChanged.connect(self._on_session_changed)
        timeline_header.addWidget(self.session_selector)

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
        if 0 <= index < len(self.sessions):
            _, _, data = self.sessions[index]
            self._load_timeline(data)

    def _on_heatmap_day_clicked(self, day):
        print(f"Selected day: {day}")

    def change_view(self, mode):
        print(f"🔁 Mode: {mode}")