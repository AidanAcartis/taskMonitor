from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QStackedWidget
from taskmonitor.gui.header import Header
from taskmonitor.gui.toolbar_layout import ToolbarLayout
from taskmonitor.gui.navbar import NavBar
from PyQt6.QtCore import Qt, pyqtSignal
from taskmonitor.gui.pages.dashboard import Dashboard
from taskmonitor.gui.pages.graph_stats import GraphStats
from taskmonitor.gui.pages.chart      import Chart
from taskmonitor.gui.pages.monitoring import MonitoringPage
from taskmonitor.gui.pages.processing import ProcessingPage
import json
from taskmonitor.core.config import EXPORTS_DIR
from taskmonitor.core.db_reader import load_latest_session
from taskmonitor.core.db_reader import (
    load_all_sessions, load_activity_counts,
    load_clusters_by_date, load_available_dates
)
from taskmonitor.gui.pages.help import HelpPage

# data_path = EXPORTS_DIR / "final_output.json"

# with open(data_path, "r") as f:
#     data = json.load(f)

data = load_latest_session() or {"clusters": []}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._history: list[str] = ["Dashboard"]  # historique des pages
        self._history_idx: int = 0                 # position courante

        self.setWindowTitle("TaskMonitor")
        self.setGeometry(100, 100, 800, 600)

        # ===== TOOLBAR =====
        self.header = Header()
        self.addToolBar(self.header)   # ✅ IMPORTANT

        self.setStyleSheet("""
            QMainWindow::separator {
                height: 0px;
                background: transparent;
            }
            """)

        # ===== CENTRAL WIDGET =====
        container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        container.setLayout(main_layout)

        # ===== NOUVEAU LAYOUT (titre + loader) =====
        self.toolbar_layout = ToolbarLayout()
        main_layout.addWidget(self.toolbar_layout)

        self.toolbar_layout.btn_prev.setEnabled(False)
        self.toolbar_layout.btn_next.setEnabled(False)

        # ===== ZONE BASSE (HORIZONTALE) =====
        bottom_container = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        bottom_container.setLayout(bottom_layout)

        # ===== NAVBAR (gauche) =====
        self.navbar = NavBar()

        # table de routing : label NavBar → index dans le stack
        self.page_index = {
            "Dashboard":       0,
            "Graphes & Stats": 1,
            "Chart":           2,
            "Monitoring":      3,
            "Processing":      4,
            "Help":            5,
        }

        self.navbar.page_selected.connect(self.switch_page)
        bottom_layout.addWidget(self.navbar)

        # ===== CENTRAL AREA (droite) =====
        # ===== STACK =====
        self.stack = QStackedWidget()

        self.page_dashboard   = Dashboard()
        self.page_graphstats  = GraphStats(data)
        self.page_chart = Chart(data)
        self.page_monitoring  = MonitoringPage()
        self.page_processing  = ProcessingPage()
        self.page_help        = HelpPage() 

        self.stack.addWidget(self.page_dashboard)   # index 0
        self.stack.addWidget(self.page_graphstats)  # index 1
        self.stack.addWidget(self.page_chart)        # index 2
        self.stack.addWidget(self.page_monitoring)   # 3
        self.stack.addWidget(self.page_processing)
        self.stack.addWidget(self.page_help) 
    

        bottom_layout.addWidget(self.stack)
        bottom_layout.setStretch(0, 0)
        bottom_layout.setStretch(1, 1)

        main_layout.addWidget(bottom_container)
        self.setCentralWidget(container)

        # ===== CONNEXIONS =====

        self.header.start_monitoring.connect(self._on_start_monitoring)
        self.header.stop_monitoring.connect(self._on_stop_monitoring)
        self.header.show_monitoring.connect(
            lambda: self._navigate_to("Monitoring")
        )

        self.header.start_processing.connect(self._on_start_processing)
        self.header.show_processing.connect(
            lambda: self._navigate_to("Processing")
        )
        self.header.quit_app.connect(self.close)

        # Connecter le signal :
        self.header.open_help.connect(lambda: self._navigate_to("Help"))

        # connexions boutons prev/next
        self.toolbar_layout.go_prev.connect(self._go_prev)
        self.toolbar_layout.go_next.connect(self._go_next)


    # ===== Actions =====
    def _on_start_monitoring(self):
        self._navigate_to("Monitoring")
        self.page_monitoring.start_monitoring()

    def _on_stop_monitoring(self):
        self.page_monitoring.stop_monitoring()

    def _on_start_processing(self):
        self._navigate_to("Processing")
        self.page_processing.start_processing()

    def _go_prev(self):
        if self._history_idx > 0:
            self._history_idx -= 1
            self._navigate_to(self._history[self._history_idx], record=False)

    def _go_next(self):
        if self._history_idx < len(self._history) - 1:
            self._history_idx += 1
            self._navigate_to(self._history[self._history_idx], record=False)

    def _navigate_to(self, page_name: str, record: bool = True):
        """Navigation centrale — appelée par switch_page et les boutons."""
        if page_name.startswith("graph:"):
            graph_name = page_name[len("graph:"):]
            self.stack.setCurrentIndex(1)
            self.page_graphstats.show_graph(graph_name)
            self.toolbar_layout.set_title(graph_name)
        else:
            idx = self.page_index.get(page_name, 0)
            self.stack.setCurrentIndex(idx)
            self.toolbar_layout.set_title(page_name)
            self.navbar.highlight_page(page_name)

        if record:
            # tronquer l'historique si on est en milieu d'historique
            self._history = self._history[:self._history_idx + 1]
            self._history.append(page_name)
            self._history_idx = len(self._history) - 1

        # mettre à jour l'état des boutons
        self.toolbar_layout.btn_prev.setEnabled(self._history_idx > 0)
        self.toolbar_layout.btn_next.setEnabled(
            self._history_idx < len(self._history) - 1
        )

    # ===== Actions NavBar =====
    def switch_page(self, page_name: str):
        self._navigate_to(page_name, record=True)