from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar,
    QPushButton
)
from PyQt6.QtCore import Qt


class ToolbarLayout(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # 🔥 collé au toolbar
        main_layout.setSpacing(0)

        # ===== LEFT =====
        left_layout = QHBoxLayout()
        self.btn_prev = QPushButton("<")
        left_layout.addWidget(self.btn_prev)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # ===== CENTER =====
        center_layout = QHBoxLayout()
        self.title = QLabel("Dashboard")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 16px; font-weight: bold;")
        center_layout.addWidget(self.title)
        self.setFixedHeight(40)

        self.setStyleSheet("""
            background-color: #2b2b2b;
            border-top: none;
            margin-top: 0px;
            padding-top: 0px;
            """)

        # ===== RIGHT =====
        right_layout = QHBoxLayout()
        self.btn_next = QPushButton(">")
        right_layout.addWidget(self.btn_next)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # ===== WRAPPER WIDGETS (IMPORTANT) =====
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # 🔥 LES 3 PRENNENT LA MÊME PLACE
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(center_widget, 1)
        main_layout.addWidget(right_widget, 1)

        self.setLayout(main_layout)

    # ===== API =====
    def set_title(self, text: str):
        self.title.setText(text)