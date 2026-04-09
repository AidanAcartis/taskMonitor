from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

class NavBar(QWidget):
    # Signal pour notifier le MainWindow du changement de page
    page_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setFixedWidth(150) # Largeur fix pour la barre de navigation
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            background-color: #1e1e1e;
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Liste des pages
        self.pages = ["Dashboard", "Graphes & Stats", "Chart"]
        self.buttons = {}

        for page in self.pages:
            btn = QPushButton(page)
            btn.setStyleSheet("""
                QPushButton {
                    color: white;
                    background-color: transparent;
                    border: none;
                    text-align: left;
                    padding-left: 10px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #2b2b2b;
                }
                QPushButton:pressed {
                    background-color: #00bcd4;
                }
            """)
            btn.setFixedHeight(20)
            btn.clicked.connect(lambda checked, p=page: self.on_button_click(p))
            layout.addWidget(btn)
            self.buttons[page] = btn

        # Pousser les bouttons en haut
        layout.addStretch()
        self.setLayout(layout)

    def on_button_click(self, page_name):
        self.page_selected.emit(page_name)


    #Surligner la page active
    def highlight_page(self, page_name):
        for name, btn in self.buttons.items():
            if name == page_name:
                btn.setStyleSheet("""
                    QPushButton {
                        color: #00bcd4;
                        background-color: #2b2b2b;
                        border: none;
                        text-align: left;
                        padding-left: 10px;
                        font-size: 13px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        color: white;
                        background-color: transparent;
                        border: none;
                        text-align: left;
                        padding-left: 10px;
                        font-size: 13px;
                    }
                """)
