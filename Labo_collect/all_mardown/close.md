Je vais détailler comment récupérer toutes ces informations et les stocker dans une base de données SQLite avec les colonnes **(ID, Type, Nom, Heure d’ouverture, Heure de fermeture)**.

---

# 🔹 **1. Création de la base de données SQLite**
Avant de collecter les informations, on va préparer une base de données pour stocker les activités.

### **📝 Création de la table `activites`**
```python
import sqlite3

conn = sqlite3.connect("activites.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS activites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    nom TEXT,
    heure_ouverture TEXT,
    heure_fermeture TEXT
)
""")

conn.commit()
conn.close()
```
✔ **Organisé et structuré**  
✔ **Permet des requêtes SQL avancées**  

---

# 🔹 **2. Récupérer les fichiers ouverts depuis 00:00**
### **📂 Méthode : Utiliser `inotifywait` (Linux)**
Sur Linux, `inotifywait` permet de surveiller les fichiers ouverts :
```bash
inotifywait -m -e open --format '%w%f %T' --timefmt '%Y-%m-%d %H:%M:%S' /home/user/ 2>/dev/null
```
Ce script liste les fichiers ouverts **en temps réel**.

### **📌 Automatisation avec Python**
On peut capturer ces événements et les insérer dans SQLite.
```python
import subprocess

def collect_opened_files():
    cmd = "inotifywait -m -e open --format '%w%f %T' --timefmt '%Y-%m-%d %H:%M:%S' /home/user/"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    
    conn = sqlite3.connect("activites.db")
    cursor = conn.cursor()

    for line in process.stdout:
        file_path, timestamp = line.strip().rsplit(" ", 1)
        cursor.execute("INSERT INTO activites (type, nom, heure_ouverture) VALUES (?, ?, ?)", 
                       ("Fichier", file_path, timestamp))
        conn.commit()

    conn.close()

collect_opened_files()
```
✔ **Avantage** : Capture en temps réel tous les fichiers ouverts.  
❌ **Limite** : Ne fonctionne pas pour les fichiers déjà ouverts avant le lancement du script.

---

# 🔹 **3. Récupérer les commandes exécutées depuis 00:00**
### **🖥️ Méthode : Lire le fichier `~/.bash_history`**
Les commandes sont enregistrées dans `~/.bash_history`, mais sans horodatage par défaut.

### **📌 Activer l’horodatage dans `~/.bashrc`**
Ajoute ceci à `~/.bashrc` :
```bash
export HISTTIMEFORMAT='%Y-%m-%d %H:%M:%S '
```
Recharge le fichier :
```bash
source ~/.bashrc
```

### **📌 Script Python pour récupérer les commandes**
```python
import os

def collect_commands():
    conn = sqlite3.connect("activites.db")
    cursor = conn.cursor()

    with open(os.path.expanduser("~/.bash_history"), "r") as f:
        for line in f:
            if line.strip():
                timestamp, command = line[:19], line[20:].strip()  # Séparer l’heure et la commande
                cursor.execute("INSERT INTO activites (type, nom, heure_ouverture) VALUES (?, ?, ?)", 
                               ("Commande", command, timestamp))

    conn.commit()
    conn.close()

collect_commands()
```
✔ **Avantage** : Facile à récupérer, fonctionne sur tous les systèmes Linux.  
❌ **Limite** : L’heure exacte dépend de l’activation d’`HISTTIMEFORMAT`.

---

# 🔹 **4. Récupérer les programmes lancés depuis 00:00**
### **📌 Utiliser `psutil` pour voir les processus**
```python
import psutil
from datetime import datetime

def collect_running_programs():
    conn = sqlite3.connect("activites.db")
    cursor = conn.cursor()

    for proc in psutil.process_iter(['pid', 'name', 'create_time']):
        try:
            name = proc.info['name']
            start_time = datetime.fromtimestamp(proc.info['create_time']).strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("INSERT INTO activites (type, nom, heure_ouverture) VALUES (?, ?, ?)", 
                           ("Programme", name, start_time))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    conn.commit()
    conn.close()

collect_running_programs()
```
✔ **Avantage** : Récupère tous les programmes démarrés depuis le dernier démarrage.  
❌ **Limite** : Impossible de récupérer l’heure d’un programme qui s’est terminé avant l’exécution du script.

---

# 🔹 **5. Récupérer les logiciels/applications lancés**
### **📌 Sur Linux (GNOME)**
```bash
journalctl --since "00:00" | grep gnome-session
```
Ou avec Python :
```python
import subprocess

def collect_launched_apps():
    cmd = "journalctl --since '00:00' | grep gnome-session"
    output = subprocess.check_output(cmd, shell=True, text=True)

    conn = sqlite3.connect("activites.db")
    cursor = conn.cursor()

    for line in output.split("\n"):
        if line.strip():
            time_str = line.split()[0] + " " + line.split()[1]  # Extraire la date et l’heure
            app_name = " ".join(line.split()[2:])  # Nom de l’application

            cursor.execute("INSERT INTO activites (type, nom, heure_ouverture) VALUES (?, ?, ?)", 
                           ("Application", app_name, time_str))

    conn.commit()
    conn.close()

collect_launched_apps()
```
✔ **Avantage** : Facile à récupérer avec `journalctl`.  
❌ **Limite** : Dépend de l’environnement de bureau.

---

# 🔹 **6. Récupérer les sites ouverts et leur fermeture**
On utilise **pygetwindow** pour détecter les fenêtres actives.

```python
import time
import sqlite3
import psutil
from datetime import datetime
import pygetwindow as gw

visited_sites = {}

def get_active_window():
    try:
        return gw.getActiveWindow().title
    except:
        return None

conn = sqlite3.connect("activites.db")
cursor = conn.cursor()

while True:
    active_window = get_active_window()
    
    if active_window and ("Firefox" in active_window or "Chrome" in active_window):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if active_window not in visited_sites:
            visited_sites[active_window] = {'open_time': now, 'close_time': None}
        
        visited_sites[active_window]['close_time'] = now
    
    time.sleep(5)
    
    # Sauvegarde dans la base de données
    for site, times in visited_sites.items():
        cursor.execute("INSERT INTO activites (type, nom, heure_ouverture, heure_fermeture) VALUES (?, ?, ?, ?)", 
                       ("Site", site, times['open_time'], times['close_time']))
        conn.commit()

conn.close()
```
✔ **Avantage** : Récupère l’heure d’ouverture et de fermeture.  
❌ **Limite** : Ne fonctionne que pour les fenêtres visibles.

---

# 🔹 **Résumé**
| Activité | Méthode |
|----------|---------|
| **Fichiers ouverts** | `inotifywait` |
| **Commandes exécutées** | `~/.bash_history` |
| **Programmes lancés** | `psutil` |
| **Applications démarrées** | `journalctl` |
| **Sites visités** | `pygetwindow` |

---

## **Tu veux un script complet qui gère tout automatiquement ?**
Je peux regrouper tout cela dans un seul script Python si besoin ! 😃