from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from taskmonitor.gui.header import Header
from taskmonitor.gui.toolbar_layout import ToolbarLayout


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

        # Zone centrale
        self.central_label = QLabel("T")
        main_layout.addWidget(self.central_label)

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