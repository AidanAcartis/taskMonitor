"""
autostart/install_autostart.py
================================
Installe le fichier .desktop pour :
  1. L'autostart au démarrage de la session (~/.config/autostart/)
  2. L'icône dans le menu des applications (~/.local/share/applications/)
  3. L'icône dans le dossier Desktop (~/Bureau/ ou ~/Desktop/)

Appelé automatiquement après pip install ou manuellement.
"""

import shutil
import subprocess
from pathlib import Path

from taskmonitor.core import config
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


DESKTOP_CONTENT = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={config.APP_NAME}
Comment={config.APP_DESCRIPTION}
Exec=taskmonitor
Icon={config.ICON_PATH}
Terminal=false
Categories=Utility;Monitor;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""


def install():
    """Lance l'installation complète de l'autostart et des raccourcis."""
    results = {
        "autostart": _install_autostart(),
        "applications": _install_app_menu(),
        "desktop_shortcut": _install_desktop_shortcut(),
    }
    _update_desktop_db()
    return results


def _install_autostart() -> bool:
    """Installe dans ~/.config/autostart/ pour démarrage automatique."""
    target = config.AUTOSTART_DIR / "taskmonitor.desktop"
    try:
        config.AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
        target.write_text(DESKTOP_CONTENT, encoding="utf-8")
        target.chmod(0o755)
        log.info(f"Autostart installé : {target}")
        return True
    except Exception as e:
        log.error(f"Erreur autostart : {e}")
        return False


def _install_app_menu() -> bool:
    """Installe dans ~/.local/share/applications/ pour le menu des apps."""
    target = config.DESKTOP_DIR / "taskmonitor.desktop"
    try:
        config.DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
        target.write_text(DESKTOP_CONTENT, encoding="utf-8")
        target.chmod(0o755)
        log.info(f"Menu applications installé : {target}")
        return True
    except Exception as e:
        log.error(f"Erreur menu applications : {e}")
        return False


def _install_desktop_shortcut() -> bool:
    """Crée un raccourci sur le bureau de l'utilisateur."""
    # Essayer Bureau (français) puis Desktop (anglais)
    for name in ["Bureau", "Desktop"]:
        desktop_dir = Path.home() / name
        if desktop_dir.exists():
            target = desktop_dir / "taskmonitor.desktop"
            try:
                target.write_text(DESKTOP_CONTENT, encoding="utf-8")
                target.chmod(0o755)
                # Marquer comme digne de confiance (GNOME)
                subprocess.run(
                    ["gio", "set", str(target), "metadata::trusted", "true"],
                    capture_output=True, timeout=5
                )
                log.info(f"Raccourci bureau créé : {target}")
                return True
            except Exception as e:
                log.warning(f"Raccourci bureau échoué : {e}")
    return False


def _update_desktop_db():
    """Met à jour la base de données des applications desktop."""
    try:
        subprocess.run(
            ["update-desktop-database",
             str(config.DESKTOP_DIR)],
            capture_output=True, timeout=10
        )
    except Exception:
        pass   # Non critique


def uninstall():
    """Supprime tous les raccourcis et l'autostart."""
    targets = [
        config.AUTOSTART_DIR / "taskmonitor.desktop",
        config.DESKTOP_DIR  / "taskmonitor.desktop",
    ]
    for name in ["Bureau", "Desktop"]:
        targets.append(Path.home() / name / "taskmonitor.desktop")

    for t in targets:
        if t.exists():
            t.unlink()
            log.info(f"Supprimé : {t}")


if __name__ == "__main__":
    results = install()
    for k, v in results.items():
        status = "✓" if v else "✗"
        print(f"  {status}  {k}")