import os
from datetime import datetime, timedelta
from pathlib import Path
from taskmonitor.core import config, logger

class CommandCollector:
    """
    Collects user commands from ~/.bash_history and saves them to data_command.txt in DATA_FILE_DIR.
    """

    def __init__(self):
        self.history_file = os.path.expanduser("~/.bash_history")
        self.output_file = config.DATA_COMMAND_FILE

        # Créer dossier si absent
        config.COMMAND_LOG_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        commandes = []
        current_timestamp = None
        date_aujourdhui = datetime.now().strftime("%Y-%m-%d")

        # Lecture du fichier historique
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            logger.logger.error(f"Fichier historique introuvable: {self.history_file}")
            return

        for line in lines:
            line = line.strip()

            # Ligne timestamp dans bash_history
            if line.startswith("#"):
                try:
                    current_timestamp = int(line[1:])
                except ValueError:
                    current_timestamp = None

            # Ligne commande
            elif current_timestamp is not None:
                date_du_jour = datetime.fromtimestamp(current_timestamp).strftime("%Y-%m-%d")

                if date_du_jour == date_aujourdhui:
                    start_dt = datetime.fromtimestamp(current_timestamp)
                    end_dt = start_dt + timedelta(seconds=2)
                    heure_ouverture = start_dt.strftime("%H:%M:%S")
                    heure_fermeture = end_dt.strftime("%H:%M:%S")
                    duree_minutes = round((end_dt - start_dt).total_seconds() / 60, 3)

                    commandes.append((
                        current_timestamp,
                        "Commande",
                        line,
                        heure_ouverture,
                        heure_fermeture,
                        date_du_jour,
                        duree_minutes
                    ))

        commandes.sort(key=lambda x: x[0])

        # Écriture du fichier final
        with open(self.output_file, "w", encoding="utf-8") as f:
            for cmd in commandes:
                ligne = f"{cmd[5]}, {cmd[3]}, {cmd[4]}, {cmd[6]:.3f}, {cmd[1]}, {cmd[2]}\n"
                f.write(ligne)

        logger.logger.info(f"{len(commandes)} commandes enregistrées dans {self.output_file}")