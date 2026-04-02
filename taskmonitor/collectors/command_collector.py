"""
collectors/command_collector.py
================================
Collecte les commandes bash du jour depuis ~/.bash_history.
Refactorisation de Collect_Data_command_Script.py.
"""

from datetime import datetime, timedelta
from taskmonitor.core import config, storage
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


def collect_commands(date_str: str) -> list[str]:
    """
    Lit .bash_history et extrait les commandes exécutées à la date donnée.

    Args:
        date_str: date au format "YYYY-MM-DD"

    Returns:
        Lignes au format data_command.txt prêtes à être stockées
    """
    history_file = config.BASH_HISTORY_FILE
    if not history_file.exists():
        log.warning(f"Fichier bash_history introuvable : {history_file}")
        return []

    commandes = []
    current_timestamp: int | None = None

    with history_file.open(encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        if line.startswith("#"):
            try:
                current_timestamp = int(line[1:])
            except ValueError:
                current_timestamp = None

        elif current_timestamp is not None:
            date_cmd = datetime.fromtimestamp(current_timestamp).strftime("%Y-%m-%d")

            if date_cmd == date_str:
                start_dt = datetime.fromtimestamp(current_timestamp)
                end_dt   = start_dt + timedelta(seconds=2)

                heure_ouverture = start_dt.strftime("%H:%M:%S")
                heure_fermeture = end_dt.strftime("%H:%M:%S")
                duree_minutes   = round((end_dt - start_dt).total_seconds() / 60, 3)

                commandes.append((
                    current_timestamp,
                    date_cmd,
                    heure_ouverture,
                    heure_fermeture,
                    duree_minutes,
                    line,           # la commande elle-même
                ))

    # Tri chronologique
    commandes.sort(key=lambda x: x[0])

    result_lines = [
        f"{cmd[1]}, {cmd[2]}, {cmd[3]}, {cmd[4]:.3f}, Commande, {cmd[5]}"
        for cmd in commandes
    ]

    storage.write_data_command(date_str, result_lines)
    log.info(f"data_command.txt : {len(result_lines)} commandes pour {date_str}")
    return result_lines