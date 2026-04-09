from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt, QRect
from datetime import datetime, timedelta
from collections import defaultdict


class HeatmapWidget(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setMinimumHeight(160)

        self.activity = self.aggregate()
        self.dates = self.build_date_range()

    def aggregate(self):
        activity = defaultdict(float)

        for cluster in self.data["clusters"]:
            for event in cluster["events"]:
                date = event["date"]
                activity[date] += event["duration"]

        return activity

    def build_date_range(self):
        dates = []

        all_dates = []
        for cluster in self.data["clusters"]:
            for e in cluster["events"]:
                all_dates.append(datetime.strptime(e["date"], "%Y-%m-%d"))

        start = min(all_dates)
        end = max(all_dates)

        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)

        return dates

    def get_color(self, value):
        if value == 0:
            return QColor("#ebedf0")
        elif value < 0.1:
            return QColor("#c6e48b")
        elif value < 0.5:
            return QColor("#7bc96f")
        elif value < 1:
            return QColor("#239a3b")
        else:
            return QColor("#196127")

    def paintEvent(self, event):
        painter = QPainter(self)

        size = 12
        spacing = 4

        x_offset = 30
        y_offset = 20

        for i, date in enumerate(self.dates):
            date_str = date.strftime("%Y-%m-%d")
            value = self.activity.get(date_str, 0)

            col = i // 7
            row = i % 7

            x = x_offset + col * (size + spacing)
            y = y_offset + row * (size + spacing)

            painter.fillRect(QRect(x, y, size, size), self.get_color(value))

            # 🟢 LABEL MOIS
            if row == 0 and date.day <= 7:
                painter.drawText(x, y - 5, date.strftime("%b"))