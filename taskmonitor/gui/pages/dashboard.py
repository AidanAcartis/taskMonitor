from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PyQt6.QtCore import Qt

from .heatmap_calendar import HeatmapCalendarWidget, parse_activity_from_json
from .timeline import TimelineWidget
from taskmonitor.core.config import EXPORTS_DIR


class Dashboard(QWidget):
    def __init__(self, data):
        super().__init__()

        self.data = data

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # ===== HEATMAP CALENDAR =====
        json_path = EXPORTS_DIR / "final_output.json"
        activity = parse_activity_from_json(json_path)

        heatmap_label = QLabel("Activity")
        heatmap_label.setStyleSheet("font-size: 13px; color: #8b949e; font-weight: 500;")

        self.heatmap = HeatmapCalendarWidget(activity)
        self.heatmap.on_day_clicked = self._on_heatmap_day_clicked

        layout.addWidget(heatmap_label)
        layout.addWidget(self.heatmap, alignment=Qt.AlignmentFlag.AlignLeft)

        # ===== TIMELINE SCROLLABLE =====
        self.timeline = TimelineWidget(data)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.timeline)

        layout.addWidget(scroll)
        self.setLayout(layout)

    def _on_heatmap_day_clicked(self, day):
        print(f"Selected day: {day}")

    def change_view(self, mode):
        print(f"🔁 Mode: {mode}")