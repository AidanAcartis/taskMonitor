from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal


STYLE_BTN = """
    QPushButton {{
        color: {color};
        background-color: {bg};
        border: none;
        text-align: left;
        padding-left: {indent}px;
        font-size: {size}px;
    }}
    QPushButton:hover {{ background-color: #2b2b2b; }}
"""

SUBGRAPHS = [
    "Activity Duration",
    "Gantt / Timeline",
    "Task Proportion",
    "App Proportion",
    "Domain Proportion",
    "Activity Heatmap",
]


class NavBar(QWidget):
    page_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(160)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #1e1e1e;")

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.buttons = {}           # name -> QPushButton  (top-level only)
        self.sub_buttons = {}       # name -> QPushButton  (sub-items)
        self._submenu_visible = False
        self._sub_widgets = []      # list of sub QPushButtons to show/hide

        top_pages = ["Dashboard", "Graphes & Stats", "Chart"]
        for page in top_pages:
            btn = self._make_top_btn(page)
            self._layout.addWidget(btn)
            self.buttons[page] = btn

            if page == "Graphes & Stats":
                for sub in SUBGRAPHS:
                    sbtn = self._make_sub_btn(sub)
                    sbtn.hide()
                    self._layout.addWidget(sbtn)
                    self.sub_buttons[sub] = sbtn
                    self._sub_widgets.append(sbtn)

        self._layout.addStretch()
        self.setLayout(self._layout)

    # ── factory helpers ────────────────────────────────────────────────────────

    def _make_top_btn(self, name: str) -> QPushButton:
        btn = QPushButton(name)
        btn.setFixedHeight(28)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setStyleSheet(STYLE_BTN.format(color="white", bg="transparent", indent=10, size=13))
        btn.clicked.connect(lambda checked, p=name: self._on_top_click(p))
        return btn

    def _make_sub_btn(self, name: str) -> QPushButton:
        btn = QPushButton(name)
        btn.setFixedHeight(24)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setStyleSheet(STYLE_BTN.format(color="#aaaaaa", bg="transparent", indent=22, size=11))
        btn.clicked.connect(lambda checked, p=name: self._on_sub_click(p))
        return btn

    # ── click handlers ─────────────────────────────────────────────────────────

    def _on_top_click(self, page_name: str):
        if page_name == "Graphes & Stats":
            self._toggle_submenu()
        self.page_selected.emit(page_name)
        self.highlight_page(page_name)

    def _on_sub_click(self, sub_name: str):
        self.page_selected.emit("graph:" + sub_name)
        self._highlight_sub(sub_name)

    def _toggle_submenu(self):
        self._submenu_visible = not self._submenu_visible
        for w in self._sub_widgets:
            w.setVisible(self._submenu_visible)
        # update arrow indicator on the parent button
        arrow = "▾" if self._submenu_visible else "▸"
        self.buttons["Graphes & Stats"].setText(f"Graphes & Stats {arrow}")

    # ── highlight helpers ──────────────────────────────────────────────────────

    def highlight_page(self, page_name: str):
        for name, btn in self.buttons.items():
            active = (name == page_name)
            color  = "#00bcd4" if active else "white"
            bg     = "#2b2b2b" if active else "transparent"
            btn.setStyleSheet(STYLE_BTN.format(color=color, bg=bg, indent=10, size=13))
        # reset sub-buttons to normal when switching top-level pages
        if page_name != "Graphes & Stats":
            for sbtn in self.sub_buttons.values():
                sbtn.setStyleSheet(STYLE_BTN.format(
                    color="#aaaaaa", bg="transparent", indent=22, size=11))

    def _highlight_sub(self, sub_name: str):
        # dim the top-level button, highlight the sub-item
        self.buttons["Graphes & Stats"].setStyleSheet(
            STYLE_BTN.format(color="#00bcd4", bg="#2b2b2b", indent=10, size=13))
        for name, sbtn in self.sub_buttons.items():
            active = (name == sub_name)
            color  = "#00bcd4" if active else "#aaaaaa"
            bg     = "#252525" if active else "transparent"
            sbtn.setStyleSheet(STYLE_BTN.format(color=color, bg=bg, indent=22, size=11))