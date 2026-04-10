from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QStackedWidget
from taskmonitor.gui.header import Header
from taskmonitor.gui.toolbar_layout import ToolbarLayout
from taskmonitor.gui.navbar import NavBar
from PyQt6.QtCore import Qt, pyqtSignal
from taskmonitor.gui.pages.dashboard import Dashboard
from taskmonitor.gui.pages.graph_stats import GraphStats
from taskmonitor.gui.pages.chart import Chart
import json
from taskmonitor.core.config import EXPORTS_DIR

data_path = EXPORTS_DIR / "final_output.json"

with open(data_path, "r") as f:
    data = json.load(f)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

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

        # ===== ZONE BASSE (HORIZONTALE) =====
        bottom_container = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        bottom_container.setLayout(bottom_layout)

        # ===== NAVBAR (gauche) =====
        self.navbar = NavBar()
        self.navbar.page_selected.connect(self.switch_page)
        bottom_layout.addWidget(self.navbar)

        # ===== CENTRAL AREA (droite) =====
        # ===== STACK =====
        self.stack = QStackedWidget()

        self.page_dashboard  = Dashboard(data)
        self.page_graphstats = GraphStats()
        self.page_chart      = Chart()

        self.stack.addWidget(self.page_dashboard)   # index 0
        self.stack.addWidget(self.page_graphstats)  # index 1
        self.stack.addWidget(self.page_chart)        # index 2

        # table de routing : label NavBar → index dans le stack
        self.page_index = {
            "Dashboard":      0,
            "Graphes & Stats": 1,
            "Chart":           2,
        }

        bottom_layout.addWidget(self.stack)
        bottom_layout.setStretch(0, 0)
        bottom_layout.setStretch(1, 1)

        main_layout.addWidget(bottom_container)
        self.setCentralWidget(container)

        # ===== CONNEXIONS =====
        self.header.start_monitoring.connect(self.on_monitoring)
        self.header.start_processing.connect(self.on_processing)
        self.header.quit_app.connect(self.close)

    # ===== Actions =====
    def on_monitoring(self):
        print("🔹 Monitoring lancé...")

    def on_processing(self):
        print("🔹 Processing lancé...")

    # ===== Actions NavBar =====
    def switch_page(self, page_name):
        index = self.page_index.get(page_name, 0)
        self.stack.setCurrentIndex(index)
        self.toolbar_layout.set_title(page_name)
        self.navbar.highlight_page(page_name)