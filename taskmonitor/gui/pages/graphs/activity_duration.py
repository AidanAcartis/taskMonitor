"""
Activity Duration — bar chart showing each cluster's total duration.
Hover tooltip shows full details. Export (PNG) and zoom buttons top-right.
"""

import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QToolTip, QFileDialog, QSizePolicy, QScrollArea
)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QPixmap
from PyQt6.QtCore import Qt, QRect, QPoint, QSize


# ── palette ───────────────────────────────────────────────────────────────────
BAR_COLOR   = QColor("#26a641")
BAR_HOVER   = QColor("#39d353")
AXIS_COLOR  = QColor("#555555")
TEXT_COLOR  = QColor("#cccccc")
BG_COLOR    = QColor("#1a1a1a")

PAD_L, PAD_R, PAD_T, PAD_B = 60, 20, 20, 60
BAR_GAP = 10


def _fmt_duration(hours: float) -> str:
    s = int(round(hours * 3600))
    if s < 60:   return f"{s}s"
    if s < 3600: return f"{s//60}m {s%60:02d}s"
    return f"{s//3600}h {(s%3600)//60}m"


# ── chart widget ──────────────────────────────────────────────────────────────

class _BarChart(QWidget):
    def __init__(self, clusters: list, parent=None):
        super().__init__(parent)
        self.clusters = clusters
        self._hovered = -1
        self._zoom    = 1.0
        self._bars: list[QRect] = []
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(320)

    # ── paint ──────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), BG_COLOR)

        if not self.clusters:
            return

        w, h = self.width(), self.height()
        chart_w = w - PAD_L - PAD_R
        chart_h = h - PAD_T - PAD_B

        durations = [c["stats"]["total_duration"] for c in self.clusters]
        max_dur   = max(durations) if durations else 1

        n        = len(self.clusters)
        bar_w    = max(8, (chart_w - BAR_GAP * (n + 1)) // n)
        self._bars = []

        for i, (cluster, dur) in enumerate(zip(self.clusters, durations)):
            bh   = int(chart_h * (dur / max_dur) * self._zoom)
            bh   = min(bh, chart_h)
            bx   = PAD_L + BAR_GAP + i * (bar_w + BAR_GAP)
            by   = PAD_T + chart_h - bh
            rect = QRect(bx, by, bar_w, bh)
            self._bars.append(rect)

            color = BAR_HOVER if i == self._hovered else BAR_COLOR
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, 3, 3)

            # x-label (short intention)
            intention = cluster.get("global_task_intention", "")
            short     = intention[:12] + "…" if len(intention) > 12 else intention
            p.setPen(QPen(TEXT_COLOR))
            p.setFont(QFont("Monospace", 8))
            fm = QFontMetrics(p.font())
            lx = bx + bar_w // 2 - fm.horizontalAdvance(short) // 2
            p.drawText(lx, PAD_T + chart_h + 14, short)

            # value on top of bar
            val = _fmt_duration(dur)
            p.setFont(QFont("Monospace", 8))
            fm2 = QFontMetrics(p.font())
            vx  = bx + bar_w // 2 - fm2.horizontalAdvance(val) // 2
            if by > PAD_T + 14:
                p.drawText(vx, by - 4, val)

        # y-axis
        p.setPen(QPen(AXIS_COLOR, 1))
        p.drawLine(PAD_L, PAD_T, PAD_L, PAD_T + chart_h)
        p.drawLine(PAD_L, PAD_T + chart_h, w - PAD_R, PAD_T + chart_h)

        # y gridlines
        for step in [0.25, 0.5, 0.75, 1.0]:
            gy  = PAD_T + chart_h - int(chart_h * step * self._zoom)
            gy  = max(PAD_T, gy)
            val = _fmt_duration(max_dur * step)
            p.setPen(QPen(AXIS_COLOR, 1, Qt.PenStyle.DashLine))
            p.drawLine(PAD_L, gy, w - PAD_R, gy)
            p.setPen(QPen(TEXT_COLOR))
            p.setFont(QFont("Monospace", 8))
            p.drawText(2, gy + 4, val)

        p.end()

    # ── mouse ──────────────────────────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        pos  = event.pos()
        prev = self._hovered
        self._hovered = -1
        for i, rect in enumerate(self._bars):
            if rect.contains(pos):
                self._hovered = i
                c   = self.clusters[i]
                dur = _fmt_duration(c["stats"]["total_duration"])
                tip = (
                    f"{c.get('global_task_intention','—')}\n"
                    f"Duration : {dur}\n"
                    f"Events   : {c['stats'].get('num_events', '?')}\n"
                    f"Start    : {c['stats'].get('start','')[:16]}\n"
                    f"End      : {c['stats'].get('end','')[:16]}"
                )
                QToolTip.showText(event.globalPosition().toPoint(), tip, self)
                break
        if self._hovered != prev:
            self.update()

    def leaveEvent(self, event):
        self._hovered = -1
        self.update()

    # ── zoom ──────────────────────────────────────────────────────────────────

    def set_zoom(self, factor: float):
        self._zoom = max(0.2, min(factor, 5.0))
        self.update()

    # ── export ────────────────────────────────────────────────────────────────

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export chart", "activity_duration.png", "PNG (*.png)")
        if path:
            pix = self.grab()
            pix.save(path)


# ── stats bar ─────────────────────────────────────────────────────────────────

class _StatsBar(QWidget):
    def __init__(self, clusters: list, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(24)

        durations = [c["stats"]["total_duration"] for c in clusters]
        total     = sum(durations)
        avg       = total / len(durations) if durations else 0
        max_c     = max(clusters, key=lambda c: c["stats"]["total_duration"], default=None)

        stats = [
            ("Total duration",    _fmt_duration(total)),
            ("Clusters",          str(len(clusters))),
            ("Avg duration",      _fmt_duration(avg)),
            ("Longest cluster",   max_c.get("global_task_intention","—")[:20] if max_c else "—"),
        ]
        for label, value in stats:
            col = QVBoxLayout()
            col.setSpacing(2)
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 10px; color: #666;")
            val = QLabel(value)
            val.setStyleSheet("font-size: 13px; color: #ccc; font-weight: 500;")
            col.addWidget(lbl)
            col.addWidget(val)
            layout.addLayout(col)

        layout.addStretch()
        self.setStyleSheet("background-color: #222; border-top: 1px solid #333;")


# ── public widget ──────────────────────────────────────────────────────────────

class ActivityDurationChart(QWidget):
    TITLE = "Activity Duration"

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
        title.setStyleSheet("font-size: 14px; font-weight: 500; color: #ddd;")
        top.addWidget(title)
        top.addStretch()

        btn_zoom_in  = QPushButton("＋ Zoom")
        btn_zoom_out = QPushButton("－ Zoom")
        btn_export   = QPushButton("↓ Export")
        for b in (btn_zoom_in, btn_zoom_out, btn_export):
            b.setFixedHeight(24)
            b.setStyleSheet("""
                QPushButton { color:#aaa; background:#2a2a2a; border:1px solid #444;
                              border-radius:4px; padding:0 8px; font-size:11px; }
                QPushButton:hover { background:#333; }
            """)
        top.addWidget(btn_zoom_out)
        top.addWidget(btn_zoom_in)
        top.addWidget(btn_export)

        top_w = QWidget()
        top_w.setLayout(top)
        top_w.setStyleSheet("background-color: #1e1e1e;")
        root.addWidget(top_w)

        # chart
        self._chart = _BarChart(clusters)
        root.addWidget(self._chart, stretch=1)

        # stats
        root.addWidget(_StatsBar(clusters))

        # connections
        self._zoom_level = 1.0
        btn_zoom_in .clicked.connect(lambda: self._zoom( 1.25))
        btn_zoom_out.clicked.connect(lambda: self._zoom(0.8))
        btn_export  .clicked.connect(self._chart.export_png)

    def _zoom(self, factor: float):
        self._zoom_level *= factor
        self._chart.set_zoom(self._zoom_level)