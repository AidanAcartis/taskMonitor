from PyQt6.QtWidgets import (
    QToolBar, QPushButton, QWidget, QSizePolicy, QMenu
)
from PyQt6.QtCore import pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QAction
import qtawesome as qta

BG       = "#1a1a1a"
BG_HOVER = "#2e2e2e"
FG       = "#c8c8c8"
BORDER   = "#333333"

BTN_STYLE = """
    QPushButton {{
        background: transparent;
        border: none;
        border-radius: 6px;
        padding: 5px;
        color: {fg};
    }}
    QPushButton:hover {{ background: {hover}; }}
    QPushButton:pressed {{ background: #1f3a3f; }}
"""

MENU_STYLE = """
    QMenu {
        background: #1e1e1e;
        border: 1px solid #333;
        border-radius: 6px;
        padding: 4px;
        color: #c8c8c8;
        font-size: 12px;
    }
    QMenu::item {
        padding: 6px 20px;
        border-radius: 4px;
    }
    QMenu::item:selected { background: #2b2b2b; color: #00bcd4; }
"""

LEFT_STYLE = BTN_STYLE.format(fg=FG, hover=BG_HOVER)
QUIT_STYLE = BTN_STYLE.format(fg="#c0504d", hover="#2e1a1a")


def _icon_btn(icon_name, tooltip, color, style):
    btn = QPushButton()
    btn.setIcon(qta.icon(icon_name, color=color))
    btn.setIconSize(QSize(20, 20))
    btn.setFixedSize(34, 34)
    btn.setToolTip(tooltip)
    btn.setStyleSheet(style)
    return btn


class Header(QToolBar):
    start_monitoring = pyqtSignal()
    stop_monitoring  = pyqtSignal()
    show_monitoring  = pyqtSignal()
    start_processing = pyqtSignal()
    show_processing  = pyqtSignal()
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
        self.monitor_btn = _icon_btn("fa5s.circle",  "Monitoring", "#00bcd4", LEFT_STYLE)
        self.process_btn = _icon_btn("fa5s.cogs",    "Processing", FG,        LEFT_STYLE)
        self.addWidget(self.monitor_btn)
        self.addWidget(self.process_btn)

        # ── spacer ────────────────────────────────────────────────────────────
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.addWidget(spacer)

        # ── droite ────────────────────────────────────────────────────────────
        self.help_btn     = _icon_btn("fa5s.question-circle", "Aide",       FG,          LEFT_STYLE)
        self.settings_btn = _icon_btn("fa5s.sliders-h",       "Paramètres", FG,          LEFT_STYLE)
        self.quit_btn     = _icon_btn("fa5s.sign-out-alt",    "Quitter",    "#c0504d",   QUIT_STYLE)
        self.addWidget(self.help_btn)
        self.addWidget(self.settings_btn)
        self.addWidget(self.quit_btn)

        # ── popups ────────────────────────────────────────────────────────────
        self._monitor_menu = QMenu(self)
        self._monitor_menu.setStyleSheet(MENU_STYLE)
        self._monitor_menu.addAction("▶  Start monitoring",  self.start_monitoring)
        self._monitor_menu.addAction("■  Stop monitoring",   self.stop_monitoring)
        self._monitor_menu.addSeparator()
        self._monitor_menu.addAction("👁  Show monitoring",  self.show_monitoring)

        self._process_menu = QMenu(self)
        self._process_menu.setStyleSheet(MENU_STYLE)
        self._process_menu.addAction("▶  Start processing",  self.start_processing)
        self._process_menu.addSeparator()
        self._process_menu.addAction("👁  Show processing",  self.show_processing)

        # ── connexions ────────────────────────────────────────────────────────
        self.monitor_btn.clicked.connect(self._show_monitor_menu)
        self.process_btn.clicked.connect(self._show_process_menu)
        self.help_btn.clicked.connect(self.open_help)
        self.settings_btn.clicked.connect(self.open_settings)
        self.quit_btn.clicked.connect(self.quit_app)

    def _show_monitor_menu(self):
        pos = self.monitor_btn.mapToGlobal(
            QPoint(0, self.monitor_btn.height())
        )
        self._monitor_menu.exec(pos)

    def _show_process_menu(self):
        pos = self.process_btn.mapToGlobal(
            QPoint(0, self.process_btn.height())
        )
        self._process_menu.exec(pos)