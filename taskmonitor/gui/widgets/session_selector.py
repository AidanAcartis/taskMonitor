from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal
from taskmonitor.core.db_reader import load_all_sessions, load_available_dates, load_clusters_by_date

COMBO_STYLE = """
    QComboBox {
        background: #1e1e1e;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        min-width: 160px;
    }
    QComboBox QAbstractItemView {
        background: #1e1e1e;
        color: #c9d1d9;
        selection-background-color: #30363d;
    }
"""


class SessionSelector(QWidget):
    session_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sessions = load_all_sessions()
        self.dates    = load_available_dates()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # ── sélecteur de session ──
        lbl_s = QLabel("Session :")
        lbl_s.setStyleSheet("font-size: 12px; color: #8b949e;")
        layout.addWidget(lbl_s)

        self._session_combo = QComboBox()
        self._session_combo.setStyleSheet(COMBO_STYLE)
        self._session_combo.addItem("— session —", userData=None)
        for _, session_date, _ in self.sessions:
            self._session_combo.addItem(session_date, userData=session_date)
        self._session_combo.currentIndexChanged.connect(self._on_session_changed)
        layout.addWidget(self._session_combo)

        # ── sélecteur de date ──
        lbl_d = QLabel("Date :")
        lbl_d.setStyleSheet("font-size: 12px; color: #8b949e;")
        layout.addWidget(lbl_d)

        self._date_combo = QComboBox()
        self._date_combo.setStyleSheet(COMBO_STYLE)
        self._date_combo.addItem("— date —", userData=None)
        for date_str in self.dates:
            self._date_combo.addItem(date_str, userData=date_str)
        self._date_combo.currentIndexChanged.connect(self._on_date_changed)
        layout.addWidget(self._date_combo)

    def _on_session_changed(self, index: int):
        if index == 0:
            return
        # réinitialiser date sans déclencher son signal
        self._date_combo.blockSignals(True)
        self._date_combo.setCurrentIndex(0)
        self._date_combo.blockSignals(False)

        session_index = index - 1
        if 0 <= session_index < len(self.sessions):
            _, _, data = self.sessions[session_index]
            self.session_changed.emit(data)

    def _on_date_changed(self, index: int):
        if index == 0:
            return
        # réinitialiser session sans déclencher son signal
        self._session_combo.blockSignals(True)
        self._session_combo.setCurrentIndex(0)
        self._session_combo.blockSignals(False)

        date_str = self._date_combo.currentData()
        if date_str:
            data = load_clusters_by_date(date_str)
            self.session_changed.emit(data)

    def current_data(self) -> dict:
        """Retourne les données de la session/date actuellement sélectionnée."""
        s_idx = self._session_combo.currentIndex()
        if s_idx > 0:
            return self.sessions[s_idx - 1][2]
        d_idx = self._date_combo.currentIndex()
        if d_idx > 0:
            return load_clusters_by_date(self._date_combo.currentData())
        # par défaut : session la plus récente
        return self.sessions[0][2] if self.sessions else {"clusters": []}