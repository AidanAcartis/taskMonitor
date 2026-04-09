from PyQt6.QtWidgets import QToolBar, QPushButton, QWidget, QSizePolicy
from PyQt6.QtCore import pyqtSignal


class Header(QToolBar):
    # ===== SIGNALS =====
    start_monitoring = pyqtSignal()
    start_processing = pyqtSignal()
    open_help = pyqtSignal()
    open_settings = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self):
        super().__init__("Main Toolbar")

        # Empêche le déplacement (optionnel)
        self.setMovable(False)

        self.setStyleSheet("""
            QToolBar {
                margin: 0px;
                padding: 0px;
            }
            """)

        # ===== GAUCHE =====
        self.monitor_btn = QPushButton("Monitoring")
        self.process_btn = QPushButton("Processing")

        self.addWidget(self.monitor_btn)
        self.addWidget(self.process_btn)

        # ===== SPACER (push droite) =====
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.addWidget(spacer)

        # ===== DROITE =====
        self.help_btn = QPushButton("Aide")
        self.settings_btn = QPushButton("Paramètres")
        self.quit_btn = QPushButton("Quitter")

        self.addWidget(self.help_btn)
        self.addWidget(self.settings_btn)
        self.addWidget(self.quit_btn)

        # ===== CONNEXIONS =====
        self.monitor_btn.clicked.connect(self.start_monitoring)
        self.process_btn.clicked.connect(self.start_processing)
        self.help_btn.clicked.connect(self.open_help)
        self.settings_btn.clicked.connect(self.open_settings)
        self.quit_btn.clicked.connect(self.quit_app)