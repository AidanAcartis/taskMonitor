"""
gui/main_window.py
==================
Fenêtre principale de l'application TaskMonitor.
Contient la sidebar de navigation, le dashboard principal,
et gère les interactions avec l'orchestrateur.
"""

from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QMessageBox, QSizePolicy,
    QStackedWidget, QSpacerItem,
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor

from taskmonitor.core import config, storage
from taskmonitor.orchestrator import Orchestrator
from taskmonitor.gui.dashboard import Dashboard
from taskmonitor.gui.pipeline_dialog import PipelineDialog
from taskmonitor.gui.tray_icon import TrayIcon
from taskmonitor.collectors.window_monitor import WindowMonitor, is_wmctrl_available
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────
# BOUTON DE SIDEBAR
# ─────────────────────────────────────────────

class SidebarButton(QPushButton):
    """Bouton de navigation dans la sidebar."""

    STYLE_INACTIVE = """
        QPushButton {
            background-color: transparent;
            color: #64748B;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            text-align: left;
            font-size: 11px;
        }
        QPushButton:hover {
            background-color: #1A1D27;
            color: #E2E8F0;
        }
    """
    STYLE_ACTIVE = """
        QPushButton {
            background-color: #1E2238;
            color: #6366F1;
            border: none;
            border-left: 3px solid #6366F1;
            border-radius: 0px;
            padding: 10px 16px;
            text-align: left;
            font-size: 11px;
            font-weight: bold;
        }
    """

    def __init__(self, icon_char: str, label: str, parent=None):
        super().__init__(f"  {icon_char}   {label}", parent)
        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_active(False)

    def set_active(self, active: bool):
        self.setStyleSheet(self.STYLE_ACTIVE if active else self.STYLE_INACTIVE)


# ─────────────────────────────────────────────
# FENÊTRE PRINCIPALE
# ─────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""

    MAIN_STYLE = """
        QMainWindow, QWidget#central {
            background-color: #0F1117;
        }
        QFrame#sidebar {
            background-color: #0A0C13;
            border-right: 1px solid #1A1D27;
        }
        QLabel#app_name {
            color: #6366F1;
            font-size: 16px;
            font-weight: bold;
        }
        QLabel#app_version {
            color: #2A2D3E;
            font-size: 9px;
        }
        QLabel#section_label {
            color: #2A2D3E;
            font-size: 9px;
            letter-spacing: 2px;
        }
        QPushButton#btn_run {
            background-color: #6366F1;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 11px;
            font-weight: bold;
        }
        QPushButton#btn_run:hover {
            background-color: #4F46E5;
        }
        QPushButton#btn_run:disabled {
            background-color: #1A1D27;
            color: #2A2D3E;
        }
        QPushButton#btn_monitor {
            background-color: #14B8A6;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 10px;
        }
        QPushButton#btn_monitor:hover {
            background-color: #0D9488;
        }
        QPushButton#btn_monitor_off {
            background-color: #1A1D27;
            color: #F87171;
            border: 1px solid #F8717133;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 10px;
        }
        QLabel#status_lbl {
            color: #475569;
            font-size: 10px;
        }
        QLabel#monitoring_dot {
            font-size: 10px;
        }
    """

    def __init__(self, tray: TrayIcon):
        super().__init__()
        self.tray         = tray
        self.orchestrator = Orchestrator(self)
        self.monitor      = WindowMonitor()
        self._monitoring  = False

        self.setWindowTitle(config.APP_NAME)
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(self.MAIN_STYLE)

        self._build_ui()
        self._connect_signals()

        # Charger les données du jour si disponibles
        self._dashboard.refresh_dates()

    # ─────────────────────────────────────────
    # CONSTRUCTION UI
    # ─────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)

        # Logo / nom
        logo_widget = QWidget()
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(20, 24, 20, 20)
        app_name = QLabel(config.APP_NAME)
        app_name.setObjectName("app_name")
        app_ver  = QLabel(f"v{config.APP_VERSION}")
        app_ver.setObjectName("app_version")
        logo_layout.addWidget(app_name)
        logo_layout.addWidget(app_ver)
        side_layout.addWidget(logo_widget)

        # Séparateur
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("color: #1A1D27;")
        side_layout.addWidget(sep1)

        # Navigation
        nav_label = QLabel("NAVIGATION")
        nav_label.setObjectName("section_label")
        nav_label.setContentsMargins(20, 14, 0, 6)
        side_layout.addWidget(nav_label)

        self._btn_dashboard = SidebarButton("◈", "Dashboard")
        self._btn_dashboard.clicked.connect(lambda: self._show_page(0))
        self._btn_dashboard.set_active(True)
        side_layout.addWidget(self._btn_dashboard)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #1A1D27; margin: 8px 0;")
        side_layout.addWidget(sep2)

        # Section contrôles
        ctrl_label = QLabel("CONTRÔLES")
        ctrl_label.setObjectName("section_label")
        ctrl_label.setContentsMargins(20, 8, 0, 6)
        side_layout.addWidget(ctrl_label)

        # Bouton monitoring
        self._btn_monitor = QPushButton("▶  Démarrer le monitoring")
        self._btn_monitor.setObjectName("btn_monitor")
        self._btn_monitor.setMinimumHeight(40)
        self._btn_monitor.setContentsMargins(16, 0, 16, 0)
        self._btn_monitor.clicked.connect(self._toggle_monitoring)
        mon_wrapper = QWidget()
        mon_wl = QVBoxLayout(mon_wrapper)
        mon_wl.setContentsMargins(12, 4, 12, 4)
        mon_wl.addWidget(self._btn_monitor)
        side_layout.addWidget(mon_wrapper)

        # Statut monitoring
        self._monitoring_status = QLabel("● Monitoring inactif")
        self._monitoring_status.setObjectName("monitoring_dot")
        self._monitoring_status.setStyleSheet("color: #475569;")
        self._monitoring_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(self._monitoring_status)

        side_layout.addSpacerItem(QSpacerItem(0, 12))

        # Bouton lancer analyse
        self._btn_run = QPushButton("⚡  Lancer l'analyse")
        self._btn_run.setObjectName("btn_run")
        self._btn_run.setMinimumHeight(44)
        run_wrapper = QWidget()
        run_wl = QVBoxLayout(run_wrapper)
        run_wl.setContentsMargins(12, 4, 12, 4)
        run_wl.addWidget(self._btn_run)
        side_layout.addWidget(run_wrapper)

        side_layout.addStretch()

        # Statut en bas
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet("color: #1A1D27;")
        side_layout.addWidget(sep3)

        self._status_lbl = QLabel(f"Prêt  ·  {datetime.now().strftime('%Y-%m-%d')}")
        self._status_lbl.setObjectName("status_lbl")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setContentsMargins(0, 10, 0, 10)
        side_layout.addWidget(self._status_lbl)

        main_layout.addWidget(sidebar)

        # ── Zone centrale ────────────────────
        self._pages = QStackedWidget()
        self._dashboard = Dashboard()
        self._pages.addWidget(self._dashboard)
        main_layout.addWidget(self._pages)

    def _connect_signals(self):
        self._btn_run.clicked.connect(self._launch_pipeline)

        # Tray → fenêtre
        self.tray.run_pipeline.connect(self._launch_pipeline)
        self.tray.monitoring_toggled.connect(self._set_monitoring)

        # Orchestrateur → UI
        self.orchestrator.finished.connect(self._on_pipeline_finished)

    # ─────────────────────────────────────────
    # NAVIGATION
    # ─────────────────────────────────────────

    def _show_page(self, index: int):
        self._pages.setCurrentIndex(index)
        self._btn_dashboard.set_active(index == 0)

    # ─────────────────────────────────────────
    # MONITORING
    # ─────────────────────────────────────────

    def _toggle_monitoring(self):
        self._set_monitoring(not self._monitoring)

    @pyqtSlot(bool)
    def _set_monitoring(self, active: bool):
        if active and not is_wmctrl_available():
            QMessageBox.warning(
                self, "wmctrl manquant",
                "wmctrl n'est pas installé sur ce système.\n\n"
                "Installer avec :\n  sudo apt install wmctrl",
            )
            return

        self._monitoring = active
        if active:
            self.monitor.start()
            self._btn_monitor.setText("⏹  Arrêter le monitoring")
            self._btn_monitor.setObjectName("btn_monitor_off")
            self._monitoring_status.setText("● Monitoring actif")
            self._monitoring_status.setStyleSheet("color: #4ADE80;")
            self.tray.set_monitoring_active(True)
            log.info("Monitoring démarré")
        else:
            self.monitor.stop()
            self._btn_monitor.setText("▶  Démarrer le monitoring")
            self._btn_monitor.setObjectName("btn_monitor")
            self._monitoring_status.setText("● Monitoring inactif")
            self._monitoring_status.setStyleSheet("color: #475569;")
            self.tray.set_monitoring_active(False)
            log.info("Monitoring arrêté")

        # Forcer le rechargement du style
        self._btn_monitor.setStyleSheet("")
        self._btn_monitor.update()

    # ─────────────────────────────────────────
    # PIPELINE
    # ─────────────────────────────────────────

    def _launch_pipeline(self):
        if self.orchestrator.is_running:
            return

        date_str = datetime.now().strftime("%Y-%m-%d")

        dialog = PipelineDialog(self.orchestrator, date_str, parent=self)
        self.orchestrator.start(date_str)
        dialog.exec()

    @pyqtSlot(bool)
    def _on_pipeline_finished(self, success: bool):
        self._btn_run.setEnabled(True)
        if success:
            self._dashboard.refresh_dates()
            self._status_lbl.setText("Analyse terminée ✓")
            self.tray.notify(
                config.APP_NAME,
                "Analyse terminée ! Ouvrez l'app pour voir les résultats.",
            )
        else:
            self._status_lbl.setText("Erreur lors de l'analyse")

    # ─────────────────────────────────────────
    # GESTION FERMETURE → TRAY
    # ─────────────────────────────────────────

    def closeEvent(self, event):
        """Minimise dans le tray au lieu de quitter."""
        event.ignore()
        self.hide()
        self.tray.notify(
            config.APP_NAME,
            "TaskMonitor tourne en arrière-plan. "
            "Double-cliquez sur l'icône pour le rouvrir.",
            duration_ms=3000,
        )