"""
Line Chart — deux vues :
  1. Activité par heure de la journée (toutes sessions agrégées)
  2. Durée par domaine dans le temps (session / date / semaine / mois / année)
"""

from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QFileDialog, QSizePolicy, QStackedWidget
)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QRect, QPoint

from taskmonitor.core.db_reader import (
    load_hourly_activity,
    load_domain_by_session,
    load_domain_by_date,
    load_domain_by_week,
    load_domain_by_month,
    load_domain_by_year,
)

DOMAIN_PALETTE = {
    "development":   "#378ADD",   # blue
    "security":      "#D4537E",   # pink/red
    "sysadmin":      "#D85A30",   # coral
    "data_science":  "#7F77DD",   # purple
    "configuration": "#EF9F27",   # amber
    "study":         "#1D9E75",   # teal
    "communication": "#5DCAA5",   # light teal
    "social":        "#F09595",   # light red
    "entertainment": "#26a641",   # green
    "gaming":        "#FAC775",   # light amber
    "creative":      "#ED93B1",   # light pink
    "productivity":  "#85B7EB",   # light blue
    "browsing":      "#B4B2A9",   # gray
    "other":         "#888780",   # muted gray
}

BG       = QColor("#1a1a1a")
AXIS     = QColor("#444")
TEXT_C   = QColor("#ccc")
TEXT2    = QColor("#666")
GRID     = QColor("#2a2a2a")

PAD_L, PAD_R, PAD_T, PAD_B = 60, 24, 24, 50

COMBO_STYLE = """
    QComboBox {
        background: #1e1e1e; color: #c9d1d9;
        border: 1px solid #30363d; border-radius: 4px;
        padding: 4px 8px; font-size: 12px; min-width: 130px;
    }
    QComboBox QAbstractItemView {
        background: #1e1e1e; color: #c9d1d9;
        selection-background-color: #30363d;
    }
"""


def _fmt_h(hours: float) -> str:
    s = int(round(hours * 3600))
    if s < 60:   return f"{s}s"
    if s < 3600: return f"{s//60}m"
    return f"{s//3600}h{(s%3600)//60:02d}m"


# ── Canvas horaire ────────────────────────────────────────────────────────────

class _HourlyCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict[int, float] = {}
        self._hovered = -1
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(280)
        self.refresh()

    def refresh(self):
        self._data = load_hourly_activity()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), BG)

        if not self._data:
            return

        w, h     = self.width(), self.height()
        cw       = w - PAD_L - PAD_R
        ch       = h - PAD_T - PAD_B
        max_val  = max(self._data.values()) or 1
        hours    = list(range(24))
        step_x   = cw / 23

        def x_of(hr): return PAD_L + int(hr * step_x)
        def y_of(v):  return PAD_T + ch - int(ch * v / max_val)

        # grid
        for pct in [0.25, 0.5, 0.75, 1.0]:
            gy  = PAD_T + ch - int(ch * pct)
            val = _fmt_h(max_val * pct)
            p.setPen(QPen(GRID, 1))
            p.drawLine(PAD_L, gy, w - PAD_R, gy)
            p.setPen(QPen(TEXT2))
            p.setFont(QFont("Monospace", 8))
            p.drawText(2, gy + 4, val)

        # axes
        p.setPen(QPen(AXIS, 1))
        p.drawLine(PAD_L, PAD_T, PAD_L, PAD_T + ch)
        p.drawLine(PAD_L, PAD_T + ch, w - PAD_R, PAD_T + ch)

        # x labels
        p.setFont(QFont("Monospace", 8))
        for hr in range(0, 24, 3):
            x = x_of(hr)
            p.setPen(QPen(TEXT2))
            p.drawText(x - 8, PAD_T + ch + 16, f"{hr:02d}h")

        # line
        color = QColor("#378ADD")
        pts   = [(x_of(hr), y_of(self._data.get(hr, 0))) for hr in hours]

        # fill area
        fill = QColor("#378ADD")
        fill.setAlpha(30)
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(pts[0][0], PAD_T + ch)
        for x, y in pts:
            path.lineTo(x, y)
        path.lineTo(pts[-1][0], PAD_T + ch)
        path.closeSubpath()
        p.setBrush(fill)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(path)

        # line stroke
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(color, 2))
        for i in range(len(pts) - 1):
            p.drawLine(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])

        # dots
        for hr, (x, y) in enumerate(pts):
            val = self._data.get(hr, 0)
            hov = (hr == self._hovered)
            p.setBrush(color if not hov else QColor("#ffffff"))
            p.setPen(QPen(color, 2))
            r = 5 if hov else 3
            p.drawEllipse(QPoint(x, y), r, r)

        p.end()

    def mouseMoveEvent(self, event):
        w   = self.width()
        cw  = w - PAD_L - PAD_R
        step_x = cw / 23
        x   = event.pos().x() - PAD_L
        hr  = round(x / step_x) if step_x > 0 else -1
        hr  = max(0, min(23, hr))
        if self._hovered != hr:
            self._hovered = hr
            self.update()
        val = self._data.get(hr, 0)
        from PyQt6.QtWidgets import QToolTip
        QToolTip.showText(
            event.globalPosition().toPoint(),
            f"{hr:02d}h00 — {_fmt_h(val)}", self
        )

    def leaveEvent(self, event):
        self._hovered = -1
        self.update()

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export", "hourly_activity.png", "PNG (*.png)")
        if path:
            self.grab().save(path)


# ── Canvas domaine/temps ──────────────────────────────────────────────────────

class _DomainCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._labels: list[str] = []
        self._series: dict[str, list[float]] = {}
        self._hovered_domain = None
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(280)

    def set_data(self, grouped: dict[str, dict[str, float]]):
        """grouped = {label: {domain: hours}}"""
        self._labels = list(grouped.keys())
        domains = set()
        for d in grouped.values():
            domains.update(d.keys())
        self._series = {
            dom: [grouped[lbl].get(dom, 0) for lbl in self._labels]
            for dom in sorted(domains)
        }
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), BG)

        if not self._labels or not self._series:
            return

        w, h    = self.width(), self.height()
        cw      = w - PAD_L - PAD_R - 100  # leave room for legend
        ch      = h - PAD_T - PAD_B
        n       = len(self._labels)
        max_val = max(
            (max(vals) for vals in self._series.values() if vals),
            default=1
        ) or 1
        step_x  = cw / max(n - 1, 1)

        def x_of(i): return PAD_L + int(i * step_x)
        def y_of(v): return PAD_T + ch - int(ch * v / max_val)

        # grid
        for pct in [0.25, 0.5, 0.75, 1.0]:
            gy  = PAD_T + ch - int(ch * pct)
            p.setPen(QPen(GRID, 1))
            p.drawLine(PAD_L, gy, PAD_L + cw, gy)
            p.setPen(QPen(TEXT2))
            p.setFont(QFont("Monospace", 8))
            p.drawText(2, gy + 4, _fmt_h(max_val * pct))

        # axes
        p.setPen(QPen(AXIS, 1))
        p.drawLine(PAD_L, PAD_T, PAD_L, PAD_T + ch)
        p.drawLine(PAD_L, PAD_T + ch, PAD_L + cw, PAD_T + ch)

        # x labels
        p.setFont(QFont("Monospace", 8))
        for i, lbl in enumerate(self._labels):
            x    = x_of(i)
            short = lbl[-5:] if len(lbl) > 5 else lbl
            p.setPen(QPen(TEXT2))
            p.drawText(x - 16, PAD_T + ch + 16, short)

        # lines
        from PyQt6.QtGui import QPainterPath
        for dom, vals in self._series.items():
            color = QColor(DOMAIN_PALETTE.get(dom, "#888780"))
            hov   = (dom == self._hovered_domain)
            pts   = [(x_of(i), y_of(v)) for i, v in enumerate(vals)]

            # fill
            fill = QColor(color)
            fill.setAlpha(20 if not hov else 50)
            path = QPainterPath()
            path.moveTo(pts[0][0], PAD_T + ch)
            for x, y in pts:
                path.lineTo(x, y)
            path.lineTo(pts[-1][0], PAD_T + ch)
            path.closeSubpath()
            p.setBrush(fill)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(path)

            # stroke
            p.setBrush(Qt.BrushStyle.NoBrush)
            pen = QPen(color, 2.5 if hov else 1.5)
            p.setPen(pen)
            for i in range(len(pts) - 1):
                p.drawLine(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])

            # dots
            for x, y in pts:
                p.setBrush(color)
                p.setPen(QPen(color, 1))
                p.drawEllipse(QPoint(x, y), 3, 3)

        # legend (right)
        lx = PAD_L + cw + 12
        ly = PAD_T
        p.setFont(QFont("Monospace", 9))
        for i, (dom, _) in enumerate(self._series.items()):
            color = QColor(DOMAIN_PALETTE.get(dom, "#888780"))
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRect(lx, ly + i * 20, 10, 10), 2, 2)
            p.setPen(QPen(TEXT_C))
            p.drawText(lx + 14, ly + i * 20 + 9, dom)

        p.end()

    def mouseMoveEvent(self, event):
        # highlight domain on hover (simple proximity to legend)
        self.update()

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export", "domain_timeline.png", "PNG (*.png)")
        if path:
            self.grab().save(path)


# ── Widget principal ──────────────────────────────────────────────────────────

class LineChart(QWidget):
    TITLE = "Line Charts"

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── top bar ───────────────────────────────────────────────────────────
        top = QHBoxLayout()
        top.setContentsMargins(12, 8, 12, 8)

        title = QLabel(self.TITLE)
        title.setStyleSheet("font-size:14px;font-weight:500;color:#ddd;")
        top.addWidget(title)
        top.addStretch()

        # vue selector
        self._view_combo = QComboBox()
        self._view_combo.setStyleSheet(COMBO_STYLE)
        self._view_combo.addItems([
            "Activité par heure",
            "Domaines — par session",
            "Domaines — par date",
            "Domaines — par semaine",
            "Domaines — par mois",
            "Domaines — par année",
        ])
        self._view_combo.currentIndexChanged.connect(self._switch_view)
        top.addWidget(self._view_combo)

        btn_export = QPushButton("↓ Export")
        btn_export.setFixedHeight(24)
        btn_export.setStyleSheet("""
            QPushButton { color:#aaa; background:#2a2a2a; border:1px solid #444;
                          border-radius:4px; padding:0 8px; font-size:11px; }
            QPushButton:hover { background:#333; }
        """)
        btn_export.clicked.connect(self._export)
        top.addWidget(btn_export)

        top_w = QWidget()
        top_w.setLayout(top)
        top_w.setStyleSheet("background-color:#1e1e1e;")
        root.addWidget(top_w)

        # ── stack interne ─────────────────────────────────────────────────────
        self._stack = QStackedWidget()

        self._hourly  = _HourlyCanvas()
        self._domain  = _DomainCanvas()

        self._stack.addWidget(self._hourly)   # 0 — hourly
        self._stack.addWidget(self._domain)   # 1 — domain (réutilisé)

        root.addWidget(self._stack, stretch=1)

        # ── stats bar ─────────────────────────────────────────────────────────
        self._stats_label = QLabel()
        self._stats_label.setStyleSheet(
            "font-size:11px;color:#666;padding:6px 12px;"
            "background:#222;border-top:1px solid #333;"
        )
        root.addWidget(self._stats_label)

        # init
        self._switch_view(0)

    def _switch_view(self, index: int):
        if index == 0:
            self._hourly.refresh()
            self._stack.setCurrentIndex(0)
            total = sum(self._hourly._data.values())
            peak  = max(self._hourly._data, key=self._hourly._data.get, default=0)
            self._stats_label.setText(
                f"Total enregistré : {_fmt_h(total)}   |   "
                f"Heure de pic : {peak:02d}h00"
            )
        else:
            loaders = {
                1: load_domain_by_session,
                2: load_domain_by_date,
                3: load_domain_by_week,
                4: load_domain_by_month,
                5: load_domain_by_year,
            }
            raw = loaders[index]()
            # normaliser en dict{label: {domain: float}}
            if isinstance(raw, list):
                grouped = {label: d for label, d in raw}
            else:
                grouped = raw

            self._domain.set_data(grouped)
            self._stack.setCurrentIndex(1)

            n_points = len(grouped)
            domains  = set()
            for d in grouped.values():
                domains.update(d.keys())
            self._stats_label.setText(
                f"Points : {n_points}   |   "
                f"Domaines : {', '.join(sorted(domains))}"
            )

    def _export(self):
        widget = self._stack.currentWidget()
        if hasattr(widget, "export_png"):
            widget.export_png()