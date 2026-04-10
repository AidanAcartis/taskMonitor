"""
GraphStats — page principale avec QStackedWidget interne.
Chaque sous-graphe est instancié une seule fois et affiché à la demande.
Le MainWindow route les signaux "graph:<Name>" émis par la NavBar.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt

from taskmonitor.gui.pages.graphs.activity_duration import ActivityDurationChart
from taskmonitor.gui.pages.graphs.gantt             import GanttChart
from taskmonitor.gui.pages.graphs.donut_charts      import (
    TaskDonutChart, AppDonutChart, DomainDonutChart
)
from taskmonitor.gui.pages.graphs.heatmap_embed     import ActivityHeatmap


# Mapping exact : label NavBar  →  index dans le stack interne
GRAPH_NAMES = [
    "Activity Duration",   # 0
    "Gantt / Timeline",    # 1
    "Task Proportion",     # 2
    "App Proportion",      # 3
    "Domain Proportion",   # 4
    "Activity Heatmap",    # 5
]


class GraphStats(QWidget):
    def __init__(self, data: dict, parent=None):
        super().__init__(parent)

        self._stack = QStackedWidget()
        self._index: dict[str, int] = {}

        graphs = [
            ActivityDurationChart(data),
            GanttChart(data),
            TaskDonutChart(data),
            AppDonutChart(data),
            DomainDonutChart(data),
            ActivityHeatmap(data),
        ]
        for i, (name, widget) in enumerate(zip(GRAPH_NAMES, graphs)):
            self._stack.addWidget(widget)
            self._index[name] = i

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._stack)

        # show first graph by default
        self._stack.setCurrentIndex(0)

    def show_graph(self, name: str):
        """Called by MainWindow when a sub-nav item is clicked."""
        idx = self._index.get(name)
        if idx is not None:
            self._stack.setCurrentIndex(idx)