from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QProgressBar
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
import qtawesome as qta


BG       = "#1e1e1e"
BG_BTN   = "transparent"
BG_HOVER = "#2e2e2e"
FG       = "#c8c8c8"
FG_TITLE = "#e0e0e0"
ACCENT   = "#00bcd4"
BORDER   = "#2a2a2a"

BTN_STYLE = f"""
    QPushButton {{
        background: {BG_BTN};
        border: none;
        border-radius: 6px;
        padding: 4px;
        color: {FG};
    }}
    QPushButton:hover {{ background: {BG_HOVER}; }}
    QPushButton:pressed {{ background: #1f3a3f; }}
"""


class ToolbarLayout(QWidget):
    go_prev = pyqtSignal()  # ← ajouter
    go_next = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG};
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── top bar ───────────────────────────────────────────────────────────
        top = QWidget()
        top.setFixedHeight(40)
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(8, 0, 8, 0)
        top_layout.setSpacing(0)

        # left
        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(qta.icon("fa5s.chevron-left", color=FG))
        self.btn_prev.setIconSize(QSize(13, 13))
        self.btn_prev.setFixedSize(28, 28)
        self.btn_prev.setStyleSheet(BTN_STYLE)
        self.btn_prev.setToolTip("Précédent")

        left_w = QWidget()
        left_l = QHBoxLayout(left_w)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.addWidget(self.btn_prev)
        left_l.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # center
        self.title = QLabel("Dashboard")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {FG_TITLE};
            letter-spacing: 0.5px;
        """)

        center_w = QWidget()
        center_l = QHBoxLayout(center_w)
        center_l.setContentsMargins(0, 0, 0, 0)
        center_l.addWidget(self.title)

        # right
        self.btn_next = QPushButton()
        self.btn_next.setIcon(qta.icon("fa5s.chevron-right", color=FG))
        self.btn_next.setIconSize(QSize(13, 13))
        self.btn_next.setFixedSize(28, 28)
        self.btn_next.setStyleSheet(BTN_STYLE)
        self.btn_next.setToolTip("Suivant")

        right_w = QWidget()
        right_l = QHBoxLayout(right_w)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.addWidget(self.btn_next)
        right_l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        top_layout.addWidget(left_w,   1)
        top_layout.addWidget(center_w, 1)
        top_layout.addWidget(right_w,  1)

        # ── progress bar ──────────────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setFixedHeight(2)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {BORDER};
                border: none;
                border-radius: 0px;
            }}
            QProgressBar::chunk {{
                background: {ACCENT};
                border-radius: 0px;
            }}
        """)

        # connecter les boutons aux signaux
        self.btn_prev.clicked.connect(self.go_prev)
        self.btn_next.clicked.connect(self.go_next)

        main_layout.addWidget(top)
        main_layout.addWidget(self.progress)

    # ── API ───────────────────────────────────────────────────────────────────

    def set_title(self, text: str):
        self.title.setText(text)

    def start_loading(self):
        self.progress.setRange(0, 0)

    def stop_loading(self):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)