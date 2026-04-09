from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from taskmonitor.gui.header import Header
from taskmonitor.gui.toolbar_layout import ToolbarLayout
from taskmonitor.gui.navbar import NavBar
from PyQt6.QtCore import Qt, pyqtSignal


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
        self.central_area = QWidget()
        self.central_area.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.central_area.setStyleSheet("background-color: 2b2b2b;")

        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_area.setLayout(central_layout)

        self.central_label = QLabel("Dashboard")
        self.central_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(self.central_label)

        bottom_layout.addWidget(self.central_area)

        # 🔥 IMPORTANT : permet au central de prendre tout l'espace restant
        bottom_layout.setStretch(0, 0)  # navbar fixe
        bottom_layout.setStretch(1, 1)  # central expand

        # ===== AJOUT FINAL =====
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
        print(f"🌟 Page sélectionnée : {page_name}")
        self.central_label.setText(page_name)
        self.toolbar_layout.set_title(page_name)
        self.navbar.highlight_page(page_name)