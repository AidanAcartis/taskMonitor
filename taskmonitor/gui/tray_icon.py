"""
gui/tray_icon.py
================
Icône dans le system tray Linux.
Menu contextuel : Ouvrir / Lancer analyse / Quitter.
Notification au démarrage : proposition d'activer le monitoring.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from taskmonitor.core import config
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


def _make_default_icon(size: int = 64, color: str = "#6366F1") -> QIcon:
    """
    Génère une icône par défaut (carré coloré avec lettre T)
    si assets/icon.png est absent.
    """
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, size - 8, size - 8, 12, 12)
    painter.setPen(QColor("white"))
    font = painter.font()
    font.setPixelSize(size // 2)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "T")
    painter.end()
    return QIcon(px)


class TrayIcon(QObject):
    """
    Gère l'icône dans la barre système.
    Émet des signaux pour communiquer avec la fenêtre principale.
    """

    open_requested      = pyqtSignal()   # ouvrir la fenêtre principale
    run_pipeline        = pyqtSignal()   # lancer l'analyse
    monitoring_toggled  = pyqtSignal(bool)  # activer/désactiver monitoring
    quit_requested      = pyqtSignal()   # quitter l'application

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitoring_active = False

        # Charger l'icône
        icon_path = config.ICON_PATH
        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            icon = _make_default_icon()

        # Créer le tray
        self._tray = QSystemTrayIcon(icon)
        self._tray.setToolTip(config.APP_NAME)
        self._tray.activated.connect(self._on_activated)

        # Menu contextuel
        self._menu = QMenu()
        self._menu.setStyleSheet("""
            QMenu {
                background-color: #1A1D27;
                color: #E2E8F0;
                border: 1px solid #2A2D3E;
                border-radius: 6px;
                padding: 4px;
                font-size: 11px;
            }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background-color: #2A2D3E; }
            QMenu::separator { height: 1px; background: #2A2D3E; margin: 4px 8px; }
        """)

        self._action_open     = self._menu.addAction("Ouvrir TaskMonitor")
        self._action_open.triggered.connect(self.open_requested)

        self._menu.addSeparator()

        self._action_monitor  = self._menu.addAction("▶  Activer le monitoring")
        self._action_monitor.triggered.connect(self._toggle_monitoring)

        self._action_run      = self._menu.addAction("⚡  Lancer l'analyse")
        self._action_run.triggered.connect(self.run_pipeline)

        self._menu.addSeparator()

        self._action_quit     = self._menu.addAction("Quitter")
        self._action_quit.triggered.connect(self.quit_requested)

        self._tray.setContextMenu(self._menu)

    def show(self):
        self._tray.show()

    def hide(self):
        self._tray.hide()

    def notify(self, title: str, message: str, duration_ms: int = 5000):
        """Affiche une notification système (bulle)."""
        self._tray.showMessage(title, message,
                               QSystemTrayIcon.MessageIcon.Information,
                               duration_ms)

    def set_monitoring_active(self, active: bool):
        self._monitoring_active = active
        if active:
            self._action_monitor.setText("⏹  Arrêter le monitoring")
            self._tray.setToolTip(f"{config.APP_NAME}  ·  Monitoring actif")
        else:
            self._action_monitor.setText("▶  Activer le monitoring")
            self._tray.setToolTip(config.APP_NAME)

    def show_startup_notification(self):
        """
        Affiche la notification au démarrage :
        'Would you like to start monitoring today?'
        """
        self.notify(
            config.APP_NAME,
            "Voulez-vous activer le monitoring aujourd'hui ?\n"
            "Cliquez ici ou ouvrez l'application.",
            duration_ms=8000,
        )

    # ── Slots privés ─────────────────────────

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_requested.emit()

    def _toggle_monitoring(self):
        self._monitoring_active = not self._monitoring_active
        self.set_monitoring_active(self._monitoring_active)
        self.monitoring_toggled.emit(self._monitoring_active)