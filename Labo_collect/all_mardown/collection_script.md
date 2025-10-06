Pour collecter ces informations, il faudra utiliser plusieurs outils et commandes sous Linux, combinés dans un script Python qui met à jour une base de données SQLite. Voici les étapes détaillées et le script final :  

---

### 1️⃣ Récupération des fichiers ouverts  
Utilisation de **`lsof`** pour lister les fichiers ouverts depuis 00:00 :  
```bash
lsof -a -u $(whoami) -d 0-65535 -t
```
- `-a` : Combine les conditions.  
- `-u $(whoami)` : Filtre par utilisateur.  
- `-d 0-65535` : Capture les fichiers normaux.  
- `-t` : Renvoie uniquement les PID.  

Puis, utiliser `ps` pour obtenir plus de détails sur ces fichiers.  

---

### 2️⃣ Récupération des commandes exécutées  
Utilisation de **`history`** (ou `bash_history`) pour les commandes exécutées depuis 00:00 :  
```bash
export HISTTIMEFORMAT="%F %T "
history | awk '$2 >= "00:00:00"'  
```
- `HISTTIMEFORMAT` : Ajoute un timestamp aux commandes.  
- `awk '$2 >= "00:00:00"'` : Filtre celles exécutées depuis minuit.  

---

### 3️⃣ Récupération des programmes en cours d'exécution  
Utilisation de **`ps`** pour lister les programmes exécutés depuis 00:00 :  
```bash
ps -eo pid,cmd,lstart | awk '$4 >= "00:00:00"'
```
- `-eo pid,cmd,lstart` : Affiche le PID, la commande et l'heure de lancement.  
- `awk '$4 >= "00:00:00"'` : Filtre par heure.  

---

### 4️⃣ Récupération des applications et logiciels  
Utilisation de **`wmctrl`** pour les applications avec une fenêtre ouverte :  
```bash
wmctrl -l -p
```
- `-l` : Liste les fenêtres.  
- `-p` : Affiche les PID associés.  
Puis, `ps` permet d'obtenir l'heure de démarrage.  

---

### 5️⃣ Récupération des sites web ouverts  
Utilisation de **`sqlite3`** pour interroger l’historique du navigateur :  
#### Firefox  
```bash
sqlite3 ~/.mozilla/firefox/*.default-release/places.sqlite "SELECT url, datetime(last_visit_date/1000000, 'unixepoch') FROM moz_places WHERE last_visit_date >= strftime('%s','now','start of day')*1000000;"
```
#### Google Chrome  
```bash
sqlite3 ~/.config/google-chrome/Default/History "SELECT url, datetime(last_visit_time/1000000-11644473600, 'unixepoch') FROM urls WHERE last_visit_time >= strftime('%s','now','start of day')*1000000+11644473600000000;"
```
---

## 🔥 Défi : Récupérer les heures de fermeture  
### 1️⃣ Fermeture des fichiers  
Utilisation de `inotifywait` pour détecter les fermetures :  
```bash
inotifywait -m /home/user -e CLOSE_WRITE,CLOSE_NOWRITE --format '%w %e %T' --timefmt '%F %T'
```
Cela surveille `/home/user` et affiche les fermetures.  

### 2️⃣ Fermeture des commandes  
Utilisation de `ps` et `wait` :  
- `ps -eo pid,etime,cmd` : Liste les processus et leur temps d’exécution.  
- `wait <PID>` : Attend qu’un processus se termine.  

### 3️⃣ Fermeture des programmes et applications  
Utilisation de `ps` et `grep` :  
```bash
while ps -p <PID> > /dev/null; do sleep 1; done; date "+%F %T"
```
Cela surveille un PID et affiche l’heure de fermeture.  

### 4️⃣ Fermeture des sites web  
Pas d’outil direct, mais on peut détecter la disparition d’une URL dans `wmctrl`.  

---

## 📝 Script final (`collection.py`)  
```python
import sqlite3
import os
import subprocess
from datetime import datetime

DB_PATH = "activities.sqlite"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activites (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Type TEXT,
            Nom TEXT,
            Heure_Ouverture TEXT,
            Heure_Fermeture TEXT,
            Jour TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_opened_files():
    result = subprocess.run("lsof -u $(whoami) -d 0-65535", shell=True, capture_output=True, text=True)
    files = []
    for line in result.stdout.split("\n")[1:]:
        parts = line.split()
        if len(parts) > 8:
            files.append((parts[8], parts[3]))  # Nom du fichier, heure d'ouverture
    return files

def get_executed_commands():
    result = subprocess.run("history", shell=True, capture_output=True, text=True)
    commands = []
    for line in result.stdout.split("\n"):
        parts = line.split()
        if len(parts) > 2:
            time_str = " ".join(parts[:2])
            cmd = " ".join(parts[2:])
            try:
                commands.append((cmd, time_str))
            except ValueError:
                continue
    return commands

def get_running_programs():
    result = subprocess.run("ps -eo pid,cmd,lstart", shell=True, capture_output=True, text=True)
    programs = []
    for line in result.stdout.split("\n")[1:]:
        parts = line.split()
        if len(parts) > 4:
            programs.append((" ".join(parts[1:-4]), " ".join(parts[-4:])))
    return programs

def get_web_history():
    query = '''SELECT url, datetime(last_visit_date/1000000, 'unixepoch') FROM moz_places 
               WHERE last_visit_date >= strftime('%s','now','start of day')*1000000;'''
    result = subprocess.run(f"sqlite3 ~/.mozilla/firefox/*.default-release/places.sqlite \"{query}\"",
                            shell=True, capture_output=True, text=True)
    sites = []
    for line in result.stdout.split("\n"):
        parts = line.split("|")
        if len(parts) == 2:
            sites.append((parts[0], parts[1]))
    return sites

def insert_data(data, type_act):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.now().strftime("%A")  # Nom du jour
    for nom, heure in data:
        cursor.execute("INSERT INTO activites (Type, Nom, Heure_Ouverture, Jour) VALUES (?, ?, ?, ?)", 
                       (type_act, nom, heure, today))
    conn.commit()
    conn.close()

def main():
    init_db()
    insert_data(get_opened_files(), "Fichier")
    insert_data(get_executed_commands(), "Commande")
    insert_data(get_running_programs(), "Programme")
    insert_data(get_web_history(), "Site")

if __name__ == "__main__":
    main()
```

---

## 🔁 Automatisation  
Ajout d’une tâche **cron** pour exécuter le script chaque jour :  
```bash
crontab -e
```
Ajoutez la ligne :  
```bash
0 0 * * * python3 /chemin/vers/collection.py
```
---

### ✅ Résumé  
✔ Stocke les activités dans **SQLite**  
✔ Organise par jour  
✔ Met à jour chaque lundi à 00:00  
✔ Récupère les fichiers, commandes, programmes, applications et sites ouverts  
✔ Surveille la fermeture avec `inotifywait`, `ps`, `wmctrl`  

C’est une base robuste. Il reste à tester et ajuster selon les besoins ! 🚀