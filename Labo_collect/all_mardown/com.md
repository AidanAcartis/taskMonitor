Voici un script Python qui exécute ton script Bash (`script.sh`), récupère les commandes exécutées aujourd'hui et les insère dans une base de données MySQL.  

### 1️⃣ **Configuration de la base de données**  
Tu dois d'abord créer une table `historique_commandes` avec les colonnes nécessaires. Connecte-toi à MySQL et exécute :  

```sql
CREATE DATABASE IF NOT EXISTS commandes_db;
USE commandes_db;

CREATE TABLE IF NOT EXISTS historique_commandes (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    Nom TEXT NOT NULL,
    heure_ouverture DATETIME NOT NULL,
    heure_fermeture DATETIME NOT NULL,
    jour DATE NOT NULL
);
```

---

### 2️⃣ **Script Python (`log_commands.py`)**
Ce script exécute `script.sh`, extrait les commandes du jour et les enregistre dans la base de données.

```python
import subprocess
import mysql.connector
import re
from datetime import datetime

# Configuration de la connexion à la base de données
db_config = {
    "host": "localhost",
    "user": "nouvel_utilisateur",  # Remplace par ton utilisateur MySQL
    "password": "ton_mot_de_passe",  # Remplace par ton mot de passe MySQL
    "database": "commandes_db"
}

# Exécuter le script Bash et récupérer la sortie
try:
    result = subprocess.run(["bash", "script.sh"], capture_output=True, text=True, check=True)
    lines = result.stdout.strip().split("\n")
except subprocess.CalledProcessError as e:
    print("Erreur lors de l'exécution du script :", e)
    exit()

# Expression régulière pour extraire la date et la commande
pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\S.*)")

# Connexion à la base de données
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    for line in lines:
        match = pattern.match(line)
        if match:
            heure_ouverture = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
            commande = match.group(2)
            jour = heure_ouverture.date()

            # Estimation de l'heure de fermeture (on prend l'heure d'ouverture de la prochaine commande)
            heure_fermeture = heure_ouverture  # Par défaut, si pas de commande suivante

            # Insérer dans la base de données
            cursor.execute("""
                INSERT INTO historique_commandes (type, Nom, heure_ouverture, heure_fermeture, jour)
                VALUES (%s, %s, %s, %s, %s)
            """, ("Commande", commande, heure_ouverture, heure_fermeture, jour))

    conn.commit()
    print("Commandes enregistrées avec succès !")

except mysql.connector.Error as err:
    print("Erreur MySQL :", err)

finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
```

---

### 3️⃣ **Exécution du script**
Lance ce script avec :

```bash
python3 log_commands.py
```

---

### 📌 **Explication du fonctionnement**
- Le script **exécute `script.sh`** et récupère la sortie.
- Il **utilise une expression régulière** pour extraire la date et la commande.
- Il **stocke ces informations dans la base de données** avec `type='Commande'`.
- `heure_ouverture` correspond à l'heure de lancement de la commande.
- `heure_fermeture` est laissée identique (mais peut être ajustée si nécessaire).

Tu peux modifier `heure_fermeture` en l'ajustant à l'heure d'ouverture de la prochaine commande si besoin.