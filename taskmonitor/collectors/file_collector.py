"""
collectors/file_collector.py
============================
Extrait les événements d'ouverture/fermeture de fenêtres
depuis window_changes.log et calcule les durées.

Fusionne les scripts :
  - extract_window_host_events.sh
  - get_collect_file.py
  - duration_file.py
"""

import re
import socket
from datetime import datetime
from collections import defaultdict
from pathlib import Path

from taskmonitor.core import config, storage
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)

HOSTNAME = socket.gethostname()


# ─────────────────────────────────────────────
# EXTRACTION OPENED / CLOSED
# ─────────────────────────────────────────────

def extract_opened_closed(date_str: str) -> tuple[list[str], list[str]]:
    """
    Lit window_changes.log et extrait les listes d'ouvertures/fermetures.

    Returns:
        (opened_lines, closed_lines) — chaque ligne = "YYYY-MM-DD HH:MM:SS titre"
    """
    raw = storage.read_window_log(date_str)
    if not raw:
        # Essayer le log actif si pas d'archive
        raw = storage.read_window_log(None)
    if not raw:
        log.warning(f"Aucun log disponible pour {date_str}")
        return [], []

    lines = raw.splitlines()
    opened: list[str] = []
    closed: list[str] = []
    current_type: str | None = None
    current_ts:   str | None = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith("---"):
            continue

        # Ligne de timestamp + type d'événement
        ts_match = re.match(
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (Nouvelles fenêtres ajoutées|Fenêtres fermées)",
            line
        )
        if ts_match:
            current_ts   = ts_match.group(1)
            event_label  = ts_match.group(2)
            current_type = "opened" if "ajoutées" in event_label else "closed"
            continue

        # Ligne de fenêtre (contient le hostname)
        if current_type and current_ts and HOSTNAME in line:
            title = _extract_title(line)
            if title:
                entry = f"{current_ts} {title}"
                if current_type == "opened":
                    opened.append(entry)
                else:
                    closed.append(entry)

    storage.write_opened_closed(date_str, opened, closed)
    log.info(f"Extrait {len(opened)} ouvertures, {len(closed)} fermetures")
    return opened, closed


def _extract_title(line: str) -> str:
    """Extrait le titre de fenêtre depuis une ligne wmctrl."""
    parts = line.split(None, 3)
    if len(parts) >= 4:
        # parts[3] est "hostname titre" → extraire après le hostname
        rest = parts[3]
        if HOSTNAME in rest:
            title = rest[rest.index(HOSTNAME) + len(HOSTNAME):].strip()
            return title
    return ""


# ─────────────────────────────────────────────
# COLLECTE ET DURÉES
# ─────────────────────────────────────────────

def _parse_entry(line: str) -> tuple[str, str, str] | None:
    """Parse une ligne "YYYY-MM-DD HH:MM:SS titre" → (date, time, titre)."""
    parts = line.strip().split(" ", 2)
    if len(parts) < 3:
        return None
    return parts[0], parts[1], parts[2]


def collect_file_data(date_str: str) -> list[str]:
    """
    À partir des fichiers Opened/Closed, calcule les durées d'utilisation
    et retourne les lignes de data_file.txt.

    Format de sortie:
        YYYY-MM-DD HH:MM:SS HH:MM:SS duration_min type   titre

    Returns:
        Lignes prêtes à écrire dans data_file.txt
    """
    files = config.get_processed_files(date_str)

    opened_path = files["opened"]
    closed_path = files["closed"]

    if not opened_path.exists() or not closed_path.exists():
        log.warning(f"Fichiers Opened/Closed manquants pour {date_str}")
        return []

    opened_lines = opened_path.read_text(encoding="utf-8").splitlines()
    closed_lines = closed_path.read_text(encoding="utf-8").splitlines()

    # Étape 1 : apparier ouvertures et fermetures (get_collect_file logic)
    collected = _pair_open_close(opened_lines, closed_lines)

    # Étape 2 : calculer les durées (duration_file logic)
    result_lines = _compute_durations(collected)

    storage.write_data_file(date_str, result_lines)
    log.info(f"data_file.txt : {len(result_lines)} entrées")
    return result_lines


def _pair_open_close(opened: list[str], closed: list[str]) -> list[str]:
    """
    Apparie chaque ouverture avec sa fermeture correspondante.
    Retourne des lignes "date open_time close_time titre".
    """
    used_close = set()
    paired = []

    for i, open_line in enumerate(opened):
        parsed_open = _parse_entry(open_line)
        if not parsed_open:
            continue
        open_date, open_time, filename = parsed_open
        filename = _normalize_title(filename)

        for j, close_line in enumerate(closed):
            if j in used_close:
                continue
            parsed_close = _parse_entry(close_line)
            if not parsed_close:
                continue
            _, close_time, close_filename = parsed_close
            close_filename = _normalize_title(close_filename)

            if close_filename == filename:
                used_close.add(j)
                paired.append(f"{open_date} {open_time} {close_time} {filename}")
                break

    return paired


def _normalize_title(title: str) -> str:
    """Supprime le préfixe '● ' (fichier modifié non sauvegardé)."""
    return title.lstrip("● ").strip()


def _compute_durations(paired: list[str]) -> list[str]:
    """
    Pour les titres répétés, cumule les durées et garde la dernière occurrence.
    Retourne les lignes data_file.txt format.
    """
    durations: dict[str, float] = defaultdict(float)
    last_info: dict[str, tuple[str, str, str]] = {}

    for line in paired:
        cols = line.split()
        if len(cols) < 4:
            continue
        date_s = cols[0]
        start_s = cols[1]
        end_s   = cols[2]
        title   = " ".join(cols[3:])

        try:
            start_dt = datetime.strptime(start_s, "%H:%M:%S")
            end_dt   = datetime.strptime(end_s,   "%H:%M:%S")
            duration_min = (end_dt - start_dt).total_seconds() / 60
        except ValueError:
            continue

        durations[title] += duration_min
        last_info[title] = (date_s, start_s, end_s)

    result = []
    for title, total_min in sorted(durations.items(), key=lambda x: x[1], reverse=True):
        date_s, start_s, end_s = last_info[title]
        entry_type = "file-directory-App" if " - " in title else "directory/App"
        result.append(f"{date_s} {start_s} {end_s} {total_min:.2f} {entry_type}   {title}")

    return result