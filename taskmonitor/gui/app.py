import sys
from PyQt6.QtWidgets import QApplication
from taskmonitor.gui.main_window import MainWindow

def run():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()