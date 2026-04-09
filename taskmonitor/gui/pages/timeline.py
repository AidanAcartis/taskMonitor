from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt


class TimelineWidget(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data

        self.zoom = 1.0  # 🔥 zoom level
        self.setMinimumHeight(300)

    def wheelEvent(self, event):
        # 🔥 ZOOM avec scroll souris
        delta = event.angleDelta().y()

        if delta > 0:
            self.zoom *= 1.1
        else:
            self.zoom *= 0.9

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        y = 20
        spacing = int(30 * self.zoom)

        for cluster in self.data["clusters"]:
            color = QColor("#00bcd4")

            for ev in cluster["events"]:
                painter.setBrush(color)
                painter.drawEllipse(20, y, 8, 8)

                text = f"{ev['start']} | {ev['description'][:50]}"
                painter.drawText(40, y + 8, text)

                y += spacing