"""
processing/assembler.py
=======================
Assemble data_file.txt et data_command.txt en un seul fichier TSV data_collect.txt.
Refactorisation de collect_data.py.
"""

from taskmonitor.core import config, storage
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


def assemble(date_str: str) -> list[str]:
    """
    Fusionne les données fichiers et commandes en un TSV unifié.

    Format de sortie (TSV):
        date  start  end  duration  type  name

    Args:
        date_str: date au format "YYYY-MM-DD"

    Returns:
        Lignes TSV de data_collect.txt
    """
    lines: list[str] = []

    # ── Fichiers (data_file.txt) ──────────────────────
    file_lines = storage.read_data_file(date_str)
    for line in file_lines:
        parts = line.strip().split()
        if len(parts) >= 6:
            date      = parts[0]
            time_open = parts[1]
            time_close= parts[2]
            duration  = parts[3]
            type_     = parts[4]
            name      = " ".join(parts[5:])
            lines.append(f"{date}\t{time_open}\t{time_close}\t{duration}\t{type_}\t{name}")

    # ── Commandes (data_command.txt) ─────────────────
    cmd_lines = storage.read_data_command(date_str)
    for line in cmd_lines:
        parts = [x.strip() for x in line.strip().split(",")]
        if len(parts) >= 6:
            date      = parts[0]
            time_open = parts[1]
            time_close= parts[2]
            duration  = parts[3]
            type_     = parts[4]
            name      = ", ".join(parts[5:])
            lines.append(f"{date}\t{time_open}\t{time_close}\t{duration}\t{type_}\t{name}")

    storage.write_data_collect(date_str, lines)
    log.info(f"data_collect.txt : {len(lines)} lignes pour {date_str}")
    return lines