from PyQt6.QtWidgets import QToolBar, QPushButton, QWidget, QSizePolicy
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QIcon
import qtawesome as qta


BG       = "#1a1a1a"
BG_HOVER = "#2e2e2e"
FG       = "#c8c8c8"
FG_ACT   = "#00bcd4"
BORDER   = "#333333"

BTN_STYLE = """
    QPushButton {{
        background: transparent;
        border: none;
        border-radius: 6px;
        padding: 5px;
        color: {fg};
    }}
    QPushButton:hover {{
        background: {hover};
    }}
    QPushButton:pressed {{
        background: #1f3a3f;
    }}
"""

LEFT_STYLE  = BTN_STYLE.format(fg=FG,     hover=BG_HOVER)
RIGHT_STYLE = BTN_STYLE.format(fg=FG,     hover=BG_HOVER)
QUIT_STYLE  = BTN_STYLE.format(fg="#c0504d", hover="#2e1a1a")


def _icon_btn(icon_name: str, tooltip: str, color: str, style: str) -> QPushButton:
    btn = QPushButton()
    btn.setIcon(qta.icon(icon_name, color=color))
    btn.setIconSize(QSize(20, 20))
    btn.setFixedSize(34, 34)
    btn.setToolTip(tooltip)
    btn.setStyleSheet(style)
    return btn


class Header(QToolBar):
    start_monitoring = pyqtSignal()
    start_processing = pyqtSignal()
    open_help        = pyqtSignal()
    open_settings    = pyqtSignal()
    quit_app         = pyqtSignal()

    def __init__(self):
        super().__init__("Main Toolbar")
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))
        self.setStyleSheet(f"""
            QToolBar {{
                background: {BG};
                border-bottom: 1px solid {BORDER};
                margin: 0px;
                padding: 3px 8px;
                spacing: 4px;
            }}
            QToolTip {{
                background: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }}
        """)

        # ── gauche ────────────────────────────────────────────────────────────
        self.monitor_btn  = _icon_btn("fa5s.circle",     "Monitoring",  "#00bcd4", LEFT_STYLE)
        self.process_btn  = _icon_btn("fa5s.cogs",       "Processing",  FG,        LEFT_STYLE)

        self.addWidget(self.monitor_btn)
        self.addWidget(self.process_btn)

        # ── spacer ────────────────────────────────────────────────────────────
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.addWidget(spacer)

        # ── droite ────────────────────────────────────────────────────────────
        self.help_btn     = _icon_btn("fa5s.question-circle", "Aide",       FG,        RIGHT_STYLE)
        self.settings_btn = _icon_btn("fa5s.sliders-h",       "Paramètres", FG,        RIGHT_STYLE)
        self.quit_btn     = _icon_btn("fa5s.sign-out-alt",    "Quitter",    "#c0504d", QUIT_STYLE)

        self.addWidget(self.help_btn)
        self.addWidget(self.settings_btn)
        self.addWidget(self.quit_btn)

        # ── connexions ────────────────────────────────────────────────────────
        self.monitor_btn.clicked.connect(self.start_monitoring)
        self.process_btn.clicked.connect(self.start_processing)
        self.help_btn.clicked.connect(self.open_help)
        self.settings_btn.clicked.connect(self.open_settings)
        self.quit_btn.clicked.connect(self.quit_app)