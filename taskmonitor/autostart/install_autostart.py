"""
autostart/install_autostart.py
================================
Installs the .desktop file for:
  1. Autostart at session startup (~/.config/autostart/)
  2. Application menu icon (~/.local/share/applications/)
  3. Desktop icon (~/Bureau/ or ~/Desktop/)

Called automatically after pip install or manually.
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
    """Launches the complete installation of autostart and shortcuts."""
    results = {
        "autostart": _install_autostart(),
        "applications": _install_app_menu(),
        "desktop_shortcut": _install_desktop_shortcut(),
    }
    _update_desktop_db()
    return results


def _install_autostart() -> bool:
    """Installs in ~/.config/autostart/ for automatic startup."""
    target = config.AUTOSTART_DIR / "taskmonitor.desktop"
    try:
        config.AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
        target.write_text(DESKTOP_CONTENT, encoding="utf-8")
        target.chmod(0o755)
        log.info(f"Autostart installed : {target}")
        return True
    except Exception as e:
        log.error(f"Error installing autostart : {e}")
        return False


def _install_app_menu() -> bool:
    """Installs in ~/.local/share/applications/ for the applications menu."""
    target = config.DESKTOP_DIR / "taskmonitor.desktop"
    try:
        config.DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
        target.write_text(DESKTOP_CONTENT, encoding="utf-8")
        target.chmod(0o755)
        log.info(f"Installed applications menu : {target}")
        return True
    except Exception as e:
        log.error(f"Error installing applications menu : {e}")
        return False


def _install_desktop_shortcut() -> bool:
    """Creates a shortcut on the user's desktop."""
    # Try Bureau (French) then Desktop (English)
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
                log.info(f"Desktop shortcut created : {target}")
                return True
            except Exception as e:
                log.warning(f"Failed to create desktop shortcut : {e}")
    return False


def _update_desktop_db():
    """Updates the desktop application database."""
    try:
        subprocess.run(
            ["update-desktop-database",
             str(config.DESKTOP_DIR)],
            capture_output=True, timeout=10
        )
    except Exception:
        pass   # Non critique


def uninstall():
    """Removes all shortcuts and autostart."""
    targets = [
        config.AUTOSTART_DIR / "taskmonitor.desktop",
        config.DESKTOP_DIR  / "taskmonitor.desktop",
    ]
    for name in ["Bureau", "Desktop"]:
        targets.append(Path.home() / name / "taskmonitor.desktop")

    for t in targets:
        if t.exists():
            t.unlink()
            log.info(f"Deleted : {t}")


if __name__ == "__main__":
    results = install()
    for k, v in results.items():
        status = "✓" if v else "✗"
        print(f"  {status}  {k}")