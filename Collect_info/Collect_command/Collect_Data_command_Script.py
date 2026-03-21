import os
from datetime import datetime, timedelta

history_file = os.path.expanduser("~/.bash_history")

with open(history_file, "r") as file:
    lines = file.readlines()

commandes = []
current_timestamp = None

date_aujourdhui = datetime.now().strftime("%Y-%m-%d")

for line in lines:
    line = line.strip()

    if line.startswith("#"):
        try:
            current_timestamp = int(line[1:])
        except ValueError:
            current_timestamp = None

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

with open("data_command.txt", "w", encoding="utf-8") as f:
    for cmd in commandes:
        ligne = f"{cmd[5]}, {cmd[3]}, {cmd[4]}, {cmd[6]:.3f}, {cmd[1]}, {cmd[2]}\n"
        f.write(ligne)

print(f"{len(commandes)} commandes enregistrées dans data_command.txt")