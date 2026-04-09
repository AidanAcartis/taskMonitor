from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QColor
from PyQt6.QtWebEngineCore import QWebEngineSettings

from .heatmap_altair import build_dataframe, build_chart


class AltairHeatmap(QWidget):
    def __init__(self, data):
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.webview = QWebEngineView()
        # Fond sombre pour correspondre au thème
        self.webview.page().setBackgroundColor(QColor("#edf0f5"))
        self.webview.setFixedHeight(160)
        layout.addWidget(self.webview)

        self.load_chart(data)

    def load_chart(self, data):
        df = build_dataframe(data)
        chart = build_chart(df)

        # Injecter un fond sombre dans le HTML généré
        html = chart.to_html()
        html = html.replace(
            "<body>",
            "<body style='background-color:#0d1117; margin:8px;'>"
        )
        self.webview.setHtml(html)