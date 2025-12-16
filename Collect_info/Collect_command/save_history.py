import mysql.connector
import os
from datetime import datetime, timedelta

# Configuration de la connexion à la base de données
db_config = {
    "host": "localhost",
    "user": "jennie",        
    "password": "...",      
    "database": "commandes_db"
}

# Connexion à MySQL
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Lire le fichier d'historique
history_file = os.path.expanduser("~/.bash_history")

with open(history_file, "r") as file:
    lines = file.readlines()

# Variables pour stocker les données extraites
commandes = []
current_timestamp = None

# Obtenir la date actuelle au format "YYYY-MM-DD"
date_aujourdhui = datetime.now().strftime("%Y-%m-%d")

for line in lines:
    line = line.strip()
    if line.startswith("#"):
        try:
            current_timestamp = int(line[1:])  # Convertir le timestamp Unix
        except ValueError:
            current_timestamp = None
    elif current_timestamp is not None:
        # Convertir le timestamp en heure et date
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

# Trier les commandes par timestamp
commandes.sort(key=lambda x: x[0])

# Insérer dans MySQL (sans le timestamp)
sql = """
INSERT INTO historique_commandes (type, Nom, heure_ouverture, heure_fermeture, jour, duree)
VALUES (%s, %s, %s, %s, %s, %s)
"""

if commandes:
    cursor.executemany(sql, [cmd[1:] for cmd in commandes])  # Exclure timestamp (index 0)
    conn.commit()
    print(f"{len(commandes)} commandes d'aujourd'hui insérées dans la base de données.")
else:
    print("Aucune commande enregistrée aujourd'hui.")

# Écrire dans le fichier texte
with open("data_command.txt", "w", encoding="utf-8") as f:
    for cmd in commandes:
        # Format: jour, heure_ouverture, heure_fermeture, type, commande, durée
        ligne = f"{cmd[5]}, {cmd[3]}, {cmd[4]}, {cmd[6]:.3f}, {cmd[1]}, {cmd[2]}\n"
        f.write(ligne)

print("Les données ont aussi été enregistrées dans 'data_command.txt'.")

# Fermer la connexion
cursor.close()
conn.close()
