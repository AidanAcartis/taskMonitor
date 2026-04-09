"""
Vertical stem-style timeline widget for PyQt6.
Displays clusters as minimal entries: dot + intention + time range.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush


# ── Color assignment by cluster type ──────────────────────────────────────────

def _cluster_color(cluster_id: str) -> str:
    cid = cluster_id.lower()
    if "singleton" in cid:
        return "#888780"          # gray
    # rotate through a small palette for numbered clusters
    palette = ["#26a641", "#378ADD", "#7F77DD", "#EF9F27", "#D4537E"]
    try:
        # extract trailing digit
        digit = int("".join(filter(str.isdigit, cluster_id)))
        return palette[digit % len(palette)]
    except (ValueError, IndexError):
        return "#888780"


# ── Small dot widget ───────────────────────────────────────────────────────────

class _Dot(QWidget):
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(QSize(10, 10))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(self._color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 8, 8)
        p.end()


# ── Vertical stem (thin line) ─────────────────────────────────────────────────

class _Stem(QWidget):
    def __init__(self, last: bool = False, parent=None):
        super().__init__(parent)
        self._last = last
        self.setFixedWidth(10)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(32)

    def paintEvent(self, event):
        if self._last:
            return
        p = QPainter(self)
        p.setPen(QPen(QColor("#3a3a3a"), 1))
        cx = self.width() // 2
        p.drawLine(cx, 0, cx, self.height())
        p.end()


# ── One timeline entry ────────────────────────────────────────────────────────

class _TimelineEntry(QWidget):
    def __init__(self, cluster: dict, last: bool = False, parent=None):
        super().__init__(parent)

        stats = cluster.get("stats", {})
        start_str = stats.get("start", "")
        end_str   = stats.get("end", "")
        intention = cluster.get("global_task_intention", "—")
        color     = _cluster_color(cluster.get("cluster_id", ""))

        start_label = start_str[11:16] if len(start_str) >= 16 else ""
        end_label   = end_str[11:16]   if len(end_str)   >= 16 else ""
        duration    = _fmt_duration(stats.get("total_duration", 0))

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── left: time ──
        time_label = QLabel(start_label)
        time_label.setFixedWidth(44)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        time_label.setStyleSheet("font-size: 11px; color: #666; font-family: monospace; padding-top: 2px; padding-right: 8px;")
        outer.addWidget(time_label)

        # ── center: dot + stem ──
        spine = QWidget()
        spine.setFixedWidth(20)
        spine_layout = QVBoxLayout(spine)
        spine_layout.setContentsMargins(0, 0, 0, 0)
        spine_layout.setSpacing(0)
        spine_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        dot = _Dot(color)
        dot.setContentsMargins(0, 2, 0, 0)
        spine_layout.addWidget(dot, alignment=Qt.AlignmentFlag.AlignHCenter)
        spine_layout.addWidget(_Stem(last=last))

        outer.addWidget(spine)

        # ── right: text ──
        text_col = QWidget()
        text_layout = QVBoxLayout(text_col)
        text_layout.setContentsMargins(10, 0, 0, 28)
        text_layout.setSpacing(3)

        lbl_intention = QLabel(intention.capitalize())
        lbl_intention.setStyleSheet("font-size: 13px; font-weight: 500; color: #e0e0e0;")
        lbl_intention.setWordWrap(True)

        time_range = f"{start_label} – {end_label}  ·  {duration}" if end_label != start_label else f"{start_label}  ·  {duration}"
        lbl_time = QLabel(time_range)
        lbl_time.setStyleSheet("font-size: 11px; color: #666;")

        text_layout.addWidget(lbl_intention)
        text_layout.addWidget(lbl_time)

        outer.addWidget(text_col, stretch=1)


# ── Duration formatter ─────────────────────────────────────────────────────────

def _fmt_duration(hours: float) -> str:
    total_sec = int(round(hours * 3600))
    if total_sec < 60:
        return f"{total_sec} s"
    minutes = total_sec // 60
    if minutes < 60:
        return f"{minutes} min"
    h, m = divmod(minutes, 60)
    return f"{h} h {m} min" if m else f"{h} h"


# ── Date header ────────────────────────────────────────────────────────────────

class _DateHeader(QLabel):
    def __init__(self, date_str: str, parent=None):
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            text = d.strftime("%a %-d %b %Y").upper()
        except ValueError:
            text = date_str.upper()
        super().__init__(text, parent)
        self.setStyleSheet(
            "font-size: 11px; font-weight: 500; color: #555; letter-spacing: 0.06em;"
            "margin-left: 74px; margin-bottom: 12px; margin-top: 8px;"
        )


# ── Main timeline widget ───────────────────────────────────────────────────────

class TimelineWidget(QWidget):
    """
    Vertical stem-style timeline.

    Expects `data` as a dict with a 'clusters' list matching final_output.json.
    Clusters are grouped by date and sorted by start time.
    """

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 24)
        layout.setSpacing(0)

        clusters = data.get("clusters", [])
        grouped  = self._group_by_date(clusters)

        for date_str, day_clusters in sorted(grouped.items()):
            layout.addWidget(_DateHeader(date_str))
            for i, cluster in enumerate(day_clusters):
                last = (i == len(day_clusters) - 1)
                layout.addWidget(_TimelineEntry(cluster, last=last))

        layout.addStretch()

    @staticmethod
    def _group_by_date(clusters: list) -> dict:
        groups: dict[str, list] = {}
        for c in clusters:
            start = c.get("stats", {}).get("start", "")
            date  = start[:10] if len(start) >= 10 else "unknown"
            groups.setdefault(date, []).append(c)
        # sort each day's clusters by start time
        for date in groups:
            groups[date].sort(key=lambda c: c.get("stats", {}).get("start", ""))
        return groups