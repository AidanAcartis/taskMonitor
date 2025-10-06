Voici un script Python qui va lire `~/.bash_history`, extraire les commandes avec leurs timestamps, et les insérer dans une base de données MySQL.  

---

### **1. Création de la table MySQL**
Avant d'exécuter le script, crée la table dans ta base de données `commandes_db` :  
```sql
CREATE TABLE IF NOT EXISTS historique_commandes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(50),
    Nom TEXT,
    heure_ouverture TIME,
    heure_fermeture TIME,
    date DATE
);
```
---

### **2. Script Python pour stocker les commandes**
Crée un fichier `save_history.py` et colle ce code :  
```python
import mysql.connector
import os
import time
from datetime import datetime

# Configuration de la connexion à la base de données
db_config = {
    "host": "localhost",
    "user": "jennie",  # Remplace par ton utilisateur MySQL
    "password": "nerd",  # Remplace par ton mot de passe MySQL
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

for line in lines:
    line = line.strip()
    if line.startswith("#"):
        try:
            current_timestamp = int(line[1:])  # Convertir le timestamp Unix
        except ValueError:
            current_timestamp = None
    elif current_timestamp is not None:
        # Convertir le timestamp en heure et date
        heure_ouverture = datetime.fromtimestamp(current_timestamp).strftime("%H:%M:%S")
        date_du_jour = datetime.fromtimestamp(current_timestamp).strftime("%Y-%m-%d")

        # Simuler une heure de fermeture (approximative)
        heure_fermeture = (datetime.fromtimestamp(current_timestamp) + 
                           timedelta(seconds=2)).strftime("%H:%M:%S")

        # Ajouter la commande à la liste
        commandes.append(("Commande", line, heure_ouverture, heure_fermeture, date_du_jour))

# Insérer les données dans la base de données
sql = """
INSERT INTO historique_commandes (type, Nom, heure_ouverture, heure_fermeture, date)
VALUES (%s, %s, %s, %s, %s)
"""

cursor.executemany(sql, commandes)
conn.commit()

print(f"{len(commandes)} commandes insérées dans la base de données.")

# Fermer la connexion
cursor.close()
conn.close()
```
---

### **3. Exécution du script**
Sauvegarde le script et exécute-le avec :  
```bash
python3 save_history.py
```
Cela va lire les commandes depuis `~/.bash_history`, les extraire avec leurs timestamps et les enregistrer dans `commandes_db`.  

**Remarque :**  
- L'heure de fermeture est estimée en ajoutant `2 secondes` après l'ouverture (car `bash_history` ne stocke pas les durées).  
- Pour automatiser, ajoute ce script à un `cron job` ou exécute-le périodiquement.  

**Dis-moi si tu veux des modifications ou des améliorations !** 😊