"""
Activity Heatmap — reuses HeatmapCalendarWidget from the dashboard.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt
from taskmonitor.gui.pages.heatmap_calendar import (
    HeatmapCalendarWidget, parse_activity_from_json
)
from taskmonitor.core.config import EXPORTS_DIR


class ActivityHeatmap(QWidget):
    TITLE = "Activity Heatmap"

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # top bar
        top = QHBoxLayout()
        top.setContentsMargins(12, 8, 12, 8)
        title = QLabel(self.TITLE)
        title.setStyleSheet("font-size:14px;font-weight:500;color:#ddd;")
        top.addWidget(title)
        top.addStretch()

        btn_export = QPushButton("↓ Export")
        btn_export.setFixedHeight(24)
        btn_export.setStyleSheet("""
            QPushButton { color:#aaa; background:#2a2a2a; border:1px solid #444;
                          border-radius:4px; padding:0 8px; font-size:11px; }
            QPushButton:hover { background:#333; }
        """)
        top.addWidget(btn_export)

        top_w = QWidget(); top_w.setLayout(top)
        top_w.setStyleSheet("background-color:#1e1e1e;")
        root.addWidget(top_w)

        # heatmap
        json_path = EXPORTS_DIR / "final_output.json"
        activity  = parse_activity_from_json(json_path)
        self._heatmap = HeatmapCalendarWidget(activity)

        content = QWidget()
        content.setStyleSheet("background-color:#1a1a1a;")
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(24, 24, 24, 24)
        c_layout.addWidget(self._heatmap, alignment=Qt.AlignmentFlag.AlignLeft)
        c_layout.addStretch()
        root.addWidget(content, stretch=1)

        # stats bar
        clusters = data.get("clusters", [])
        active_days = len({
            c["stats"]["start"][:10]
            for c in clusters
            if c.get("stats", {}).get("start")
        })
        total_sessions = len(clusters)

        stats_bar = QWidget()
        stats_bar.setStyleSheet("background-color:#222;border-top:1px solid #333;")
        s_layout = QHBoxLayout(stats_bar)
        s_layout.setContentsMargins(12, 6, 12, 6)
        s_layout.setSpacing(24)

        for label, value in [("Active days", str(active_days)),
                              ("Total sessions", str(total_sessions))]:
            col = QVBoxLayout(); col.setSpacing(2)
            lbl = QLabel(label); lbl.setStyleSheet("font-size:10px;color:#666;")
            val = QLabel(value); val.setStyleSheet("font-size:13px;color:#ccc;font-weight:500;")
            col.addWidget(lbl); col.addWidget(val)
            s_layout.addLayout(col)
        s_layout.addStretch()
        root.addWidget(stats_bar)

        btn_export.clicked.connect(self._export)

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export heatmap", "heatmap.png", "PNG (*.png)")
        if path:
            self._heatmap.grab().save(path)