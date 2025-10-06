import subprocess
import mysql.connector
from datetime import datetime

# Configuration de la connexion à la base de données
db_config = {
    "host": "localhost",
    "user": "jennie",  # Remplace par ton utilisateur MySQL
    "password": "nerd",  # Remplace par ton mot de passe MySQL
    "database": "commandes_db"
}

# Exécuter le script Bash et récupérer la sortie
try:
    result = subprocess.run(["bash", "script.sh"], capture_output=True, text=True, check=True)
    lines = result.stdout.strip().split("\n")
except subprocess.CalledProcessError as e:
    print("Erreur lors de l'exécution du script :", e)
    exit()

# Connexion à la base de données
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    for line in lines:
        # Séparer chaque ligne en valeurs basées sur les espaces
        values = line.split()

        if len(values) >= 5:  # Assurer qu'il y a suffisamment de valeurs dans la ligne
            # Extraire les valeurs nécessaires
            jour = datetime.strptime(values[0], "%Y-%m-%d").date()  # 1ère valeur : Date
            heure_ouverture = datetime.strptime(values[3], "%H:%M:%S").time()  # 4ème valeur : Heure d'ouverture
            heure_fermeture = datetime.strptime(values[1], "%H:%M:%S").time()  # 2ème valeur : Heure de fermeture
            commande = values[4]  # 5ème valeur : Commande
            
            # Joindre toutes les valeurs après la 5ème dans une seule chaîne pour 'Nom'
            nom = ' '.join(values[4:])

            # Insérer dans la base de données
            cursor.execute("""
                INSERT INTO historique_commandes (type, Nom, heure_ouverture, heure_fermeture, jour)
                VALUES (%s, %s, %s, %s, %s)
            """, ("Commande", nom, heure_ouverture, heure_fermeture, jour))

    conn.commit()
    print("Commandes enregistrées avec succès !")

except mysql.connector.Error as err:
    print("Erreur MySQL :", err)

finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
