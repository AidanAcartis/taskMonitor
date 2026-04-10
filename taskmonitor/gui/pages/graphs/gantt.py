"""
Gantt / Timeline — shows active segments per cluster across the day.
Adapts to minute/hour/day scale based on actual data span.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QToolTip, QFileDialog, QSizePolicy, QScrollArea
)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QRect


PAD_L, PAD_R, PAD_T, PAD_B = 160, 20, 20, 30
ROW_H  = 28
ROW_GAP = 6
BG     = QColor("#1a1a1a")
AXIS   = QColor("#444")
TEXT   = QColor("#ccc")
TEXT2  = QColor("#888")

PALETTE = [
    "#26a641","#378ADD","#7F77DD","#EF9F27",
    "#D4537E","#1D9E75","#D85A30","#888780",
]


def _parse_dt(s: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return datetime.min


def _fmt_duration(hours: float) -> str:
    s = int(round(hours * 3600))
    if s < 60:   return f"{s}s"
    if s < 3600: return f"{s//60}m"
    return f"{s//3600}h{(s%3600)//60}m"


class _GanttCanvas(QWidget):
    def __init__(self, clusters: list, parent=None):
        super().__init__(parent)
        self.clusters = clusters
        self._hovered_seg = None   # (cluster_idx, seg_idx)
        self._rects: dict = {}     # (ci, si) -> QRect
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._compute_time_range()
        self._update_height()

    def _compute_time_range(self):
        all_starts, all_ends = [], []
        for c in self.clusters:
            for seg in c.get("segments", []):
                all_starts.append(_parse_dt(seg["start"]))
                all_ends.append(_parse_dt(seg["end"]))
        self._t_min = min(all_starts) if all_starts else datetime.min
        self._t_max = max(all_ends)   if all_ends   else datetime.min
        span_sec = (self._t_max - self._t_min).total_seconds()
        # choose tick scale
        if span_sec <= 3600:
            self._tick_sec = 300      # every 5 min
            self._tick_fmt = "%H:%M"
        elif span_sec <= 86400:
            self._tick_sec = 3600
            self._tick_fmt = "%H:00"
        else:
            self._tick_sec = 86400
            self._tick_fmt = "%b %d"

    def _update_height(self):
        n = len(self.clusters)
        self.setFixedHeight(PAD_T + n * (ROW_H + ROW_GAP) + PAD_B)

    def _t_to_x(self, dt: datetime, chart_w: int) -> int:
        span = (self._t_max - self._t_min).total_seconds()
        if span == 0:
            return PAD_L
        frac = (dt - self._t_min).total_seconds() / span
        return PAD_L + int(frac * chart_w)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), BG)

        chart_w = self.width() - PAD_L - PAD_R
        span    = (self._t_max - self._t_min).total_seconds()

        # ticks
        if span > 0:
            t = self._t_min
            from datetime import timedelta
            while t <= self._t_max:
                x = self._t_to_x(t, chart_w)
                p.setPen(QPen(AXIS, 1, Qt.PenStyle.DashLine))
                p.drawLine(x, PAD_T, x, self.height() - PAD_B)
                p.setPen(QPen(TEXT2))
                p.setFont(QFont("Monospace", 8))
                p.drawText(x - 16, self.height() - PAD_B + 14, t.strftime(self._tick_fmt))
                t += timedelta(seconds=self._tick_sec)

        self._rects = {}

        for ci, cluster in enumerate(self.clusters):
            color  = QColor(PALETTE[ci % len(PALETTE)])
            y      = PAD_T + ci * (ROW_H + ROW_GAP)

            # row label
            intention = cluster.get("global_task_intention", "—")
            short     = intention[:18] + "…" if len(intention) > 18 else intention
            p.setPen(QPen(TEXT))
            p.setFont(QFont("Monospace", 9))
            p.drawText(4, y + ROW_H // 2 + 4, short)

            # segments
            for si, seg in enumerate(cluster.get("segments", [])):
                t_s = _parse_dt(seg["start"])
                t_e = _parse_dt(seg["end"])
                x1  = self._t_to_x(t_s, chart_w)
                x2  = self._t_to_x(t_e, chart_w)
                w   = max(4, x2 - x1)

                rect = QRect(x1, y + 4, w, ROW_H - 8)
                self._rects[(ci, si)] = rect

                hov  = self._hovered_seg == (ci, si)
                fill = color.lighter(130) if hov else color
                p.setBrush(fill)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(rect, 3, 3)

        p.end()

    def mouseMoveEvent(self, event):
        pos  = event.pos()
        prev = self._hovered_seg
        self._hovered_seg = None
        for (ci, si), rect in self._rects.items():
            if rect.contains(pos):
                self._hovered_seg = (ci, si)
                c   = self.clusters[ci]
                seg = c["segments"][si]
                tip = (
                    f"{c.get('global_task_intention','—')}\n"
                    f"Segment : {seg['start'][11:16]} – {seg['end'][11:16]}\n"
                    f"Duration: {_fmt_duration(seg['duration'])}"
                )
                QToolTip.showText(event.globalPosition().toPoint(), tip, self)
                break
        if self._hovered_seg != prev:
            self.update()

    def leaveEvent(self, event):
        self._hovered_seg = None
        self.update()

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export", "gantt.png", "PNG (*.png)")
        if path:
            self.grab().save(path)


class _StatsBar(QWidget):
    def __init__(self, clusters: list, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(24)

        total_segs = sum(len(c.get("segments", [])) for c in clusters)
        all_spans  = []
        for c in clusters:
            segs = c.get("segments", [])
            if segs:
                t0 = _parse_dt(segs[0]["start"])
                t1 = _parse_dt(segs[-1]["end"])
                all_spans.append((t1 - t0).total_seconds() / 3600)

        stats = [
            ("Clusters",       str(len(clusters))),
            ("Total segments", str(total_segs)),
            ("Day span",       f"{sum(all_spans):.1f} h" if all_spans else "—"),
        ]
        for label, value in stats:
            col = QVBoxLayout()
            col.setSpacing(2)
            lbl = QLabel(label); lbl.setStyleSheet("font-size:10px;color:#666;")
            val = QLabel(value); val.setStyleSheet("font-size:13px;color:#ccc;font-weight:500;")
            col.addWidget(lbl); col.addWidget(val)
            layout.addLayout(col)
        layout.addStretch()
        self.setStyleSheet("background-color:#222;border-top:1px solid #333;")


class GanttChart(QWidget):
    TITLE = "Gantt / Timeline"

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        clusters = data.get("clusters", [])

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

        top_w = QWidget()
        top_w.setLayout(top)
        top_w.setStyleSheet("background-color:#1e1e1e;")
        root.addWidget(top_w)

        # scrollable canvas
        self._canvas = _GanttCanvas(clusters)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._canvas)
        scroll.setStyleSheet("background:#1a1a1a; border:none;")
        root.addWidget(scroll, stretch=1)

        root.addWidget(_StatsBar(clusters))

        btn_export.clicked.connect(self._canvas.export_png)