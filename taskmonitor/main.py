"""
main.py
=======
Point d'entrée principal de TaskMonitor.
Lance l'application PyQt6, crée l'icône tray,
et affiche la notification de démarrage.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from taskmonitor.core import config
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


def main():
    # Initialiser les dossiers de données
    config.ensure_dirs()

    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setQuitOnLastWindowClosed(False)   # rester en tray après fermeture fenêtre

    # Vérifier que le system tray est disponible
    from PyQt6.QtWidgets import QSystemTrayIcon
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None, "Erreur",
            "Le system tray n'est pas disponible sur ce système.\n"
            "TaskMonitor nécessite un environnement desktop avec system tray."
        )
        sys.exit(1)

    # Créer l'icône tray
    from taskmonitor.gui.tray_icon import TrayIcon
    tray = TrayIcon()
    tray.show()

    # Créer la fenêtre principale (cachée au démarrage)
    from taskmonitor.gui.main_window import MainWindow
    window = MainWindow(tray)

    # Connecter les signaux tray → fenêtre
    tray.open_requested.connect(window.show)
    tray.open_requested.connect(window.raise_)
    tray.open_requested.connect(window.activateWindow)
    tray.quit_requested.connect(lambda: _quit(app, window))

    # Notification de démarrage
    tray.show_startup_notification()
    tray.notify(
        config.APP_NAME,
        "TaskMonitor est actif. Double-cliquez sur l'icône pour ouvrir.",
        duration_ms=4000,
    )

    log.info(f"TaskMonitor {config.APP_VERSION} démarré")
    sys.exit(app.exec())


def _quit(app: QApplication, window):
    """Arrêt propre : arrête le monitoring si actif, puis quitte."""
    try:
        if hasattr(window, 'monitor') and window.monitor.is_running:
            window.monitor.stop()
        if hasattr(window, 'orchestrator') and window.orchestrator.is_running:
            window.orchestrator.cancel()
    except Exception as e:
        log.error(f"Erreur à l'arrêt : {e}")
    app.quit()


if __name__ == "__main__":
    main()