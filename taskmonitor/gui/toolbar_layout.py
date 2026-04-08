from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QProgressBar
)
from PyQt6.QtCore import Qt


class ToolbarLayout(QWidget):
    def __init__(self):
        super().__init__()

        # ===== MAIN LAYOUT (VERTICAL) =====
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # =========================
        # TOP BAR (titre + boutons)
        # =========================
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(5, 0, 5, 0)
        top_layout.setSpacing(0)

        # ===== LEFT =====
        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(30, 25)

        left_layout.addWidget(self.btn_prev)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # ===== CENTER =====
        center_layout = QHBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel("Dashboard")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 14px; font-weight: bold;")

        center_layout.addWidget(self.title)

        # ===== RIGHT =====
        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedSize(30, 25)

        right_layout.addWidget(self.btn_next)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # ===== WRAPPER (équilibrage 3 zones) =====
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        top_layout.addWidget(left_widget, 1)
        top_layout.addWidget(center_widget, 1)
        top_layout.addWidget(right_widget, 1)

        # ===== WRAPPER TOP (IMPORTANT pour hauteur) =====
        top_container = QWidget()
        top_container.setLayout(top_layout)
        top_container.setFixedHeight(35)

        # =========================
        # PROGRESS BAR
        # =========================
        self.progress = QProgressBar()
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)

        # Style moderne
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #444;
            }
            QProgressBar::chunk {
                background-color: #00bcd4;
            }
        """)

        # =========================
        # ASSEMBLAGE FINAL
        # =========================
        main_layout.addWidget(top_container)
        main_layout.addWidget(self.progress)

        self.setLayout(main_layout)

        # ===== STYLE GLOBAL =====
        self.setFixedHeight(45)
        self.setStyleSheet("""
            background-color: #2b2b2b;
        """)

    # ===== API =====
    def set_title(self, text: str):
        self.title.setText(text)

    def start_loading(self):
        self.progress.setRange(0, 0)  # animation infinie

    def stop_loading(self):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)