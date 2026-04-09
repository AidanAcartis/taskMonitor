"""
GitHub-style activity heatmap calendar widget for PyQt6.
Reads cluster data from final_output.json and displays daily activity frequency.
"""

import json
from datetime import date, timedelta
from collections import defaultdict

from PyQt6.QtWidgets import QWidget, QToolTip, QSizePolicy
from PyQt6.QtGui import QPainter, QColor, QFont, QCursor
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from pathlib import Path


MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = ["Mon", "Wed", "Fri"]  # shown at rows 1, 3, 5

# Colors matching GitHub's heatmap palette (dark-theme friendly)
LEVEL_COLORS = [
    QColor("#161b22"),   # 0 – no activity (dark neutral)
    QColor("#0e4429"),   # 1 – low
    QColor("#006d32"),   # 2 – medium-low
    QColor("#26a641"),   # 3 – medium-high
    QColor("#39d353"),   # 4 – high
]
CELL_SIZE = 13
CELL_GAP = 3
STEP = CELL_SIZE + CELL_GAP
LEFT_MARGIN = 30    # space for day labels
TOP_MARGIN = 20     # space for month labels
CORNER_RADIUS = 2


def parse_activity_from_json(json_path: str | Path) -> dict[str, int]:

    """
    Parse final_output.json and return a dict mapping 'YYYY-MM-DD' -> session_count.
    One cluster (or singleton) per day is counted as one session.
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    clusters = data.get("clusters", [])
    counts: dict[str, int] = defaultdict(int)

    for cluster in clusters:
        stats = cluster.get("stats", {})
        start_str = stats.get("start", "")
        if start_str:
            day = start_str[:10]   # 'YYYY-MM-DD'
            counts[day] += 1

    return dict(counts)


def compute_level(count: int) -> int:
    """Map a session count to a heatmap level (0-4)."""
    if count == 0:
        return 0
    if count == 1:
        return 1
    if count <= 3:
        return 2
    if count <= 6:
        return 3
    return 4


class HeatmapCalendarWidget(QWidget):
    """
    A GitHub-style contribution heatmap calendar.

    Shows the last 52 weeks of activity, one cell per day.
    Cell color intensity reflects session count for that day.

    Usage:
        activity = parse_activity_from_json("final_output.json")
        widget = HeatmapCalendarWidget(activity)
    """

    def __init__(self, activity: dict[str, int], parent=None):
        super().__init__(parent)
        self.activity = activity          # {'YYYY-MM-DD': count}
        self.weeks = self._build_weeks()  # list of lists of date (or None)
        self.hovered_cell: tuple[int, int] | None = None  # (week_idx, day_idx)

        # Compute widget size
        num_weeks = len(self.weeks)
        w = LEFT_MARGIN + num_weeks * STEP + CELL_GAP
        h = TOP_MARGIN + 7 * STEP + 30   # +30 for legend row
        self.setFixedSize(QSize(w, h))
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _build_weeks(self) -> list[list[date | None]]:
        """
        Build a 2-D grid: weeks[week_idx][day_of_week (0=Sun..6=Sat)].
        Covers the last 52 full weeks up to today.
        """
        today = date.today()
        # rewind to the most recent Sunday
        start = today - timedelta(days=today.weekday() + 1)  # Monday-based -> Sunday
        # align to Sunday (weekday 6 in Python's Mon=0 system)
        while start.weekday() != 6:
            start -= timedelta(days=1)
        start -= timedelta(weeks=51)    # go back 51 more weeks → 52 total

        weeks: list[list[date | None]] = []
        current = start
        while current <= today:
            week: list[date | None] = []
            for d in range(7):
                day = current + timedelta(days=d)
                week.append(day if day <= today else None)
            weeks.append(week)
            current += timedelta(weeks=1)
        return weeks

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font_small = QFont("Monospace", 9)
        painter.setFont(font_small)

        drawn_months: set[int] = set()

        for wi, week in enumerate(self.weeks):
            x = LEFT_MARGIN + wi * STEP

            # Month label at the first cell of a new month
            for day in week:
                if day and day.day <= 7 and day.month not in drawn_months:
                    drawn_months.add(day.month)
                    painter.setPen(QColor("#8b949e"))
                    painter.drawText(x, 12, MONTH_LABELS[day.month - 1])
                    break

            for di, day in enumerate(week):
                y = TOP_MARGIN + di * STEP

                # Day labels (Mon, Wed, Fri) on the very first column
                if wi == 0 and di in (1, 3, 5):
                    painter.setPen(QColor("#8b949e"))
                    label = DAY_LABELS[di // 2]
                    painter.drawText(0, y + CELL_SIZE - 2, label)

                if day is None:
                    continue

                key = day.isoformat()
                count = self.activity.get(key, 0)
                level = compute_level(count)
                color = LEVEL_COLORS[level]

                # Highlight hovered cell
                if self.hovered_cell == (wi, di):
                    color = color.lighter(150)

                painter.setBrush(color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(
                    QRect(x, y, CELL_SIZE, CELL_SIZE),
                    CORNER_RADIUS, CORNER_RADIUS
                )

        # Legend
        legend_y = TOP_MARGIN + 7 * STEP + 8
        painter.setFont(font_small)
        painter.setPen(QColor("#8b949e"))
        painter.drawText(LEFT_MARGIN, legend_y + CELL_SIZE - 2, "Less")
        lx = LEFT_MARGIN + 32
        for i, color in enumerate(LEVEL_COLORS):
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                QRect(lx + i * (CELL_SIZE + 2), legend_y, CELL_SIZE, CELL_SIZE),
                CORNER_RADIUS, CORNER_RADIUS
            )
        painter.setPen(QColor("#8b949e"))
        painter.drawText(lx + 5 * (CELL_SIZE + 2) + 2, legend_y + CELL_SIZE - 2, "More")

        painter.end()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        cell = self._cell_at(pos)
        if cell != self.hovered_cell:
            self.hovered_cell = cell
            self.update()

        if cell:
            wi, di = cell
            day = self.weeks[wi][di]
            if day:
                key = day.isoformat()
                count = self.activity.get(key, 0)
                label = f"{count} session{'s' if count != 1 else ''} on {key}" if count else f"No activity on {key}"
                QToolTip.showText(QCursor.pos(), label, self)
        else:
            QToolTip.hideText()

    def mousePressEvent(self, event):
        cell = self._cell_at(event.pos())
        if cell:
            wi, di = cell
            day = self.weeks[wi][di]
            if day:
                self.on_day_clicked(day)

    def leaveEvent(self, event):
        self.hovered_cell = None
        self.update()

    def _cell_at(self, pos: QPoint) -> tuple[int, int] | None:
        """Return (week_idx, day_idx) for a given pixel position, or None."""
        x, y = pos.x() - LEFT_MARGIN, pos.y() - TOP_MARGIN
        if x < 0 or y < 0:
            return None
        wi = x // STEP
        di = y // STEP
        if wi >= len(self.weeks) or di >= 7:
            return None
        # check we're inside the cell, not the gap
        if x % STEP >= CELL_SIZE or y % STEP >= CELL_SIZE:
            return None
        if self.weeks[wi][di] is None:
            return None
        return wi, di

    def on_day_clicked(self, day: date):
        """Override this to react to a day being clicked."""
        print(f"Day clicked: {day} — {self.activity.get(day.isoformat(), 0)} sessions")