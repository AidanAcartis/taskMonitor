Je vais te détailler comment structurer et collecter ces données dans SQLite en Python, en récupérant les heures d’ouverture et de fermeture des fichiers, sites web, programmes et applications.  

---

## 📌 **1. Structure de la base SQLite**
On va créer une table `activites` avec les colonnes suivantes :
```sql
CREATE TABLE activites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    nom TEXT NOT NULL,
    heure_ouverture TEXT NOT NULL,
    heure_fermeture TEXT
);
```
- `id` : Clé primaire unique
- `type` : Type d'activité (Commande, Fichier, Programme, Site, etc.)
- `nom` : Nom de l’activité (chemin du fichier, nom du programme, URL du site)
- `heure_ouverture` : Date et heure d’ouverture
- `heure_fermeture` : Date et heure de fermeture (NULL si pas encore fermé)

---

## 📌 **2. Comment récupérer les activités depuis minuit (00:00) jusqu'à l'heure de lancement du script ?**

### 🔹 **Fichiers ouverts**
**Méthode :** Utiliser `lsof` (Linux) ou `psutil` (Python)  
```python
import os
import sqlite3
from datetime import datetime

def get_open_files():
    result = os.popen("lsof -Fn").read().split("\n")
    open_files = []
    for line in result:
        if line.startswith("n"):
            open_files.append(line[1:])  # Récupère le nom du fichier
    return open_files

def store_open_files():
    conn = sqlite3.connect("activites.db")
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for file in get_open_files():
        cursor.execute("INSERT INTO activites (type, nom, heure_ouverture) VALUES (?, ?, ?)", ("Fichier", file, now))
    
    conn.commit()
    conn.close()

store_open_files()
```

---

### 🔹 **Commandes exécutées**
**Méthode :** Récupérer l'historique avec `history` (Linux)  
```python
import os

def get_command_history():
    result = os.popen("history").read()
    return result.split("\n")

for line in get_command_history():
    print(line)  # À insérer dans la BDD avec l'heure courante
```
*(Il faut ajouter une logique pour récupérer l’heure d’exécution.)*

---

### 🔹 **Programmes en cours d'exécution**
**Méthode :** `psutil.process_iter()`  
```python
import psutil

def get_running_programs():
    return [(p.pid, p.name()) for p in psutil.process_iter(['pid', 'name'])]

for pid, name in get_running_programs():
    print(f"Programme en cours : {name} (PID: {pid})")
```
*(Lancer ce script périodiquement pour suivre les ouvertures et fermetures.)*

---

### 🔹 **Sites web ouverts**
**Méthode :** Récupérer le titre de la fenêtre active  
```python
import pygetwindow as gw
import time

visited_sites = {}

while True:
    active_window = gw.getActiveWindow()
    
    if active_window and ("Firefox" in active_window.title or "Chrome" in active_window.title):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if active_window.title not in visited_sites:
            visited_sites[active_window.title] = {'open_time': now, 'close_time': None}
        
        visited_sites[active_window.title]['close_time'] = now
    
    time.sleep(5)
```

---

## 📌 **3. Comment récupérer l’heure de fermeture ?**

### 🔹 **Fichiers fermés**
Impossible directement, mais on peut surveiller si un fichier disparaît de `lsof`.

### 🔹 **Programmes fermés**
**Méthode :** Vérifier périodiquement si le PID n'existe plus  
```python
programs = {}

while True:
    current_programs = {p.pid: p.name() for p in psutil.process_iter(['pid', 'name'])}
    
    for pid, name in list(programs.items()):
        if pid not in current_programs:  # Si un programme a disparu
            close_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{name} fermé à {close_time}")
            del programs[pid]
    
    for pid, name in current_programs.items():
        if pid not in programs:
            open_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            programs[pid] = name
    
    time.sleep(5)
```

---

## 📌 **4. Mise à jour hebdomadaire**
On va exécuter un script tous les lundis à 00:00 pour nettoyer les anciennes données :
```python
import sqlite3
from datetime import datetime, timedelta

def clean_old_data():
    conn = sqlite3.connect("activites.db")
    cursor = conn.cursor()
    
    last_monday = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d 00:00:00")
    cursor.execute("DELETE FROM activites WHERE heure_ouverture < ?", (last_monday,))
    
    conn.commit()
    conn.close()

clean_old_data()
```
👉 On peut automatiser cela avec `cron` :
```bash
0 0 * * 1 python3 /chemin/vers/script.py
```

---

## 📌 **5. Résumé**
| Type | Détection Ouverture | Détection Fermeture |
|------|---------------------|---------------------|
| **Commande** | `history` | Instantané |
| **Fichier** | `lsof` | Comparaison avec un ancien état |
| **Programme** | `psutil.process_iter()` | Vérifier disparition du PID |
| **Site Web** | `pygetwindow.getActiveWindow()` | Vérifier changement de fenêtre |

Tout est structuré et automatisé ! 🎯 Tu peux maintenant récupérer et analyser les activités avec SQLite.