"""
Donut charts:
  - TaskDonutChart    — proportion of time per global task (cluster)
  - AppDonutChart     — proportion of time per application
  - DomainDonutChart  — proportion of time per domain (work/leisure/etc.)
"""

import math
from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QToolTip, QFileDialog, QSizePolicy
)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QRect, QRectF, QPoint

from taskmonitor.gui.widgets.session_selector import SessionSelector

PALETTE = [
    "#26a641","#378ADD","#7F77DD","#EF9F27","#D4537E",
    "#1D9E75","#D85A30","#5DCAA5","#FAC775","#F09595",
]

# ── domain keyword mapping ──────────────────────────────────────────────────────
DOMAIN_MAP = {
    "work":          ["visual studio code","terminal","code .","ls ","git ",
                      "python","data_command","config.py","documents"],
    "leisure":       ["youtube","chinchilla","little girl gone","2002 teen fashion",
                      "google chrome","new tab","music","video"],
    "security":      ["burp suite","nmap","metasploit","wireshark","pen test",
                      "attack","exploit","payload"],
    "configuration": ["config","settings","setup","install","apt","pip "],
    "study":         ["study","learn","course","tutorial","lecture","book"],
    "other":         [],   # fallback
}


def _assign_domain(description: str) -> str:
    desc = description.lower()
    for domain, keywords in DOMAIN_MAP.items():
        if domain == "other":
            continue
        if any(kw in desc for kw in keywords):
            return domain
    return "other"


def _fmt_duration(hours: float) -> str:
    s = int(round(hours * 3600))
    if s < 60:   return f"{s}s"
    if s < 3600: return f"{s//60}m {s%60:02d}s"
    return f"{s//3600}h {(s%3600)//60}m"


# ── base donut canvas ─────────────────────────────────────────────────────────

class _DonutCanvas(QWidget):
    def __init__(self, slices: list[tuple[str, float]], parent=None):
        """slices : list of (label, value_in_hours)"""
        super().__init__(parent)
        self.slices   = slices
        self._hovered = -1
        self._arcs: list[tuple[float, float]] = []   # (start_angle, span) in 1/16°
        self.setMouseTracking(True)
        self.setMinimumSize(340, 280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#1a1a1a"))

        if not self.slices:
            return

        w, h    = self.width(), self.height()
        size    = min(w - 180, h - 40)   # leave room for legend
        size    = max(size, 100)
        cx, cy  = size // 2 + 20, h // 2
        outer_r = size // 2
        inner_r = int(outer_r * 0.55)

        total = sum(v for _, v in self.slices)
        if total == 0:
            return

        self._arcs = []
        angle = 90 * 16   # start at top

        for i, (label, val) in enumerate(self.slices):
            span  = int(round(val / total * 360 * 16))
            color = QColor(PALETTE[i % len(PALETTE)])

            expand = 6 if i == self._hovered else 0
            rect   = QRectF(cx - outer_r - expand, cy - outer_r - expand,
                            (outer_r + expand) * 2, (outer_r + expand) * 2)

            p.setBrush(color)
            p.setPen(QPen(QColor("#1a1a1a"), 2))
            p.drawPie(rect, angle, span)

            self._arcs.append((angle, span))
            angle += span

        # inner hole
        p.setBrush(QColor("#1a1a1a"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(cx, cy), inner_r, inner_r)

        # center text (hovered slice)
        if self._hovered >= 0:
            label, val = self.slices[self._hovered]
            pct  = val / total * 100
            p.setPen(QPen(QColor("#ddd")))
            p.setFont(QFont("Monospace", 11, QFont.Weight.Bold))
            fm   = QFontMetrics(p.font())
            txt  = f"{pct:.1f}%"
            p.drawText(cx - fm.horizontalAdvance(txt)//2, cy + 4, txt)
            p.setFont(QFont("Monospace", 8))
            fm2  = QFontMetrics(p.font())
            short = label[:14]
            p.setPen(QPen(QColor("#999")))
            p.drawText(cx - fm2.horizontalAdvance(short)//2, cy + 18, short)

        # legend (right side)
        lx = cx + outer_r + 24
        ly = (h - len(self.slices) * 22) // 2
        for i, (label, val) in enumerate(self.slices):
            color = QColor(PALETTE[i % len(PALETTE)])
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRect(lx, ly + i * 22, 12, 12), 2, 2)
            p.setPen(QPen(QColor("#bbb")))
            p.setFont(QFont("Monospace", 9))
            pct  = val / total * 100
            text = f"{label[:16]}  {pct:.1f}%"
            p.drawText(lx + 18, ly + i * 22 + 10, text)

        p.end()

    def _angle_at(self, pos: QPoint) -> int:
        w, h    = self.width(), self.height()
        size    = min(w - 180, h - 40)
        size    = max(size, 100)
        cx, cy  = size // 2 + 20, h // 2
        outer_r = size // 2
        inner_r = int(outer_r * 0.55)

        dx, dy = pos.x() - cx, cy - pos.y()
        dist   = math.sqrt(dx*dx + dy*dy)
        if dist < inner_r or dist > outer_r + 8:
            return -1

        raw_angle = math.degrees(math.atan2(dy, dx)) * 16
        for i, (start, span) in enumerate(self._arcs):
            # normalise into [0, 360*16)
            s = start % (360 * 16)
            a = raw_angle % (360 * 16)
            end = (s + span) % (360 * 16)
            if span == 0:
                continue
            if s <= end:
                if s <= a <= end:
                    return i
            else:
                if a >= s or a <= end:
                    return i
        return -1

    def mouseMoveEvent(self, event):
        idx  = self._angle_at(event.pos())
        prev = self._hovered
        self._hovered = idx
        if idx >= 0:
            label, val = self.slices[idx]
            total = sum(v for _, v in self.slices)
            tip = f"{label}\n{_fmt_duration(val)}  ({val/total*100:.1f}%)"
            QToolTip.showText(event.globalPosition().toPoint(), tip, self)
        if idx != prev:
            self.update()

    def leaveEvent(self, event):
        self._hovered = -1
        self.update()

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export", "donut.png", "PNG (*.png)")
        if path:
            self.grab().save(path)


# ── stats bar ─────────────────────────────────────────────────────────────────

class _StatsBar(QWidget):
    def __init__(self, slices: list[tuple[str, float]], parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(24)

        total = sum(v for _, v in slices)
        top   = max(slices, key=lambda x: x[1], default=("—", 0))

        stats = [
            ("Categories",   str(len(slices))),
            ("Total time",   _fmt_duration(total)),
            ("Top category", f"{top[0][:18]}  ({top[1]/total*100:.0f}%)" if total else "—"),
        ]
        for label, value in stats:
            col = QVBoxLayout(); col.setSpacing(2)
            lbl = QLabel(label); lbl.setStyleSheet("font-size:10px;color:#666;")
            val = QLabel(value); val.setStyleSheet("font-size:13px;color:#ccc;font-weight:500;")
            col.addWidget(lbl); col.addWidget(val)
            layout.addLayout(col)
        layout.addStretch()
        self.setStyleSheet("background-color:#222;border-top:1px solid #333;")


# ── base page wrapper ─────────────────────────────────────────────────────────

class _DonutPage(QWidget):
    TITLE = "Donut Chart"

    def __init__(self, slices: list[tuple[str, float]], parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(12, 8, 12, 8)
        title = QLabel(self.TITLE)
        title.setStyleSheet("font-size:14px;font-weight:500;color:#ddd;")
        top.addWidget(title)
        top.addStretch()

        self._selector = SessionSelector()
        self._selector.session_changed.connect(self._on_session_changed)
        top.addWidget(self._selector)

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

        self._canvas = _DonutCanvas(slices)
        root.addWidget(self._canvas, stretch=1)

        # ← assigné à self._stats_bar
        self._stats_bar = _StatsBar(slices)
        root.addWidget(self._stats_bar)

        btn_export.clicked.connect(self._canvas.export_png)

    def _on_session_changed(self, data: dict):
        slices = self._build(data.get("clusters", []))
        self._canvas.slices = slices
        self._canvas.update()
        self._stats_bar.setParent(None)
        self._stats_bar = _StatsBar(slices)
        self.layout().addWidget(self._stats_bar)


# ── Task proportion ───────────────────────────────────────────────────────────

class TaskDonutChart(_DonutPage):
    TITLE = "Task Proportion"

    def __init__(self, data: dict, parent=None):
        slices = self._build(data.get("clusters", []))
        super().__init__(slices, parent)

    @staticmethod
    def _build(clusters):
        return [
            (c.get("global_task_intention", "—"), c["stats"]["total_duration"])
            for c in clusters
        ]


# ── App proportion ────────────────────────────────────────────────────────────

class AppDonutChart(_DonutPage):
    TITLE = "App Proportion"

    def __init__(self, data: dict, parent=None):
        slices = self._build(data.get("clusters", []))
        super().__init__(slices, parent)

    @staticmethod
    def _build(clusters):
        totals: dict[str, float] = defaultdict(float)
        for c in clusters:
            for item in c.get("task_items", []):
                desc = item.get("description", "")
                app  = "Unknown"
                for known in ["Visual Studio Code","Terminal","Google Chrome",
                               "Burp Suite","Documents","YouTube"]:
                    if known.lower() in desc.lower():
                        app = known; break
                totals[app] += item.get("total_duration", 0)
        return sorted(totals.items(), key=lambda x: -x[1])


# ── Domain proportion ─────────────────────────────────────────────────────────

class DomainDonutChart(_DonutPage):
    TITLE = "Domain Proportion"

    def __init__(self, data: dict, parent=None):
        slices = self._build(data.get("clusters", []))
        super().__init__(slices, parent)

    @staticmethod
    def _build(clusters):
        totals: dict[str, float] = defaultdict(float)
        for c in clusters:
            for item in c.get("task_items", []):
                domain = _assign_domain(item.get("description", ""))
                totals[domain] += item.get("total_duration", 0)
        return sorted(totals.items(), key=lambda x: -x[1])