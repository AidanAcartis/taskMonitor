Il s'agit d'un projet de task monitoring sur un ordinateur:
- Le programme surveille tous les activites sur la fenetre de l'utilisateur et l'enregistre dans un fichier logs.
- Les logs sont de nouveau traite par le programme: analyse de fichier ouvert, commande lance, app utilise, site ou page web ouvert.
- Les actions bien definis sont stockes en .csv avec les dates et les durees d'utilisation
- Une des fonctionnalites du logiciel est de representer graphiquement et statistiquement les activites de l'utilisateur globalement et en details.
- Alors les donnees enregistres dans le fichier .csv, les actions seront rassembler en cluster qui rassemblent les actions soumis a un seul global intention , oui on leur definit un global task intention

Pour le moment, j'ai fini les scripts qui font chaque taches pour avoir le donnee final a presenter a l'interface, mais mon code n'est pas encore structure tel un vrai projet logiciel. et pas encore d'interface.

Alors je vais presenter ici chaque scripts, emplacements et les fichiers inportant ainsi que les modeles. Apres tu va m'aider a le structurer et construire le vrai logiciel.

- EMPLACEMENT PRINCIPAL:
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls
ALL_LABS  taskMonitor  taskMonitor_LABS  Vis_Models

```
Seul `taskMonitor` et `Vis_Models` importent ici.
- `taskMonitor` contient tous les scripts partages dans des dossiers qui presentent chaque etapes du logiciel pour le collecte et le traitement des donnees finaux.
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor
COLLECT_COMMAND_LOGS  COLLECT_FILE_DATA  ReadDme.md
COLLECT_DATA          PROCESSING         READme.md

```

- `Vis_Models` contient mes models pour analyser les logs(fichiers, directories, sites, app), model pour clustering, model pour generer les global tasks intention
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls Vis_Models/
augmented-peft-global_task-checkpoint-local  final_Model_V3      Gen_Desc_Model
final_model                                  final_Model_V3.zip

```
======== `taskMonitor` ==========
# 1- COLLECT_FILE_DATA:
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/COLLECT_FILE_DATA/
COLLECT_FILE_LOGS  EXTRACT_WINDOWS_LOGS  MONITOR_WINDOW  READme.md

```
## 1-1. MONITOR_WINDOW:
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/COLLECT_FILE_DATA/MONITOR_WINDOW/
corrected_monitor_windows.sh

```
Ce script `corrected_monitor_windows.sh` lance la surveillance des fenetres(windows) sur l'ordinateur de l'user et l'enregister dans un fichier `window_changes.log`.

- `corrected_monitor_windows.sh` :
```bash
#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=/home/aidan/.Xauthority

LOG_FILE="$HOME/window_changes.log"  # Fichier de log pour enregistrer les changements
PREV_WINDOWS_FILE="$HOME/prev_windows.txt"  # Fichier pour stocker l'état précédent des fenêtres

# Si le fichier précédent n'existe pas, créez-le avec l'état actuel des fenêtres
if [ ! -f "$PREV_WINDOWS_FILE" ]; then
    wmctrl -l > "$PREV_WINDOWS_FILE"
fi

echo "Surveillance des fenêtres en cours..."

while true; do
    # Obtenir la date d'aujourd'hui
    CURRENT_DATE=$(date +"%Y-%m-%d")

    # Vérifier la dernière date enregistrée dans le fichier de log
    if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
        LAST_LOG_DATE=$(grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}" "$LOG_FILE" | tail -n 1 | awk '{print $1}')
    else
        LAST_LOG_DATE=""
    fi

    # Si la dernière date enregistrée est différente d'aujourd'hui, on vide le fichier de log
    if [ "$CURRENT_DATE" != "$LAST_LOG_DATE" ]; then
        echo "-----------------------------" > "$LOG_FILE"
        echo "$(date +"%Y-%m-%d %H:%M:%S") - Nouveau jour de surveillance" >> "$LOG_FILE"
    fi

    # Obtenez la liste actuelle des fenêtres
    CURRENT_WINDOWS=$(wmctrl -l)

    # Comparez l'état actuel avec l'état précédent
    NEW_WINDOWS=$(comm -13 <(sort "$PREV_WINDOWS_FILE") <(echo "$CURRENT_WINDOWS" | sort))
    CLOSED_WINDOWS=$(comm -23 <(sort "$PREV_WINDOWS_FILE") <(echo "$CURRENT_WINDOWS" | sort))

    # Si de nouvelles fenêtres ont été ajoutées, enregistrez-les dans le fichier log
    if [ -n "$NEW_WINDOWS" ]; then
        echo "$(date +"%Y-%m-%d %H:%M:%S") - Nouvelles fenêtres ajoutées :" >> "$LOG_FILE"
        echo "$NEW_WINDOWS" >> "$LOG_FILE"
        echo "-----------------------------" >> "$LOG_FILE"
    fi

    # Si des fenêtres ont été fermées, enregistrez-les dans le fichier log
    if [ -n "$CLOSED_WINDOWS" ]; then
        echo "$(date +"%Y-%m-%d %H:%M:%S") - Fenêtres fermées :" >> "$LOG_FILE"
        echo "$CLOSED_WINDOWS" >> "$LOG_FILE"
        echo "-----------------------------" >> "$LOG_FILE"
    fi

    # Mettez à jour le fichier de l'état précédent
    echo "$CURRENT_WINDOWS" > "$PREV_WINDOWS_FILE"

    # Pause de 2 secondes avant la prochaine vérification
    sleep 2
done

```
- `window_changes.log`:
```log
-----------------------------
2026-03-28 00:00:00 - Nouveau jour de surveillance
2026-03-28 00:00:04 - Nouvelles fenêtres ajoutées :
0x02a0001c  0 aidan-Lenovo-N50-70 ChatGPT - Google Chrome
-----------------------------
2026-03-28 00:00:04 - Fenêtres fermées :
0x02a0001c  0 aidan-Lenovo-N50-70 New Tab - Google Chrome
-----------------------------
2026-03-28 00:00:16 - Nouvelles fenêtres ajoutées :
0x02a0001c  0 aidan-Lenovo-N50-70 Erreur fichier non trouvé - Google Chrome
-----------------------------
2026-03-28 00:00:16 - Fenêtres fermées :
0x02a0001c  0 aidan-Lenovo-N50-70 ChatGPT - Google Chrome
-----------------------------
2026-03-28 00:00:56 - Nouvelles fenêtres ajoutées :
0x03400004  0 aidan-Lenovo-N50-70 get_collect_file.py - taskMonitor - Visual Studio Code
-----------------------------
```

- `prev_windows.txt`:
```txt
0x02a0001c  0 aidan-Lenovo-N50-70 Erreur fichier non trouvé - Google Chrome
0x00a00004  0 aidan-Lenovo-N50-70 command_describer_project
0x0280000a  0 aidan-Lenovo-N50-70 aidan@aidan-Lenovo-N50-70: ~/Documents/Projects/Visualization/taskMonitor
0x03400004  0 aidan-Lenovo-N50-70 collect_data.py - taskMonitor - Visual Studio Code
0x0340000b  0 aidan-Lenovo-N50-70 ● EXPORT_MANAGE.py - Visual Studio Code
0x00a0031e  0 aidan-Lenovo-N50-70 Home
0x02805bd9  0 aidan-Lenovo-N50-70 aidan@aidan-Lenovo-N50-70: ~/Documents/Projects/Visualization/taskMonitor/PROCESSING/DESCRIBE_EVENTS
0x02806935  0 aidan-Lenovo-N50-70 aidan@aidan-Lenovo-N50-70: ~/Documents/Projects/Visualization/taskMonitor/PROCESSING/DESCRIBE_EVENTS/command_desc/command_describer_project
0x02600009 -1 aidan-Lenovo-N50-70 Desktop Icons 1

```

Le script `wmctrl` pour la surveillance des fenetres, cela requiert :
- Un interface graphique X11 
- Du fichier `prev_windows.txt`
- Un OS ubuntu ou une distribution linux qui peut supporter cet outil

## 1-2. EXTRACT_WINDOWS_LOGS:
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/COLLECT_FILE_DATA/EXTRACT_WINDOWS_LOGS/
Closed_file.txt  extract_window_host_events.sh  Opened_file.txt

```
On lance apres un script `extract_window_host_events.sh` pour collecter les donnees dans le log et les restructurer pour lister les fichier, app, sites, directory ouverts et fermes separes en deux fichiers pour la detection d'ouverture `Opened_file.txt` et detection de fermeture `Closed_file.txt`. 
Le requierement est bien sur le fichier log `window_changes.log`.

- `extract_window_host_events.sh`:
```bash
#!/bin/bash

# Répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Fichier log à analyser
LOG_FILE="$HOME/window_changes.log"

# Fichiers de sortie (dans le même répertoire que le script)
OPENED_FILE="$SCRIPT_DIR/Opened_file.txt"
CLOSED_FILE="$SCRIPT_DIR/Closed_file.txt"

# Vider les fichiers avant insertion
> "$OPENED_FILE"
> "$CLOSED_FILE"

# Détecter automatiquement le hostname actuel
HOSTNAME_CURRENT=$(hostname)

# Extraction des fenêtres ouvertes avec horodatage
paste -d ' ' \
  <(grep -A 0 "Nouvelles fenêtres ajoutées" "$LOG_FILE" | grep -v "^--$" | awk '{print $1}' | grep .) \
  <(grep -A 0 "Nouvelles fenêtres ajoutées" "$LOG_FILE" | grep -v "^--$" | awk '{print $2}' | grep .) \
  <(grep -A 1 "Nouvelles fenêtres ajoutées" "$LOG_FILE" | grep -v "^--$" | awk -v host="$HOSTNAME_CURRENT" '{for (i=1;i<=NF;i++) if ($i ~ "^"host) {for (j=i+1;j<=NF;j++) printf $j" "; print ""}}' | grep .) \
  > "$OPENED_FILE"

# Extraction des fenêtres fermées avec horodatage
paste -d ' ' \
  <(grep -A 0 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk '{print $1}' | grep .) \
  <(grep -A 0 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk '{print $2}' | grep .) \
  <(grep -A 1 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk -v host="$HOSTNAME_CURRENT" '{for (i=1;i<=NF;i++) if ($i ~ "^"host) {for (j=i+1;j<=NF;j++) printf $j" "; print ""}}' | grep .) \
  > "$CLOSED_FILE"

echo "Fichiers générés :"
echo "- $OPENED_FILE"
echo "- $CLOSED_FILE"
```
- `Opened_file.txt`:
```txt
2026-03-28 00:00:04 ChatGPT - Google Chrome 
2026-03-28 00:00:16 Erreur fichier non trouvé - Google Chrome 
2026-03-28 00:00:56 get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:17 ● get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:19 get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:23 ● get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:35 get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:37 ● get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:41 get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:43 ● get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:47 get_collect_file.py - taskMonitor - Visual Studio Code 

```
- `Closed_file.txt`:
```txt
2026-03-28 00:00:04 New Tab - Google Chrome 
2026-03-28 00:00:16 ChatGPT - Google Chrome 
2026-03-28 00:00:56 collect_file_script.sh - taskMonitor - Visual Studio Code 
2026-03-28 00:01:17 get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:19 ● get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:23 get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:35 ● get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:37 get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:41 ● get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:43 get_collect_file.py - taskMonitor - Visual Studio Code 
2026-03-28 00:01:47 ● get_collect_file.py - taskMonitor - Visual Studio Code 

```
## 1-3. COLLECT_FILE_LOGS:
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/COLLECT_FILE_DATA/COLLECT_FILE_LOGS/
collected_file.txt  collect_file_script.sh  data_file.txt  REQUIEREMENTS
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/COLLECT_FILE_DATA/COLLECT_FILE_LOGS/REQUIEREMENTS/
collected_file.txt  duration_file.py  get_collect_file.py
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ 
```
Ici , on collecte l'ensemble des donnees sur des logs obtenus auparavant, on assemble closed et opened file pour un seul log avec l'heure d'ouverture, de fermeture, la duree d'utilisation ou d'ouverture, le type (file, app, directory) et le log grace au script `collect_file_script.sh` pour avoir `data_file.txt`. 
Le script lancer deux scripts python en ordre pour avoir `data_file.txt`:
- `get_collect_file.py` pour normaliser les logs brutes en collected_file.txt, mais ce dernier repetent l'ouverture ou la fermeture en rendondance comme vu par le log avec des ouvertures et des fermetures sur des heures differentes.
- `duration_file.py` reglent les problemes de redondance en calculant la duree d'ouverture ou d'utilisation vu la premiere heure d'ouverture et la derniere heure de ferneture, et finallement on a `data_file.txt`.

- `collect_file_script.sh` :
```bash
#!/bin/bash

set -e // stop the script if one of those scripts are bugging

echo "Start extract the opened and closed file in window_changes.log..."
../EXTRACT_WINDOWS_LOGS/extract_window_host_events.sh
echo "Opened_file.txt and Closed_file.txt successfully extracted!"

# echo "Start correct closed and opened file..."
# python3 correct_opened-closed_file.py
# echo "Format successfully corrected!"

echo "Start create ./REQUIEREMENTS/collected_file.txt"
python3 ./REQUIEREMENTS/get_collect_file.py
echo "collect_file.txt successfuly created!"

echo "Start to make the real data"
python3 ./REQUIEREMENTS/duration_file.py
echo "data_file.txt successfully created!"
```
- `get_collect_file.py`:
```python

def parse_line(line):
    parts = line.strip().split(" ", 2)
    date = parts[0]
    time = parts[1]
    filename = parts[2]
    return date, time, filename

# Lire les deux fichiers
with open("../EXTRACT_WINDOWS_LOGS/Opened_file.txt", "r", encoding="utf-8") as f_open:
    opened_lines = f_open.readlines()

with open("../EXTRACT_WINDOWS_LOGS/Closed_file.txt", "r", encoding="utf-8") as f_close:
    closed_lines = f_close.readlines()

# Initialiser la liste pour les résultats
true_file_lines = []
used_close_indices = set()  # Pour éviter les doublons de fermeture

# Boucle sur chaque ligne d'ouverture
for i, open_line in enumerate(opened_lines):
    open_date, open_time, filename = parse_line(open_line)

    # Rechercher la fermeture correspondante à partir de la ligne i
    for j in range(i, len(closed_lines)):
        if j in used_close_indices:
            continue
        close_date, close_time, close_filename = parse_line(closed_lines[j])
        if close_filename == filename:
            used_close_indices.add(j)
            true_file_lines.append(f"{open_date} {open_time} {close_time} {filename}\n")
            break

# Écriture dans le fichier de sortie
with open("collected_file.txt", "w", encoding="utf-8") as f_true:
    f_true.writelines(true_file_lines)

print("Fichier 'collected_file.txt' généré avec succès.")
```
- `duration_file.py`:
```python
from datetime import datetime
from collections import defaultdict

input_file = "collected_file.txt"
output_file = "data_file.txt"

# Dictionnaire pour stocker les durées cumulées par titre
durations = defaultdict(float)
last_info = {}  # pour mémoriser date et heures par titre

def normalize_title(title):
    # Enlève le "● " devant le nom si présent
    return title.lstrip('● ').strip()

def get_entry_type(title):
    # Type 1 → contient " - " (file - directory - app)
    if " - " in title:
        return "file-directory-App"
    # Type 2 → juste un répertoire
    return "directory/App"

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        columns = line.split()

        if len(columns) >= 4:
            date = columns[0]
            start_time_str = columns[1]
            end_time_str = columns[2]
            title = " ".join(columns[3:])
            title = normalize_title(title)

            time_format = "%H:%M:%S"
            start_time = datetime.strptime(start_time_str, time_format)
            end_time = datetime.strptime(end_time_str, time_format)

            duration_sec = (end_time - start_time).total_seconds()
            duration_min = duration_sec / 60

            durations[title] += duration_min
            last_info[title] = (date, start_time_str, end_time_str)

# Écriture des résultats
with open(output_file, "w", encoding="utf-8") as f_out:
    for title, total_min in sorted(durations.items(), key=lambda x: x[1], reverse=True):
        date, start_time_str, end_time_str = last_info[title]
        entry_type = get_entry_type(title)
        f_out.write(f"{date} {start_time_str} {end_time_str} {total_min:.2f} {entry_type}   {title}\n")

print(f"Durées totales (en minutes) enregistrées dans {output_file}")

```
- `collected_file.txt`:
```txt
2026-03-28 00:00:04 00:00:16 ChatGPT - Google Chrome
2026-03-28 00:00:56 00:01:17 get_collect_file.py - taskMonitor - Visual Studio Code
2026-03-28 00:01:17 00:01:19 ● get_collect_file.py - taskMonitor - Visual Studio Code
2026-03-28 00:01:19 00:01:23 get_collect_file.py - taskMonitor - Visual Studio Code
2026-03-28 00:01:23 00:01:35 ● get_collect_file.py - taskMonitor - Visual Studio Code
2026-03-28 00:01:35 00:01:37 get_collect_file.py - taskMonitor - Visual Studio Code
2026-03-28 00:01:37 00:01:41 ● get_collect_file.py - taskMonitor - Visual Studio Code
2026-03-28 00:01:41 00:01:43 get_collect_file.py - taskMonitor - Visual Studio Code
2026-03-28 00:01:43 00:01:47 ● get_collect_file.py - taskMonitor - Visual Studio Code

```
- `data_file.txt`:
```txt
2026-03-28 00:01:43 00:01:47 0.85 file-directory-App   get_collect_file.py - taskMonitor - Visual Studio Code
2026-03-28 00:00:04 00:00:16 0.20 file-directory-App   ChatGPT - Google Chrome

```
les requierements sont bien sur dans le dossier `(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/COLLECT_FILE_DATA/COLLECT_FILE_LOGS/REQUIEREMENTS/`.

# 2- COLLECT_COMMAND_LOGS:
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/COLLECT_COMMAND_LOGS/
Collect_Data_command_Script.py  data_command.txt

```
Il suffit d'une seule etape:
On lance le script `Collect_Data_command_Script.py` pour avoir les listes de commandes lances enregistres dans `data_command.txt`.

- `Collect_Data_command_Script.py` :
```python
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
```
- `data_command.txt`:
```txt
2026-03-27, 11:08:52, 11:08:54, 0.033, Commande, code .
2026-03-27, 11:16:58, 11:17:00, 0.033, Commande, conda env list
2026-03-27, 11:17:09, 11:17:11, 0.033, Commande, conda activate MLproject_py311
2026-03-27, 11:17:11, 11:17:13, 0.033, Commande, clear
2026-03-27, 11:17:12, 11:17:14, 0.033, Commande, ls
2026-03-27, 11:17:18, 11:17:20, 0.033, Commande, python3 PREDICT_CLUSTERS_INTENTION.py
2026-03-27, 11:31:29, 11:31:31, 0.033, Commande, clear
2026-03-27, 11:31:30, 11:31:32, 0.033, Commande, python3 PREDICT_CLUSTERS_INTENTION.py
```
# 3- COLLECT_DATA:
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/COLLECT_DATA/
collect_data.py

```
Ici on assemble on dans un seul fichier `data_collect.txt` data_file.txt et data_command.txt avec le script `collect_data.py`.

- `collect_data.py`:
```python
from pathlib import Path
import os

#File source
BASE_DIR = Path(__file__).parent

file1 = BASE_DIR / "../COLLECT_FILE_DATA/COLLECT_FILE_LOGS/data_file.txt"
file2 = BASE_DIR / "../COLLECT_COMMAND_LOGS/data_command.txt"
output_file = BASE_DIR / "../PROCESSING/DATA_COLLECT/data_collect.txt"

# Store formatted line
lines=[]

#file1 traitment
with file1.open(encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 6:
            date = parts[0]
            time_open = parts[1]
            time_close = parts[2]
            duration = parts[3]
            type_ = parts[4]
            name = " ".join(parts[5:])
            lines.append(f"{date}\t{time_open}\t{time_close}\t{duration}\t{type_}\t{name}")


#file2 traitment
with file2.open(encoding="utf-8") as f:
    for line in f:
        parts = [x.strip() for x in line.strip().split(",")]
        if len(parts) >= 6:
            date = parts[0]
            time_open = parts[1]
            time_close = parts[2]
            duration = parts[3]
            type_ = parts[4]
            name = " ".join(parts[5:])
            lines.append(f"{date}\t{time_open}\t{time_close}\t{duration}\t{type_}\t{name}")

#THe final file in TSV
with output_file.open("w", encoding="utf-8") as f:
    for line in lines:
        f.write(line + "\n")

print(f"the TSV file is generated : {output_file.resolve()}")

```
- `PROCESSING/DATA_COLLECT/data_collect.txt`:
```
2026-03-28	00:01:43	00:01:47	0.85	file-directory-App	get_collect_file.py - taskMonitor - Visual Studio Code
2026-03-28	00:00:04	00:00:16	0.20	file-directory-App	ChatGPT - Google Chrome
2026-03-27	11:08:52	11:08:54	0.033	Commande	code .
2026-03-27	11:16:58	11:17:00	0.033	Commande	conda env list
2026-03-27	11:17:09	11:17:11	0.033	Commande	conda activate MLproject_py311
2026-03-27	11:17:11	11:17:13	0.033	Commande	clear
2026-03-27	11:17:12	11:17:14	0.033	Commande	ls
```

# 4- PROCESSING:
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/PROCESSING/
CLUSTERING    DESCRIBE_CLUSTERS  DICT        __pycache__
DATA_COLLECT  DESCRIBE_EVENTS    PARSE_DATA  zLabs_clustering_describe

```
## 4-1. PARSE_DATA:
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/PROCESSING/PARSE_DATA/
events_normalized.csv  PARSE_2.py  parse.py

```
Ici, on normalise les donnees brut  data_collect.txt en .csv avec le script `parse.py` et on a `events_normalized.csv`. 

- `parse.py`:
```python
import pandas as pd
import re
import os

BASE_DIR = os.path.dirname(__file__)
INPUT = os.path.join(BASE_DIR, "../DATA_COLLECT/data_collect.txt")
OUTPUT = os.path.join(BASE_DIR, "events_normalized.csv")

file_regex = re.compile(r"\.[a-zA-Z0-9]+$")


def detect_file(name):
    return bool(file_regex.search(name))


def parse_event(raw):

    parts = raw.split(" - ")

    if len(parts) >= 2:
        filename = parts[0].strip()
        app = parts[-1].strip()

        if detect_file(filename):
            return "file", filename, app, ""

        else:
            return "app", "", app, ""

    else:

        if detect_file(raw):
            return "file", raw, "", ""

        return "app", "", raw, ""


rows = []

with open(INPUT) as f:

    for line in f:

        cols = line.strip().split("\t")

        if len(cols) < 6:
            continue

        date, start, end, duration, type_raw, raw_event = cols

        if type_raw == "Commande":

            rows.append({
                "date": date,
                "start": start,
                "end": end,
                "duration": float(duration),
                "event_type": "command",
                "file": "",
                "app": "Terminal",
                "command": raw_event,
                "raw": raw_event
            })

        else:

            event_type, file, app, command = parse_event(raw_event)

            rows.append({
                "date": date,
                "start": start,
                "end": end,
                "duration": float(duration),
                "event_type": event_type,
                "file": file,
                "app": app,
                "command": command,
                "raw": raw_event
            })


df = pd.DataFrame(rows)

df.to_csv(OUTPUT, index=False)

print("Saved:", OUTPUT)
```
- `events_normalized.csv`:
```csv
date,start,end,duration,event_type,file,app,command,raw
2026-03-28,00:01:43,00:01:47,0.85,file,get_collect_file.py,Visual Studio Code,,get_collect_file.py - taskMonitor - Visual Studio Code
2026-03-28,00:00:04,00:00:16,0.2,app,,Google Chrome,,ChatGPT - Google Chrome
2026-03-27,11:08:52,11:08:54,0.033,command,,Terminal,code .,code .
2026-03-27,11:16:58,11:17:00,0.033,command,,Terminal,conda env list,conda env list
```
- requierements/input => 'data_collect.txt'

## 4-2. DESCRIBE_EVENTS:
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/PROCESSING/DESCRIBE_EVENTS/
command_desc  describe-event2.py  events_described.csv

```
Ici, on decrit chaque raw de events_normalized.csv. C'est l'analyse des fichiers ouverts, app utilises, site visites, commande lance,... avec le script `describe-event2.py` a partir de la colonne `raw` dans `events_normalized.csv`.

- `describe-event2.py`:
```python
import os, re, subprocess, json
import torch, torch.nn as nn, pandas as pd
from transformers import AutoTokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.dirname(__file__)
# ───────────────── CONFIG ─────────────────
CSV_INPUT   = os.path.join(BASE_DIR, "../PARSE_DATA/events_normalized.csv")
CSV_OUTPUT  = os.path.join(BASE_DIR, "events_described.csv")
MODEL_DIR   = os.path.join(BASE_DIR, "../../../Vis_Models/Gen_Desc_Model/full_finetuned")

# Charger les fichiers JSON
FILE_EXTENSION = json.load(open(os.path.join(BASE_DIR, "../DICT/FILE_EXTENSION.json")))
MIME_MAP        = json.load(open(os.path.join(BASE_DIR, "../DICT/mime_map.json")))
TOOLS           = json.load(open(os.path.join(BASE_DIR, "../DICT/TOOLS.json")))

LEXICAL_DIM = 512
BATCH_SIZE  = 8
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ───────────────── DICTS SUPPLÉMENTAIRES ─────────────────
linux_special_files = {
    # ── SYSTEM CONFIG & ENVIRONMENT ──────────────────
    "/etc/environment": "global environment variables",
    "/etc/profile": "system-wide shell profile",
    "/etc/bash.bashrc": "system-wide bash config (Debian/Ubuntu)",
    "/etc/bashrc": "system-wide bash config (RHEL/CentOS)",
    "/etc/hostname": "system static hostname",
    "/etc/issue": "pre-login message/system identification",
    "/etc/motd": "message of the day (post-login)",
    "/etc/locale.conf": "system language and regional settings",
    "/etc/os-release": "operating system identification",
    "/etc/shells": "list of valid login shells",
    "/etc/timezone": "system timezone configuration",
    "/etc/skel/.bashrc": "default bashrc template for new users",
    
    # ── USER SHELL CONFIGS (HOME) ────────────────────
    "~/.bashrc": "user-specific bash aliases and functions",
    "~/.bash_profile": "user login shell configuration",
    "~/.bash_logout": "commands executed at user logout",
    "~/.profile": "user-specific environment settings",
    "~/.zshrc": "Zsh shell configuration (if installed)",
    
    # ── NETWORK & DNS ────────────────────────────────
    "/etc/hosts": "static hostname to IP mapping",
    "/etc/resolv.conf": "DNS resolver configuration",
    "/etc/network/interfaces": "legacy network interface config",
    "/etc/netplan": "modern network configuration (Ubuntu/Debian)",
    "/etc/nsswitch.conf": "name service switch configuration",
    "/etc/host.conf": "resolver lookup order",
    "/etc/protocols": "list of IP protocols and numbers",
    "/etc/services": "list of port names and numbers",
    
    # ── USERS & SECURITY ─────────────────────────────
    "/etc/passwd": "user account information",
    "/etc/shadow": "secure user password hashes",
    "/etc/group": "group account information",
    "/etc/gshadow": "secure group password hashes",
    "/etc/sudoers": "sudo privileges configuration",
    "/etc/pam.d": "pluggable authentication modules config",
    "/etc/login.defs": "shadow password suite configuration",
    "/etc/securetty": "list of terminals allowed for root login",
    "/etc/security/limits.conf": "system resource limits for users",
    "~/.ssh/authorized_keys": "SSH public keys for remote access",
    "~/.ssh/id_rsa": "SSH private key (highly sensitive)",
    "~/.ssh/known_hosts": "list of trusted remote host keys",
    
    # ── FILESYSTEM & STORAGE ─────────────────────────
    "/etc/fstab": "static information about filesystems",
    "/etc/mtab": "list of currently mounted filesystems",
    "/etc/crypttab": "encrypted device table",
    "/etc/exports": "NFS server export configuration",
    "/etc/auto.master": "autofs mount points configuration",
    
    # ── SERVICES & CRON ──────────────────────────────
    "/etc/crontab": "system-wide cron schedule",
    "/etc/cron.d": "modular system cron jobs",
    "/etc/systemd/system": "systemd service unit files",
    "/etc/ssh/sshd_config": "SSH server daemon configuration",
    "/etc/nginx/nginx.conf": "Nginx web server configuration",
    "/etc/apache2/apache2.conf": "Apache web server configuration",
    "/etc/mysql/my.cnf": "MySQL/MariaDB database configuration",
    "/etc/redis/redis.conf": "Redis server configuration",
    
    # ── PACKAGE MANAGEMENT ───────────────────────────
    "/etc/apt/sources.list": "APT software repository list",
    "/etc/apt/sources.list.d": "additional APT repository files",
    "/etc/yum.repos.d": "YUM/DNF repository configuration",
    "/var/lib/dpkg/status": "installed package status database",
    
    # ── KERNEL & HARDWARE ────────────────────────────
    "/etc/modules": "list of kernel modules to load at boot",
    "/etc/modprobe.d": "kernel module loading rules",
    "/etc/sysctl.conf": "kernel runtime parameters (sysctl)",
    "/etc/X11/xorg.conf": "X Server (graphics) configuration",
    "/boot/grub/grub.cfg": "GRUB bootloader configuration",
    
    # ── VIRTUAL FILESYSTEMS (KERNEL/PROCESS) ──────────
    "/proc/cpuinfo": "processor and architecture details",
    "/proc/meminfo": "detailed memory usage statistics",
    "/proc/uptime": "system uptime and idle time",
    "/proc/version": "kernel version and build info",
    "/proc/cmdline": "bootloader kernel parameters",
    "/proc/net/dev": "network interface statistics",
    "/proc/sys": "kernel runtime parameters (sysctl)",
    "/proc/self/exe": "link to current process executable",
    "/dev/null": "null device (data sink)",
    "/dev/zero": "zero device (null byte generator)",
    "/dev/random": "blocking random number generator",
    "/dev/urandom": "non-blocking random number generator",
    "/dev/sda": "primary hard drive device file",
    
    # ── LOGS & HISTORY ────────────────────────────────
    "/var/log/syslog": "central system log (Debian/Ubuntu)",
    "/var/log/messages": "general system log (RHEL/CentOS)",
    "/var/log/auth.log": "authentication and security logs",
    "/var/log/kern.log": "kernel messages log",
    "/var/log/dmesg": "kernel ring buffer messages",
    "/var/log/dpkg.log": "Debian package manager logs",
    "/var/log/apt/history.log": "apt package history",
    "/var/log/faillog": "failed login attempts",
    "/var/log/lastlog": "last login information for users",
    "/var/log/wtmp": "login/logout history (binary)",
    "/var/log/btmp": "failed login records (binary)",
    "~/.bash_history": "user shell command history",
}


# ─────────────────── CLASSES & MODELS ───────────────────
# ─────────────────────────────────────────────
# PARTIE 1 — Modèle T5 pour les fichiers
# ─────────────────────────────────────────────
# ───────────────── CONFIGURATION D'INFÉRENCE ─────────────────
# Ces paramètres forcent le modèle à être plus précis et varié
INFERENCE_CONFIG = {
    "num_beams": 5,                # Explore plus de chemins pour trouver des mots clés (ex: windows)
    "no_repeat_ngram_size": 3,     # Empêche la répétition de suites de 3 mots (ex: "monitoring and monitoring")
    "repetition_penalty": 1.5,     # Pénalise fortement la réutilisation des mêmes mots
    "length_penalty": 1.0,         # Équilibre entre phrases courtes et longues
    "max_new_tokens": 50,          # Limite de longueur pour éviter les phrases qui divaguent
    "early_stopping": True         # Arrête la recherche dès qu'une phrase cohérente est finie
}

# ─────────────────── CLASSES & MODELS ───────────────────

class T5WithFusion(nn.Module):
    def __init__(self, model_name="google/flan-t5-small", lexical_dim=512):
        super().__init__()
        self.t5  = T5ForConditionalGeneration.from_pretrained(model_name)
        self.proj = nn.Linear(lexical_dim, self.t5.config.d_model)

    def forward(self, input_ids=None, attention_mask=None, labels=None,
                lexical_embeds=None, **kwargs):
        inputs_embeds = self.t5.encoder.embed_tokens(input_ids)
        if lexical_embeds is not None:
            lexical_proj  = self.proj(lexical_embeds.float()).to(inputs_embeds.device)
            inputs_embeds = inputs_embeds + lexical_proj.unsqueeze(1)
        return self.t5(
            input_ids=None, attention_mask=attention_mask,
            labels=labels, inputs_embeds=inputs_embeds, **kwargs
        )

    def prepare_inputs_for_generation(self, input_ids, attention_mask=None, **kwargs):
        # Assure que les embeds lexicaux sont transmis pendant la génération auto-régressive
        inputs = self.t5.prepare_inputs_for_generation(
            input_ids, attention_mask=attention_mask, **kwargs
        )
        if "lexical_embeds" in kwargs:
            inputs["lexical_embeds"] = kwargs["lexical_embeds"]
        return inputs

    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.t5, name)


def load_t5_model():
    """Charge tokenizer + modèle T5 fine-tuné."""
    print(f"  Chargement du modèle depuis {MODEL_DIR} ...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model     = T5WithFusion(model_name="google/flan-t5-small", lexical_dim=LEXICAL_DIM)
    
    # Chargement des poids
    state = torch.load(f"{MODEL_DIR}/pytorch_model.bin", map_location=DEVICE)
    model.load_state_dict(state, strict=False)
    model.to(DEVICE).eval()
    
    lex_model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"  Device : {DEVICE}")
    return tokenizer, model, lex_model


def generate_file_descriptions(filenames: list[str], tokenizer, model, lex_model) -> list[str]:
    """
    Génère une description IA avec correction des répétitions et focus amélioré.
    """
    descriptions = []

    for i in range(0, len(filenames), BATCH_SIZE):
        batch = filenames[i : i + BATCH_SIZE]

        # Note : On a légèrement modifié le prompt pour être plus directif ("specific purpose")
        prompts = [
            f"Describe the specific purpose of the following file.\n\nFilename: {name}\n\nDescription:"
            for name in batch
        ]

        inputs = tokenizer(
            prompts, return_tensors="pt",
            padding=True, truncation=True, max_length=128
        ).to(DEVICE)

        with torch.no_grad():
            # Injection de l'INFERENCE_CONFIG ici
            outputs = model.generate(
                input_ids      = inputs["input_ids"],
                attention_mask = inputs["attention_mask"],
                **INFERENCE_CONFIG
            )

        descriptions.extend(
            tokenizer.decode(o, skip_special_tokens=True) for o in outputs
        )
        print(f"    [{i + len(batch)}/{len(filenames)}] fichiers décrits avec succès")

    return descriptions

# ─────────────────── FONCTIONS UTILES ───────────────────
# ─────────────────────────────────────────────
# PARTIE 2 — cmddesc pour les commandes
# ─────────────────────────────────────────────
NOISE_PREFIXES = (
    "Command '", "Argument '", "String '",
    "Number '", "IP address '", "URL '", "JSON '",
    "File '", "Folder '", "Server '",
)

KNOWN_DIRS = {
    "Desktop", "Music", "Public", "Documents", "Videos",
    "Downloads", "Pictures", "Templates",
    # racine filesystem Linux
    "bin", "etc", "lib", "lib32", "lib64", "libx32", "opt", "sbin",
    "tmp", "usr", "var", "home", "root", "boot", "dev", "proc",
    "run", "srv", "sys", "mnt", "media", "snap", "cdrom",
    "lost+found",
}

FILE_RE = re.compile(r"\.[a-zA-Z0-9]+$")


def is_directory(token: str) -> bool:
    """Retourne True si le token ressemble à un répertoire."""
    if "/" in token:
        return True
    if token in KNOWN_DIRS:
        return True
    
    return False


def is_file(token: str) -> bool:
    """Retourne True si le token ressemble à un fichier (a une extension)."""
    return bool(FILE_RE.search(token)) and "/" not in token.rstrip("/")


def extract_context_from_command(command: str) -> tuple[list[str], list[str]]:
    """
    Parcourt les tokens d'une commande et retourne :
      - la liste des fichiers détectés
      - la liste des répertoires détectés
    On ignore les flags (commençant par -) et le premier token (la commande).
    """
    tokens = command.split()
    files, dirs = [], []

    for token in tokens[1:]:
        clean = token.strip("'\"")
        if not clean or clean.startswith("-"):
            continue

        basename = os.path.basename(clean.rstrip("/"))
        if is_file(basename):
            files.append(clean)
        elif is_directory(clean):
            dirs.append(clean)

    # Dédupliquer en préservant l'ordre
    seen  = set()
    files = [f for f in files if not (f in seen or seen.add(f))]
    seen  = set()
    dirs  = [d for d in dirs  if not (d in seen or seen.add(d))]

    return files, dirs


def run_cmddesc(command: str) -> str:
    result = subprocess.run(
        ["cmddesc"], input=command, capture_output=True, text=True
    )
    return result.stdout


def parse_cmddesc_output(raw_output: str) -> str:
    def is_noise(value: str) -> bool:
        return any(value.startswith(p) for p in NOISE_PREFIXES)

    def extract_value(line: str) -> str:
        return re.sub(r"^(desc_\w+|with sudo privilege):\s*", "", line.strip()).strip()

    sub_commands, current, mode = [], [], None

    for line in raw_output.splitlines():
        s = line.strip()

        if re.match(r"^=== Command \d+", s):
            if current:
                sub_commands.append(" + ".join(current))
            current, mode = [], None

        elif "FULL DESCRIPTION APPLIED" in s:
            mode = "full"

        elif "DESCRIPTION SEQUENTIELLE" in s:
            mode = "sequential"

        elif re.match(r"^(desc_|with sudo)", s):
            value = extract_value(s)
            if not value or is_noise(value):
                continue
            if mode == "full":
                if s.lstrip().startswith("desc_cmd"):
                    current.insert(0, value)
                else:
                    current.append(value)
            elif mode == "sequential":
                current.append(value)

    if current:
        sub_commands.append(" + ".join(current))

    result = " | ".join(sub_commands) if sub_commands else "No description found"

    # Nettoyer les préfixes résiduels de cmddesc
    result = re.sub(r"\bdesc_\w+:\s*", "", result).strip()
    result = re.sub(r"\s*\+\s*-\s*", ", ", result)
    result = re.sub(r"Command\s+'[^']+'\s*\+?\s*", "", result).strip()
    result = re.sub(r"^\s*-\s*", "", result).strip()   # tiret résiduel en début
    result = re.sub(r",\s*,", ",", result).strip()     # double virgule
    result = re.sub(r",\s*$", "", result).strip()      # virgule finale
    result = re.sub(r"\s{2,}", " ", result).strip()

    return result if result else "No description found"


def describe_command(command: str) -> str:
    command = command.strip()
    if not command:
        return ""
    try:
        return parse_cmddesc_output(run_cmddesc(command))
    except Exception as e:
        return f"[ERROR: {e}]"
    
def get_file_type(filename: str) -> str:
    """Retourne l'extension ou le type basé sur les dictionnaires."""
    ext = os.path.splitext(filename)[1].lower()
    types = []
    if ext in MIME_MAP: types.append(MIME_MAP[ext].get("comment", ""))
    if ext in FILE_EXTENSION: types.append(FILE_EXTENSION[ext])
    return ", ".join(types) if types else "file"

# ─────────────────── DESCRIPTION FINALE ───────────────────
def amplify_description(target: str, file_desc_map: dict = None) -> str:
    """
    Moteur de détection : Scanne le texte pour enrichir via IA et Dictionnaires.
    Priorité aux Linux Special Files.
    """
    file_desc_map = file_desc_map or {}
    elements = []
    
    # 1. Vérifier si la cible (ou une partie) est un fichier spécial Linux
    # On cherche le match exact du chemin dans linux_special_files
    special_match = None
    for path, info in linux_special_files.items():
        if path in target:
            special_match = info
            break
    
    if special_match:
        elements.append(special_match)
    else:
        # 2. Si pas special, on cherche l'extension et l'IA
        basename = os.path.basename(target.rstrip("/"))
        stem = os.path.splitext(basename)[0]
        
        # Extension / MIME
        ftype = get_file_type(target)
        if ftype != "file":
            elements.append(ftype)
            
        # IA Description
        if stem in file_desc_map:
            ai_val = file_desc_map[stem]
            ai_val = re.sub(r"^[Ii]t (likely|probably) (contains?|collects?|is|provides?)\s*", "", ai_val).strip()
            elements.append(ai_val)

    # 3. Dictionnaire TOOLS (pour détecter bash, nano, etc.)
    for tool, tool_desc in TOOLS.items():
        if re.search(rf"\b{re.escape(tool)}\b", target, re.IGNORECASE):
            elements.append(tool_desc)

    seen = set()
    unique = [e for e in elements if e and not (e.lower() in seen or seen.add(e.lower()))]
    return ", ".join(unique)


def build_description(row: dict, file_desc_map: dict) -> str:
    """
    Formateur final optimisé pour le dataset d'entraînement.
    Incorpore la logique infer_verb et élimine les parenthèses pour une lecture fluide.
    """
    etype = str(row.get("event_type", "")).strip().lower()

    # ── 1. TYPE: FILE ────────────────────────────────
    if etype == "file":
        filename  = str(row.get("file",      "")).strip()
        app       = str(row.get("app",       "")).strip()
        directory = str(row.get("directory", "")).strip()
        enriched_info = amplify_description(filename, file_desc_map)
        
        # Format: Nom, type, contexte, action, contenu
        parts = [f"{filename}, file"]
        if directory: parts.append(f"stored in {directory}")
        if app: parts.append(f"opened with {app}")
        if enriched_info: parts.append(f"contains data related to {enriched_info}")
        
        return ", ".join(p for p in parts if p)

    # ── 2. TYPE: COMMAND ─────────────────────────────
    elif etype == "command":
        command = str(row.get("command", "")).strip()
        cmd_desc = describe_command(command) 
        cmd_files, cmd_dirs = extract_context_from_command(command)

        if cmd_desc and cmd_desc.strip() not in ("", "No description found"):
            cmd_desc_clean = re.sub(r"^-\s*", "", cmd_desc.strip().rstrip(".")).lower()
            base = f"{command}, command, executed in terminal, used to {cmd_desc_clean}"
        else:
            base = f"{command}, command, executed in terminal"

        context_elements = []
        for d in cmd_dirs:
            if d in linux_special_files:
                context_elements.append(f"targeting the special file {d} which is {linux_special_files[d]}")
            else:
                context_elements.append(f"in {d}")
        
        for f in cmd_files:
            f_amplified = amplify_description(f, file_desc_map)
            if f_amplified:
                # Nettoyage des parenthèses éventuelles issues des dictionnaires
                clean_info = f_amplified.replace("(", "").replace(")", "")
                context_elements.append(f"with the {f} file which is a {clean_info}")
            else:
                context_elements.append(f"with the {f} file")

        if context_elements:
            return base + " " + " and ".join(context_elements)
        return base

    # ── 3. TYPE: APP ─────────────────────────────────
    elif etype == "app":
        app = str(row.get("app", "")).strip()
        raw = str(row.get("raw", "")).strip()
        
        title = ""
        if raw and " - " in raw:
            parts_raw = raw.split(" - ")
            candidate = " - ".join(parts_raw[:-1]).strip()
            if candidate.lower() != app.lower():
                title = candidate

        # --- Logique infer_verb réintégrée ---
        def infer_verb(title_str: str, app_str: str) -> str:
            t = title_str.lower()
            a = app_str.lower()
            if any(k in t for k in ("youtube", "twitch", "netflix", "dailymotion", "vimeo", "peertube", "invidious")):
                return "watch"
            if a in ("vlc", "mpv", "totem", "celluloid"):
                return "watch"
            if any(k in t for k in ("spotify", "soundcloud", "deezer", "bandcamp", "last.fm", "music")):
                return "listen to music on"
            if a in ("rhythmbox", "clementine", "audacious", "amarok"):
                return "listen to music on"
            if any(k in t for k in ("gmail", "outlook", "inbox", "mail", "thunderbird", "protonmail")):
                return "read and write emails on"
            if a in ("thunderbird", "evolution", "geary"):
                return "read and write emails on"
            if a in ("visual studio code", "code", "gedit", "nano", "vim", "neovim", "sublime text", "atom", "kate"):
                return "edit files using"
            if any(k in t for k in ("google docs", "overleaf", "notion", "libreoffice", "writer")):
                return "write a document using"
            if any(k in t for k in ("github", "gitlab", "bitbucket")):
                return "review code on"
            if any(k in t for k in ("stack overflow", "reddit", "wikipedia", "medium", "dev.to", "documentation", "mdn", "read the docs")):
                return "read content on"
            if a in ("nautilus", "thunar", "nemo", "dolphin", "files", "pcmanfm"):
                return "navigate files using"
            if a in ("brave", "firefox", "google-chrome", "chromium", "brave-browser", "opera", "vivaldi"):
                return "browse the web using"
            return "use"

        verb = infer_verb(title, app)
        
        if title:
            return f"{app}, application, used to {verb} {title}"
        
        # Description bonus via TOOLS si pas de titre
        app_desc = TOOLS.get(app, "application")
        return f"{app}, {app_desc}, used by the user"

    # ── 4. TYPE: DIRECTORY ───────────────────────────
    elif etype == "directory":
        directory = str(row.get("directory", "")).strip()
        if directory in linux_special_files:
            return f"{directory}, directory, {linux_special_files[directory]}, navigated by the user"
        return f"{directory}, directory, navigated by the user"

    return ""


# ─────────────────── SCRIPT PRINCIPAL ───────────────────
print("[1/4] Lecture CSV...")
df = pd.read_csv(CSV_INPUT).fillna("")
df.columns = df.columns.str.strip().str.lower()

# ── Extraction groupée pour T5 (Fichiers + Commandes)
print("[2/4] Collecte des noms de fichiers pour l'IA...")
stems_to_process = set()

# 1. On récupère les fichiers des événements "file"
for f in df[df.event_type.str.lower()=="file"]["file"]:
    if f:
        stems_to_process.add(os.path.splitext(os.path.basename(f))[0])

# 2. On récupère les fichiers cachés dans les événements "command"
for cmd in df[df.event_type.str.lower()=="command"]["command"]:
    files, _ = extract_context_from_command(cmd)
    for f in files:
        stems_to_process.add(os.path.splitext(os.path.basename(f))[0])

file_desc_map = {}
if stems_to_process:
    stems_list = list(stems_to_process)
    tokenizer, t5_model, lex_model = load_t5_model()
    # On génère les descriptions pour TOUS les fichiers détectés partout
    descriptions = generate_file_descriptions(stems_list, tokenizer, t5_model, lex_model)
    file_desc_map = dict(zip(stems_list, descriptions))

# ── Construction description finale
print("[3/4] Construction de la colonne description...")
df["description"] = df.apply(lambda r: build_description(r.to_dict(), file_desc_map), axis=1)

# ── Sauvegarde
df.to_csv(CSV_OUTPUT, index=False)
print(f"✅ Terminé ! Descriptions générées pour {len(stems_to_process)} fichiers uniques.")
```

- `events_described.csv`:
```csv
date,start,end,duration,event_type,file,app,command,raw,description
2026-03-28,00:01:43,00:01:47,0.85,file,get_collect_file.py,Visual Studio Code,,get_collect_file.py - taskMonitor - Visual Studio Code,"get_collect_file.py, file, opened with Visual Studio Code, contains data related to Python 3 script, text files, data related to get collecting files."
2026-03-28,00:00:04,00:00:16,0.2,app,,Google Chrome,,ChatGPT - Google Chrome,"Google Chrome, application, used to use ChatGPT"
2026-03-27,11:08:52,11:08:54,0.033,command,,Terminal,code .,code .,"code ., command, executed in terminal, used to start visual studio code"
2026-03-27,11:16:58,11:17:00,0.033,command,,Terminal,conda env list,conda env list,"conda env list, command, executed in terminal"
```
============= REQUIEREMENTS ================
Cela recquiert, selon le code :
- ce model `MODEL_DIR   = os.path.join(BASE_DIR, "../../../Vis_Models/Gen_Desc_Model/full_finetuned")` pour decrire un fichier, un app, un directory, 

- ainsi que des dictionnaires :
```python
# Charger les fichiers JSON
FILE_EXTENSION = json.load(open(os.path.join(BASE_DIR, "../DICT/FILE_EXTENSION.json")))
MIME_MAP        = json.load(open(os.path.join(BASE_DIR, "../DICT/mime_map.json")))
TOOLS           = json.load(open(os.path.join(BASE_DIR, "../DICT/TOOLS.json")))

LEXICAL_DIM = 512
BATCH_SIZE  = 8
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ───────────────── DICTS SUPPLÉMENTAIRES ─────────────────
linux_special_files = {
    # ── SYSTEM CONFIG & ENVIRONMENT ──────────────────
    "/etc/environment": "global environment variables",
```

- un commande `cmddesc` pour decrire les commandes lances, il faut l'installer de cet facon :
```md
cd taskMonitor/PROCESSING/DESCRIBE_EVENTS/command_desc/command_describer_project/:
```bash
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/PROCESSING/DESCRIBE_EVENTS/command_desc/command_describer_project/
cmddesc_executable          dist            README.md
command_describer           Makefile        requirements.txt
command_describer.egg-info  pyproject.toml

```


##### Install in editable mode
pip install -e .

##### Run the CLI
cmddesc
```
- un environnement virtuel avec ces requierements installes:
python                      3.11.15
command-describer           0.1.0 
torch                       2.10.0
transformers                5.3.0
tensorflow                  2.21.0
```

## 4-3. CLUSTERING:
```bash
(MLproject_py311) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/PROCESSING/CLUSTERING/
cluster.py  clusters_output.txt

```
Ici, on lance le script `cluster.py` pour clusteriser les raw(descriptions)
de `events_described.csv` et on obtient `clusters_output.txt`.

- `cluster.py`:
```python
"""
cluster_tasks.py
----------------
Lit events_described.csv, regroupe les descriptions en clusters
de tâches globales via le modèle fine-tuné (all-MiniLM-L6-v2).

Suit exactement les étapes d'inférence du notebook :
  1.  Chargement + normalisation
  2.  Shuffle (seed=42)
  3.  Embeddings (normalize=True)
  4.  Matrice de distance cosinus
  5.  Clustering initial → meilleur threshold par silhouette
  6.  Cohésion par cluster
  7.  Reclustering itératif (recluster_subset)
  8.  Extraction des singletons
  9.  Reclustering global des singletons (si ratio >= 20%)
  10. Fusion finale
  11. Reclustering final par cohésion (best_split_by_k)
  12. Métriques finales (silhouette + cohésion)
  13. Sauvegarde du rapport texte → clusters_output.txt
"""

import random
import numpy as np
import pandas as pd
import os

from collections import defaultdict
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sentence_transformers import SentenceTransformer, util

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
CSV_INPUT          = os.path.join(BASE_DIR, "../DESCRIBE_EVENTS/events_described.csv")
OUTPUT_FILE        = os.path.join(BASE_DIR, "clusters_output.txt")
MODEL_DIR          = os.path.join(BASE_DIR, "../../../Vis_Models/final_model")
COHESION_THRESHOLD = 0.34    # seuil cohésion reclustering itératif (étape 7)
SIZE_THRESHOLD     = 10      # taille max avant reclustering forcé   (étape 7)
COHESION_FINAL     = 0.55    # seuil reclustering final              (étape 11)
COHESION_SPLIT_MAX = 0.45    # seuil acceptation d'un split
SINGLETON_RATIO    = 0.10    # ratio min singletons pour reclustering global
THRESHOLDS         = np.arange(0.45, 0.85, 0.01)
RANDOM_SEED        = 42


# ─────────────────────────────────────────────
# ÉTAPE 1 — Chargement + normalisation
# ─────────────────────────────────────────────
def normalize_task(text: str) -> str:
    text = text.replace('\\"', '').replace('"', '')
    return text.lower().strip()


print("=" * 60)
print("cluster_tasks.py")
print("=" * 60)

print(f"\n[1] Chargement de {CSV_INPUT} ...")
df = pd.read_csv(CSV_INPUT)
df.columns = df.columns.str.strip().str.lower()

if "description" not in df.columns:
    raise ValueError("Colonne 'description' introuvable dans le CSV.")

df["description"] = df["description"].fillna("").astype(str)
tasks_raw = [normalize_task(t) for t in df["description"].tolist()]
tasks_raw = [t for t in tasks_raw if t]
print(f"    {len(tasks_raw)} descriptions chargées.")

# Déduplication — on garde uniquement les descriptions uniques
seen      = set()
tasks_raw = [t for t in tasks_raw if not (t in seen or seen.add(t))]
print(f"    {len(tasks_raw)} descriptions après déduplication.")


# ─────────────────────────────────────────────
# ÉTAPE 2 — Shuffle (seed=42)
# ─────────────────────────────────────────────
print("\n[2] Shuffle (seed=42) ...")
tasks = tasks_raw[:]
random.seed(RANDOM_SEED)
random.shuffle(tasks)


# ─────────────────────────────────────────────
# ÉTAPE 3 — Embeddings
# ─────────────────────────────────────────────
print(f"\n[3] Chargement du modèle : {MODEL_DIR} ...")
model = SentenceTransformer(MODEL_DIR)
model.eval()

print("    Calcul des embeddings ...")
embeddings = model.encode(
    tasks,
    convert_to_tensor=True,
    normalize_embeddings=True
)


# ─────────────────────────────────────────────
# ÉTAPE 4 — Matrice de distance
# ─────────────────────────────────────────────
print("\n[4] Calcul de la matrice de distance ...")
sim  = util.cos_sim(embeddings, embeddings).cpu().numpy()
dist = 1 - sim
dist = np.clip(dist, 0, None)


# ─────────────────────────────────────────────
# ÉTAPE 5 — Clustering initial
# ─────────────────────────────────────────────
print("\n[5] Clustering initial (recherche meilleur threshold) ...")

def cluster_cohesion_map(dist, labels):
    clusters = defaultdict(list)
    for i, c in enumerate(labels):
        clusters[c].append(i)
    cohesions = {}
    for c, idxs in clusters.items():
        if len(idxs) < 2:
            cohesions[c] = 0.0
            continue
        sub = dist[np.ix_(idxs, idxs)]
        cohesions[c] = sub.mean()
    return cohesions

best = {"th": None, "silhouette": -1, "labels": None, "cohesion": None}

for th in THRESHOLDS:
    clustering = AgglomerativeClustering(
        n_clusters=None,
        metric="precomputed",
        linkage="average",
        distance_threshold=th
    )
    labels     = clustering.fit_predict(dist)
    n_clusters = len(set(labels))

    if n_clusters <= 1 or n_clusters > len(tasks) // 2:
        continue

    sil      = silhouette_score(dist, labels, metric="precomputed")
    cohesion = cluster_cohesion_map(dist, labels)

    if sil > best["silhouette"]:
        best.update({"th": th, "silhouette": sil,
                     "labels": labels, "cohesion": cohesion})

print(f"    Meilleur threshold : {best['th']:.2f} | silhouette : {best['silhouette']:.3f}")

groups = defaultdict(list)
for task, lbl in zip(tasks, best["labels"]):
    groups[lbl].append(task)


# ─────────────────────────────────────────────
# ÉTAPE 6 — Cohésion par cluster
# ─────────────────────────────────────────────
print("\n[6] Cohésion par cluster ...")

cluster_cohesions = []
for c, items in groups.items():
    idxs = [tasks.index(t) for t in items]
    if len(idxs) > 1:
        d   = dist[np.ix_(idxs, idxs)]
        coh = d[np.triu_indices_from(d, 1)].mean()
        cluster_cohesions.append(coh)

mean_cohesion = np.mean(cluster_cohesions) if cluster_cohesions else 0.0
print(f"    Cohésion moyenne initiale : {mean_cohesion:.3f}")


# ─────────────────────────────────────────────
# ÉTAPE 7 — Reclustering itératif (best_split_by_k)
# ─────────────────────────────────────────────
print("\n[7] Reclustering itératif ...")

def compute_cohesion(sub_dist):
    n = sub_dist.shape[0]
    if n < 2:
        return 0.0
    return sub_dist[np.triu_indices_from(sub_dist, 1)].mean()


def best_split_by_k(tasks_subset, dist_matrix_subset):
    """
    Cherche le plus petit k (2..n) tel que cohésion moyenne <= COHESION_SPLIT_MAX.
    """
    n = len(tasks_subset)
    for k in range(2, n + 1):
        clustering = AgglomerativeClustering(
            n_clusters=k,
            metric="precomputed",
            linkage="average"
        )
        labels = clustering.fit_predict(dist_matrix_subset)
        total  = sum(
            compute_cohesion(
                dist_matrix_subset[np.ix_(
                    np.where(labels == lbl)[0],
                    np.where(labels == lbl)[0]
                )]
            )
            for lbl in set(labels)
        )
        avg = total / k
        if avg <= COHESION_SPLIT_MAX:
            return {"k": k, "labels": labels, "avg_cohesion": avg}
    return {"k": None, "labels": None, "avg_cohesion": None}


final_groups      = {}
new_label_counter = 0
clusters_to_check = list(groups.values())

while clusters_to_check:
    current = clusters_to_check.pop(0)
    n       = len(current)

    if n < 2:
        final_groups[new_label_counter] = current
        new_label_counter += 1
        continue

    idxs     = [tasks.index(t) for t in current]
    sub_dist = dist[np.ix_(idxs, idxs)]
    coh      = compute_cohesion(sub_dist)

    # Reclustering si cohésion trop haute OU cluster trop grand
    should_recluster = (coh > COHESION_THRESHOLD) or (n > SIZE_THRESHOLD)

    if should_recluster:
        split = best_split_by_k(current, sub_dist)
        if split["labels"] is None:
            final_groups[new_label_counter] = current
            new_label_counter += 1
        else:
            new_sub_groups = defaultdict(list)
            for i, lbl in enumerate(split["labels"]):
                new_sub_groups[lbl].append(current[i])
            for sub_items in new_sub_groups.values():
                clusters_to_check.append(sub_items)
    else:
        final_groups[new_label_counter] = current
        new_label_counter += 1

print(f"    {len(final_groups)} clusters après reclustering itératif.")


# ─────────────────────────────────────────────
# ÉTAPE 8 — Extraction des singletons
# ─────────────────────────────────────────────
print("\n[8] Extraction des singletons ...")

singletons           = []
non_singleton_groups = {}

for cid, items in final_groups.items():
    if len(items) == 1:
        singletons.append(items[0])
    else:
        non_singleton_groups[cid] = items

print(f"    {len(singletons)} singletons sur {len(tasks)} tâches.")


# ─────────────────────────────────────────────
# ÉTAPE 9 — Reclustering global des singletons
# ─────────────────────────────────────────────
print("\n[9] Reclustering global des singletons ...")

singleton_clusters = {}

if len(singletons) / len(tasks) < SINGLETON_RATIO:
    print("    Ratio insuffisant → singletons conservés tels quels.")
    for t in singletons:
        singleton_clusters[len(singleton_clusters)] = [t]
else:
    print("    Reclustering global des singletons activé.")
    singleton_idxs = [tasks.index(t) for t in singletons]
    new_dist       = dist[np.ix_(singleton_idxs, singleton_idxs)]
    new_dist       = np.clip(new_dist, 0, None)

    best_singleton = {"th": None, "silhouette": -1, "labels": None}

    for th in THRESHOLDS:
        if len(singletons) < 2:
            break
        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric="precomputed",
            linkage="average",
            distance_threshold=th
        )
        labels     = clustering.fit_predict(new_dist)
        n_clusters = len(set(labels))

        if n_clusters <= 1 or n_clusters > len(singletons) // 2:
            continue

        sil = silhouette_score(new_dist, labels, metric="precomputed")
        if sil > best_singleton["silhouette"]:
            best_singleton.update({"th": th, "silhouette": sil,
                                   "labels": labels})

    if best_singleton["labels"] is None:
        for t in singletons:
            singleton_clusters[len(singleton_clusters)] = [t]
    else:
        tmp = defaultdict(list)
        for task, lbl in zip(singletons, best_singleton["labels"]):
            tmp[lbl].append(task)
        singleton_clusters = dict(tmp)


# ─────────────────────────────────────────────
# ÉTAPE 10 — Fusion finale
# ─────────────────────────────────────────────
print("\n[10] Fusion finale ...")

final_merged_groups = {}
cid = 0
for items in non_singleton_groups.values():
    final_merged_groups[cid] = items
    cid += 1
for items in singleton_clusters.values():
    final_merged_groups[cid] = items
    cid += 1

task_to_index = {t: i for i, t in enumerate(tasks)}
labels_final  = np.full(len(tasks), -1, dtype=int)
for c, items in final_merged_groups.items():
    for t in items:
        labels_final[task_to_index[t]] = c

assert np.all(labels_final != -1), "Certaines tâches n'ont pas été assignées."
print(f"    {len(final_merged_groups)} clusters fusionnés.")


# ─────────────────────────────────────────────
# ÉTAPE 11 — Reclustering final (best_split_by_k)
# ─────────────────────────────────────────────
print(f"\n[11] Reclustering final (seuil cohésion = {COHESION_FINAL}) ...")

clusters_from_labels = defaultdict(list)
for idx, c in enumerate(labels_final):
    clusters_from_labels[c].append(tasks[idx])

clusters_to_recluster = []
clusters_kept         = {}

for c, items in clusters_from_labels.items():
    idxs     = [tasks.index(t) for t in items]
    sub_dist = dist[np.ix_(idxs, idxs)]
    coh      = compute_cohesion(sub_dist)
    if coh > COHESION_FINAL and len(idxs) >= 2:
        clusters_to_recluster.append((c, items))
    else:
        clusters_kept[c] = items

final_reclustered = {}
new_cid           = 0
assigned_tasks    = set()

for cid, items in clusters_to_recluster:
    queue = [items]
    while queue:
        current  = queue.pop(0)
        idxs     = [tasks.index(t) for t in current]
        sub_dist = dist[np.ix_(idxs, idxs)]
        coh      = compute_cohesion(sub_dist)

        if coh > COHESION_SPLIT_MAX:
            split = best_split_by_k(current, sub_dist)
            if split["labels"] is None:
                final_reclustered[new_cid] = current
                new_cid += 1
                assigned_tasks.update(current)
            else:
                new_groups = defaultdict(list)
                for i, lbl in enumerate(split["labels"]):
                    new_groups[lbl].append(current[i])
                for sub_items in new_groups.values():
                    sub_idxs = [tasks.index(t) for t in sub_items]
                    sub_d    = dist[np.ix_(sub_idxs, sub_idxs)]
                    if compute_cohesion(sub_d) > COHESION_SPLIT_MAX:
                        queue.append(sub_items)
                    else:
                        final_reclustered[new_cid] = sub_items
                        new_cid += 1
                        assigned_tasks.update(sub_items)
        else:
            final_reclustered[new_cid] = current
            new_cid += 1
            assigned_tasks.update(current)

for items in clusters_kept.values():
    if not any(t in assigned_tasks for t in items):
        final_reclustered[new_cid] = items
        new_cid += 1
        assigned_tasks.update(items)

print(f"    {len(final_reclustered)} clusters après reclustering final.")


# ─────────────────────────────────────────────
# ÉTAPE 12 — Métriques finales
# ─────────────────────────────────────────────
print("\n[12] Métriques finales ...")

labels_final2 = np.full(len(tasks), -1, dtype=int)
for c, items in final_reclustered.items():
    for t in items:
        labels_final2[tasks.index(t)] = c

n_clusters_final = len(set(labels_final2))

sil_final = (
    silhouette_score(dist, labels_final2, metric="precomputed")
    if 1 < n_clusters_final < len(tasks) else 0.0
)

cohesions_list = []
for c, items in final_reclustered.items():
    idxs = [tasks.index(t) for t in items]
    if len(idxs) >= 2:
        d   = dist[np.ix_(idxs, idxs)]
        coh = compute_cohesion(d)
        cohesions_list.append(coh)

mean_cohesion_final = np.mean(cohesions_list) if cohesions_list else 0.0

print(f"    Nombre de clusters   : {n_clusters_final}")
print(f"    Silhouette finale    : {sil_final:.3f}")
print(f"    Cohésion moyenne     : {mean_cohesion_final:.3f}")


# ─────────────────────────────────────────────
# ÉTAPE 14 — Post-processing ciblé
#
# Pour chaque cluster :
#   A) Cohésion >= POSTPROC_SPLIT_MIN → rediviser,
#      chaque fragment rejoint le cluster existant
#      le plus proche (si sim >= POSTPROC_MERGE_SIM),
#      sinon devient singleton.
#   B) Cohésion < POSTPROC_SPLIT_MIN → vérifier chaque
#      élément : s'il est plus proche d'un autre cluster
#      que du sien (marge >= POSTPROC_REASSIGN_MARGIN),
#      on le réassigne, sinon il reste.
# ─────────────────────────────────────────────
print("\n[14] Post-processing ciblé ...")

POSTPROC_SPLIT_MIN      = 0.40   # cohésion min pour forcer redivision
POSTPROC_MERGE_SIM      = 0.55   # similarité min pour fusionner dans un cluster existant
POSTPROC_REASSIGN_MARGIN = 0.05  # marge min pour réassigner un élément


def mean_sim_to_cluster(task_idx: int, cluster_idxs: list[int], sim_matrix: np.ndarray) -> float:
    """Similarité moyenne d'un élément avec les membres d'un cluster (lui exclu)."""
    others = [i for i in cluster_idxs if i != task_idx]
    if not others:
        return 0.0
    return float(sim_matrix[task_idx, others].mean())


# Matrice de similarité (1 - dist)
sim_matrix = 1 - dist

# Travailler sur une copie mutable
working_groups = {c: list(items) for c, items in final_reclustered.items()}
next_cid       = max(working_groups.keys()) + 1

# ── A) Rediviser les clusters trop cohésifs ──────────────
to_split = [
    cid for cid, items in working_groups.items()
    if len(items) >= 2 and compute_cohesion(
        dist[np.ix_([tasks.index(t) for t in items],
                    [tasks.index(t) for t in items])]
    ) >= POSTPROC_SPLIT_MIN
]

freed_elements = []   # éléments libérés après division

for cid in to_split:
    items    = working_groups.pop(cid)
    idxs     = [tasks.index(t) for t in items]
    sub_dist = dist[np.ix_(idxs, idxs)]
    split    = best_split_by_k(items, sub_dist)

    if split["labels"] is None:
        # Pas de split valide → libérer tous les éléments
        freed_elements.extend(items)
    else:
        sub_groups = defaultdict(list)
        for i, lbl in enumerate(split["labels"]):
            sub_groups[lbl].append(items[i])
        freed_elements.extend(items)   # on libère tout pour réassignation

print(f"    {len(to_split)} cluster(s) redivisé(s) → {len(freed_elements)} élément(s) libérés.")

# ── B) Réassigner chaque élément libéré ─────────────────
# (et aussi les éléments des clusters incohérents détectés par B)

# Détecter les éléments mal placés dans les clusters restants
for cid, items in list(working_groups.items()):
    if len(items) < 2:
        continue
    cluster_idxs = [tasks.index(t) for t in items]
    for t in items:
        t_idx    = tasks.index(t)
        sim_self = mean_sim_to_cluster(t_idx, cluster_idxs, sim_matrix)

        # Chercher le meilleur cluster alternatif
        best_other_sim = 0.0
        for other_cid, other_items in working_groups.items():
            if other_cid == cid or len(other_items) == 0:
                continue
            other_idxs   = [tasks.index(x) for x in other_items]
            sim_other    = mean_sim_to_cluster(t_idx, other_idxs, sim_matrix)
            if sim_other > best_other_sim:
                best_other_sim = sim_other

        if best_other_sim > sim_self + POSTPROC_REASSIGN_MARGIN:
            freed_elements.append(t)

# Dédupliquer freed_elements (un élément peut avoir été libéré deux fois)
seen_freed = set()
freed_elements = [t for t in freed_elements if not (t in seen_freed or seen_freed.add(t))]

# Retirer les éléments libérés de leurs clusters actuels
for t in freed_elements:
    for cid in list(working_groups.keys()):
        if t in working_groups[cid]:
            working_groups[cid].remove(t)

# Supprimer les clusters vides
working_groups = {c: items for c, items in working_groups.items() if items}

# Réassigner chaque élément libéré
reassigned = 0
new_singletons = 0

for t in freed_elements:
    t_idx      = tasks.index(t)
    best_cid   = None
    best_sim   = POSTPROC_MERGE_SIM   # seuil minimum

    for cid, items in working_groups.items():
        if not items:
            continue
        other_idxs = [tasks.index(x) for x in items]
        sim        = mean_sim_to_cluster(t_idx, other_idxs, sim_matrix)
        if sim > best_sim:
            best_sim = sim
            best_cid = cid

    if best_cid is not None:
        working_groups[best_cid].append(t)
        reassigned += 1
    else:
        # Singleton
        working_groups[next_cid] = [t]
        next_cid += 1
        new_singletons += 1

# Renuméroter proprement
final_reclustered = {i: items for i, items in enumerate(working_groups.values())}

print(f"    {reassigned} élément(s) réassigné(s), {new_singletons} nouveau(x) singleton(s).")
print(f"    {len(final_reclustered)} clusters après post-processing.")

# ── Fusion intelligente des singletons avant 'Autres petites tâches' ──
SINGLETON_MERGE_SIM = 0.45

singletons_to_group = [
    items[0]
    for items in final_reclustered.values()
    if len(items) == 1
]

# Retirer les singletons
final_reclustered = {
    cid: items
    for cid, items in final_reclustered.items()
    if len(items) > 1
}

sim_matrix_post = 1 - dist
singletons_merged  = 0
singletons_orphans = []

for t in singletons_to_group:
    t_idx    = tasks.index(t)
    best_cid = None
    best_sim = SINGLETON_MERGE_SIM

    for cid, items in final_reclustered.items():
        if len(items) < 2:
            continue
        other_idxs = [tasks.index(x) for x in items]
        sim = float(sim_matrix_post[t_idx, other_idxs].mean())
        if sim > best_sim:
            best_sim = sim
            best_cid = cid

    if best_cid is not None:
        final_reclustered[best_cid].append(t)
        singletons_merged += 1
    else:
        singletons_orphans.append(t)

print(f"    {singletons_merged} singleton(s) fusionné(s) dans un cluster existant.")
print(f"    {len(singletons_orphans)} singleton(s) orphelins → 'Autres petites tâches'.")

if singletons_orphans:
    autres_cid = (max(final_reclustered.keys()) + 1) if final_reclustered else 0
    final_reclustered[autres_cid] = singletons_orphans
    final_reclustered = {i: items for i, items in enumerate(final_reclustered.values())}
    AUTRES_CID = len(final_reclustered) - 1
    print(f"    Cluster 'Autres petites tâches' : {len(singletons_orphans)} tâche(s).")
else:
    final_reclustered = {i: items for i, items in enumerate(final_reclustered.values())}
    AUTRES_CID = None
    print("    Aucun singleton orphelin.")


# ─────────────────────────────────────────────
# Recalcul métriques après étape 14
# ─────────────────────────────────────────────
labels_final2 = np.full(len(tasks), -1, dtype=int)
for c, items in final_reclustered.items():
    for t in items:
        labels_final2[tasks.index(t)] = c

n_clusters_final = len(set(labels_final2))

sil_final = (
    silhouette_score(dist, labels_final2, metric="precomputed")
    if 1 < n_clusters_final < len(tasks) else 0.0
)

cohesions_list = []
for c, items in final_reclustered.items():
    idxs = [tasks.index(t) for t in items]
    if len(idxs) >= 2:
        cohesions_list.append(compute_cohesion(dist[np.ix_(idxs, idxs)]))

mean_cohesion_final = np.mean(cohesions_list) if cohesions_list else 0.0

print(f"    Silhouette après post-processing : {sil_final:.3f}")
print(f"    Cohésion moyenne après           : {mean_cohesion_final:.3f}")


# ─────────────────────────────────────────────
# ÉTAPE 13 — Sauvegarde du rapport texte
# ─────────────────────────────────────────────
print(f"\n[13] Écriture du rapport dans {OUTPUT_FILE} ...")

lines = []
lines.append("=" * 60)
lines.append("RAPPORT DE CLUSTERING DES TÂCHES")
lines.append("=" * 60)
lines.append(f"Tâches totales          : {len(tasks)}")
lines.append(f"Nombre de clusters      : {n_clusters_final}")
lines.append(f"Silhouette finale       : {sil_final:.3f}")
lines.append(f"Cohésion moyenne finale : {mean_cohesion_final:.3f}")
lines.append("")

for c, items in final_reclustered.items():
    idxs  = [tasks.index(t) for t in items]
    coh   = compute_cohesion(dist[np.ix_(idxs, idxs)])
    label = "Autres petites tâches" if c == AUTRES_CID else f"Cluster {c}"

    lines.append("─" * 60)
    lines.append(f"{label}  |  {len(items)} tâche(s)  |  cohésion = {coh:.3f}")
    lines.append("─" * 60)
    for t in items:
        lines.append(f"  • {t}")
    lines.append("")

lines.append("=" * 60)
lines.append("FIN DU RAPPORT")
lines.append("=" * 60)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n✅ Rapport sauvegardé : {OUTPUT_FILE}")
print(f"   {n_clusters_final} clusters | {len(tasks)} tâches")
```
- `clusters_output.txt`:
```txt
============================================================
RAPPORT DE CLUSTERING DES TÂCHES
============================================================
Tâches totales          : 38
Nombre de clusters      : 8
Silhouette finale       : 0.352
Cohésion moyenne finale : 0.402

────────────────────────────────────────────────────────────
Cluster 0  |  10 tâche(s)  |  cohésion = 0.335
────────────────────────────────────────────────────────────
  • git commit -m, command, executed in terminal, used to commits staged changes to the local repository with a message
  • git commit -m reorganize file and directories, command, executed in terminal, used to commits staged changes to the local repository with a message
  • git commit -m moved collect_file_script, command, executed in terminal, used to commits staged changes to the local repository with a message
  • git commit -m parse_data, command, executed in terminal, used to commits staged changes to the local repository with a message
  • git commit -m arrange collect file script, command, executed in terminal, used to commits staged changes to the local repository with a message
  • code ., command, executed in terminal, used to start visual studio code
  • git commit -m correct directory to parse and describe-events, command, executed in terminal, used to commits staged changes to the local repository with a message
  • git status, command, executed in terminal, used to view the status of the local repository
  • git commit -m move brouillon to labs, command, executed in terminal, used to commits staged changes to the local repository with a message
  • git commit -m removed predict_ch et predict_ge, command, executed in terminal, used to commits staged changes to the local repository with a message

────────────────────────────────────────────────────────────
Cluster 1  |  2 tâche(s)  |  cohésion = 0.316
────────────────────────────────────────────────────────────
  • clear, command, executed in terminal
  • clear, command, executed in terminal, used to clear the screen

```

==================== REQUIEREMENTS ========================
- Le modele `MODEL_DIR          = os.path.join(BASE_DIR, "../../../Vis_Models/final_model")` pour le clustering

- et le meme env python 

## 4-4. DESCRIBE_CLUSTERS:
```bash
(MLproject_py311) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization$ ls taskMonitor/PROCESSING/DESCRIBE_CLUSTERS/
clusters_with_intentions.jsonl  PREDICT_CLUSTERS_INTENTION.py
clusters_with_intentions.txt

```
Ici , on genere le global task intention pour chaque clusters grace au script `PREDICT_CLUSTERS_INTENTION.py` et on obtient `clusters_with_intentions.txt`.

================= REQUIEREMENTS ===============
- Le modele pour generer le global task intention est `DEFAULT_MODEL     = os.path.join(BASE_DIR, "../../../Vis_Models/final_Model_V3/final_model")
`.

- `PREDICT_CLUSTERS_INTENTION.py`:
```python
#!/usr/bin/env python3
"""
============================================================
  Cluster Global Task Intention Predictor
  Usage: python predict_cluster_intentions.py [--input FILE] [--model PATH]
============================================================

Entrée  : clusters_output.txt  (rapport de clustering formaté)
Modèle  : kaggle/working/flan-t5-task-intention/final_model/
Sorties : clusters_with_intentions.txt   — rapport lisible
          clusters_with_intentions.jsonl — format structuré
============================================================
"""

import re
import json
import sys
import argparse
from pathlib import Path
import os

import torch
from transformers import T5ForConditionalGeneration, T5TokenizerFast


# ─────────────────────────────────────────────────────────────
# CONFIG  — modifie ces valeurs selon ton environnement
# ─────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(__file__)

DEFAULT_INPUT     = os.path.join(BASE_DIR, "../CLUSTERING/clusters_output.txt")
DEFAULT_MODEL     = os.path.join(BASE_DIR, "../../../Vis_Models/final_Model_V3/final_model")
DEFAULT_OUT_TXT   = os.path.join(BASE_DIR, "clusters_with_intentions.txt")
DEFAULT_OUT_JSONL = os.path.join(BASE_DIR, "clusters_with_intentions.jsonl")

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

VERB_MAP = load_json(os.path.join(BASE_DIR, "../DICT/VERB_MAP_EXTENDED.json"))
VERB_MAP = {k.lower(): v.lower() for k, v in VERB_MAP.items()}

# Identique aux hyperparamètres d'inférence utilisés à l'entraînement
INFERENCE_CONFIG = {
    "num_beams":            4,
    "no_repeat_ngram_size": 4,
    "repetition_penalty":   1.3,
    "max_new_tokens":       48,
    "early_stopping":       True,
}

MAX_INPUT_LENGTH = 448   # même valeur que CONFIG["max_input_length"]


# ─────────────────────────────────────────────────────────────
# 1. PARSING  clusters_output.txt
# ─────────────────────────────────────────────────────────────
def parse_clusters(filepath: str) -> list:
    """
    Lit le rapport de clustering et retourne une liste de dicts :
        {
            "cluster_id" : str,   ex. "Cluster 0" / "Autres petites tâches"
            "num_tasks"  : int,
            "cohesion"   : float,
            "items"      : [str, ...]   # items déjà formatés dans le fichier
        }

    Format attendu dans le fichier :
        Cluster N  |  K tâche(s)  |  cohésion = X.XXX
        Autres petites tâches  |  K tâche(s)  |  cohésion = X.XXX
    suivi de lignes "  • <item>"
    """
    clusters = []
    current  = None

    header_re = re.compile(
        r"^(Cluster\s+\d+|Autres\s+petites\s+t[aâ]ches)"
        r"\s*\|\s*(\d+)\s+t[aâ]che\(s\)"
        r"\s*\|\s*coh[eé]sion\s*=\s*([\d.]+)",
        re.IGNORECASE,
    )
    item_re = re.compile(r"^\s*[•\-\*]\s+(.+)$")

    with open(filepath, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip()
            m = header_re.search(line)
            if m:
                if current:
                    clusters.append(current)
                current = {
                    "cluster_id": m.group(1).strip(),
                    "num_tasks":  int(m.group(2)),
                    "cohesion":   float(m.group(3)),
                    "items":      [],
                }
                continue
            if current:
                m2 = item_re.match(line)
                if m2:
                    current["items"].append(m2.group(1).strip())

    if current:
        clusters.append(current)

    # ── Éclater "Autres petites tâches" en singletons ────────
    expanded = []
    for c in clusters:
        if re.search(r"autres\s+petites\s+t[aâ]ches", c["cluster_id"], re.IGNORECASE):
            for idx, item in enumerate(c["items"]):
                expanded.append({
                    "cluster_id": f"Autres petites tâches — singleton {idx + 1}",
                    "num_tasks":  1,
                    "cohesion":   c["cohesion"],
                    "items":      [item],
                    "is_singleton": True,
                })
        else:
            c.setdefault("is_singleton", False)
            expanded.append(c)

    return expanded


# ─────────────────────────────────────────────────────────────
# 2. FORMATAGE DU PROMPT
#    Identique au format utilisé pendant l'entraînement
# ─────────────────────────────────────────────────────────────
def format_prompt(items):
    items_text = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(items))
    return (
        "Based on the following list of task items, "
        "generate a concise global task intention in one sentence:\n"
        f"{items_text}"
    )


# ─────────────────────────────────────────────────────────────
# 3. CHARGEMENT DU MODÈLE
# ─────────────────────────────────────────────────────────────
def load_model(model_path: str):
    path = Path(model_path)
    if not path.exists():
        sys.exit(
            f"\n[ERREUR] Modèle introuvable : {model_path}\n"
            "  → Vérifie DEFAULT_MODEL ou utilise --model <chemin>\n"
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Device : {device}")
    if device == "cuda":
        print(f"  GPU    : {torch.cuda.get_device_name(0)}")
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"  VRAM   : {vram:.1f} GB")

    print(f"  Chargement depuis : {model_path}")
    tokenizer = T5TokenizerFast.from_pretrained(model_path)
    model = T5ForConditionalGeneration.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
    )
    if device == "cpu":
        model.to(device)
    model.eval()
    print("  Modele pret\n")

    return model, tokenizer, device

# ─────────────────────────────────────────────
# SIMPLE ACTION EXTRACTION (pour singletons)
# ─────────────────────────────────────────────


STOP_WORDS = {
    "of", "to", "for", "with", "in", "on", "at", "from",
    "by", "about", "as", "into", "after", "before"
}

COMMON_VERBS = {
    "create", "run", "execute", "install", "remove", "update",
    "send", "open", "read", "write", "build", "compile",
    "check", "verify", "record", "display", "launch",
    "render", "provide", "handle", "manage", "analyze",
    "list", "clear", "exit", "play", "search"
}

def clean_segment(seg):
    seg = seg.lower().strip()
    seg = re.sub(
        r"(command used to|used to|used for|used in|opened with|written in|executed in)",
        "",
        seg
    )
    return seg.strip()

def detect_verb(word):
    if word in VERB_MAP:
        return VERB_MAP[word]
    if word in COMMON_VERBS:
        return word
    return None

def extract_action(item):
    parts = [p.strip() for p in item.split(",") if p.strip()]

    INVALID_STARTS = {
        "text", "data", "file", "application", "plain", "script", "document"
    }

    # ── 1. PRIORITÉ : segments avec "used to"
    for part in parts:
        if "used to" in part:
            segment = clean_segment(part)
            words = segment.split()

            if not words:
                continue

            # 🔥 ignorer bruit
            if words[0] in INVALID_STARTS:
                continue

            verb = detect_verb(words[0])
            if not verb:
                continue

            obj_words = []
            for w in words[1:]:
                if w in STOP_WORDS:
                    break
                obj_words.append(w)

            return verb + (" " + " ".join(obj_words) if obj_words else "")

    # ── 2. FALLBACK : mais filtré
    for part in reversed(parts):
        segment = clean_segment(part)
        words = segment.split()

        if not words:
            continue

        # 🔥 ignorer bruit direct
        if words[0] in INVALID_STARTS:
            continue

        verb = detect_verb(words[0])
        if not verb:
            continue

        obj_words = []
        for w in words[1:]:
            if w in STOP_WORDS:
                break
            obj_words.append(w)

        return verb + (" " + " ".join(obj_words) if obj_words else "")

    return None


def generate_simple_intention(item: str) -> str:
    item_lower = item.lower()
    obj = item.split(",")[0].strip()
    obj_lower = obj.lower()

    # ─────────────────────────────────────────────
    # 🔥 1. PRIORITÉ MAX — FILE OPENED WITH APP
    # ─────────────────────────────────────────────
    if "file" in item_lower and "opened with" in item_lower:
        match = re.search(r"opened with ([^,]+)", item_lower)
        if match:
            app = match.group(1).strip().title()
            return f"open {obj} with {app}"

    # ─────────────────────────────────────────────
    # 🔥 2. EXTRACTION ACTION
    # ─────────────────────────────────────────────
    action = extract_action(item)

    # ─────────────────────────────────────────────
    # 🔥 3. FILTRE ANTI-BRUIT
    # ─────────────────────────────────────────────
    INVALID_ACTIONS = {
        "text files", "plain text", "data related", "file",
        "application log", "script", "document"
    }

    if action and action.lower() in INVALID_ACTIONS:
        action = None

    # ─────────────────────────────────────────────
    # 🔥 4. ENRICHIR + ANTI-REPEAT
    # ─────────────────────────────────────────────
    if action:
        words = action.split()

        # Cas : verbe seul
        if len(words) == 1:
            verb = words[0]

            # éviter : "exit exit"
            if verb == obj_lower:
                return verb

            return f"{verb} {obj_lower}"

        return action

    # ─────────────────────────────────────────────
    # 🔥 5. FALLBACKS INTELLIGENTS
    # ─────────────────────────────────────────────

    # CAS APPLICATION
    if "application" in item_lower:
        if "desktop" in item_lower:
            return f"manage {obj_lower}"
        return f"use {obj_lower}"

    # CAS FILE
    if "file" in item_lower:
        return f"open {obj_lower}"

    # CAS COMMAND
    if "command" in item_lower:
        return f"run {obj_lower}"

    # ─────────────────────────────────────────────
    # 🔥 6. ULTIME FALLBACK
    # ─────────────────────────────────────────────
    return obj_lower


# ─────────────────────────────────────────────────────────────
# 4. INFÉRENCE
# ─────────────────────────────────────────────────────────────
def predict(model, tokenizer, device, items):
    if not items:
        return "(cluster vide — pas de prediction)"

    prompt = format_prompt(items)
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=MAX_INPUT_LENGTH,
        truncation=True,
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(**inputs, **INFERENCE_CONFIG)

    return tokenizer.decode(outputs[0], skip_special_tokens=True)


# ─────────────────────────────────────────────────────────────
# 5. ÉCRITURE DES SORTIES
# ─────────────────────────────────────────────────────────────
SEP  = "=" * 65
DASH = "─" * 65


def write_txt(results, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{SEP}\n")
        f.write("  CLUSTERS — GLOBAL TASK INTENTIONS\n")
        f.write(f"{SEP}\n\n")

        for c in results:
            f.write(f"{DASH}\n")
            label = (
                f"{c['cluster_id']}  |  singleton"
                if c.get("is_singleton") else
                f"{c['cluster_id']}  |  {c['num_tasks']} tache(s)  |  cohesion = {c['cohesion']:.3f}"
            )
            f.write(f"{label}\n")
            f.write(f"{DASH}\n")
            f.write(f"  Global Task Intention : {c['intention']}\n\n")
            f.write("  Items :\n")
            for item in c["items"]:
                f.write(f"    - {item}\n")
            f.write("\n")

        f.write(f"{SEP}\n")
        f.write("  FIN DU RAPPORT\n")
        f.write(f"{SEP}\n")


def write_jsonl(results, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        for i, c in enumerate(results):
            record = {
                "id":                    str(i),
                "cluster_id":            c["cluster_id"],
                "num_tasks":             c["num_tasks"],
                "cohesion":              c["cohesion"],
                "task_items":            c["items"],
                "global_task_intention": c["intention"],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ─────────────────────────────────────────────────────────────
# 6. MAIN
# ─────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Genere une global task intention pour chaque cluster."
    )
    parser.add_argument(
        "--input",     default=DEFAULT_INPUT,
        help=f"Fichier de clusters en entree (defaut : {DEFAULT_INPUT})"
    )
    parser.add_argument(
        "--model",     default=DEFAULT_MODEL,
        help=f"Chemin vers le modele Flan-T5 fine-tune (defaut : {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--out-txt",   default=DEFAULT_OUT_TXT,
        help=f"Fichier texte de sortie (defaut : {DEFAULT_OUT_TXT})"
    )
    parser.add_argument(
        "--out-jsonl", default=DEFAULT_OUT_JSONL,
        help=f"Fichier JSONL de sortie (defaut : {DEFAULT_OUT_JSONL})"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"\n{'='*65}")
    print("  CLUSTER GLOBAL TASK INTENTION PREDICTOR")
    print(f"{'='*65}\n")

    # ── 1. Parse ──────────────────────────────────────────────
    print(f"Lecture : {args.input}")
    if not Path(args.input).exists():
        sys.exit(
            f"\n[ERREUR] Fichier introuvable : {args.input}\n"
            "  Verifie DEFAULT_INPUT ou utilise --input <chemin>\n"
        )

    clusters = parse_clusters(args.input)
    if not clusters:
        sys.exit(
            "\n[ERREUR] Aucun cluster trouve.\n"
            "  Verifie que le format du fichier correspond au rapport de clustering.\n"
        )
    print(f"  {len(clusters)} clusters trouves\n")

    # ── 2. Modèle ─────────────────────────────────────────────
    print("Chargement du modele...")
    model, tokenizer, device = load_model(args.model)

    # ── 3. Inférence ──────────────────────────────────────────
    print(f"Inference ({len(clusters)} clusters)...\n")
    print(f"{'─'*65}")

    results = []
    for i, cluster in enumerate(clusters):

        # ── CAS 1 : singleton → PAS DE MODELE ───────────────
        if cluster.get("is_singleton"):
            item = cluster["items"][0]
            intention = generate_simple_intention(item)

        # ── CAS 2 : cluster normal → MODELE ────────────────
        else:
            intention = predict(model, tokenizer, device, cluster["items"])

        cluster["intention"] = intention
        results.append(cluster)

        print(f"[{i+1:02d}/{len(clusters)}] {cluster['cluster_id']}")
        print(f"         {len(cluster['items'])} item(s) | cohesion = {cluster['cohesion']:.3f}")
        print(f"         -> {intention}\n")

    print(f"{'─'*65}\n")

    # ── 4. Écriture ───────────────────────────────────────────
    write_txt(results,   args.out_txt)
    write_jsonl(results, args.out_jsonl)

    print(f"Sorties generees :")
    print(f"  {args.out_txt}")
    print(f"  {args.out_jsonl}")
    print(f"\n{'='*65}\n")


if __name__ == "__main__":
    main()
```

- `clusters_with_intentions.txt`:
```txt
=================================================================
  CLUSTERS — GLOBAL TASK INTENTIONS
=================================================================

─────────────────────────────────────────────────────────────────
Cluster 0  |  10 tache(s)  |  cohesion = 0.335
─────────────────────────────────────────────────────────────────
  Global Task Intention : Create and process staged changes to the local repository

  Items :
    - git commit -m, command, executed in terminal, used to commits staged changes to the local repository with a message
    - git commit -m reorganize file and directories, command, executed in terminal, used to commits staged changes to the local repository with a message
    - git commit -m moved collect_file_script, command, executed in terminal, used to commits staged changes to the local repository with a message
    - git commit -m parse_data, command, executed in terminal, used to commits staged changes to the local repository with a message
    - git commit -m arrange collect file script, command, executed in terminal, used to commits staged changes to the local repository with a message
    - code ., command, executed in terminal, used to start visual studio code
    - git commit -m correct directory to parse and describe-events, command, executed in terminal, used to commits staged changes to the local repository with a message
    - git status, command, executed in terminal, used to view the status of the local repository
    - git commit -m move brouillon to labs, command, executed in terminal, used to commits staged changes to the local repository with a message
    - git commit -m removed predict_ch et predict_ge, command, executed in terminal, used to commits staged changes to the local repository with a message

─────────────────────────────────────────────────────────────────
Cluster 1  |  2 tache(s)  |  cohesion = 0.316
─────────────────────────────────────────────────────────────────
  Global Task Intention : Clear screen on computer

  Items :
    - clear, command, executed in terminal
    - clear, command, executed in terminal, used to clear the screen

─────────────────────────────────────────────────────────────────
Cluster 2  |  5 tache(s)  |  cohesion = 0.236
─────────────────────────────────────────────────────────────────
  Global Task Intention : Use collect data

  Items :
    - ls collect_info/collect_file/, command, executed in terminal, used to list directory contents in collect_info/collect_file/
    - ls collect_info/collect_file/collect_file_script/, command, executed in terminal, used to list directory contents in collect_info/collect_file/collect_file_script/
    - get_collect_file.py, file, opened with visual studio code, contains data related to python 3 script, text files, data related to get collecting files.
    - python3 collect_data_command_script.py, command, executed in terminal, used to runs a python script using the python 3 interpreter with the collect_data_command_script.py file which is a python 3 script, text files, it serves as a collect data command script.
    - ls collect_info/, command, executed in terminal, used to list directory contents in collect_info/

─────────────────────────────────────────────────────────────────
Cluster 3  |  6 tache(s)  |  cohesion = 0.321
─────────────────────────────────────────────────────────────────
  Global Task Intention : Create and process clusters

  Items :
    - git commit -m correct path in cluster.py, command, executed in terminal, used to commits staged changes to the local repository with a message with the cluster.py file which is a python 3 script, text files, it contains data related to a cluster.
    - git commit -m correct path in predict_clusters_intention.py, command, executed in terminal, used to commits staged changes to the local repository with a message with the predict_clusters_intention.py file which is a python 3 script, text files, it serves as a predict clustersintention.
    - python3 taskmonitor/data/clustering/cluster.py, command, executed in terminal, used to runs a python script using the python 3 interpreter with the taskmonitor/data/clustering/cluster.py file which is a python 3 script, text files, it contains data related to a cluster.
    - python3 taskmonitor/data/describe_clusters/predict_clusters_intention.py, command, executed in terminal, used to runs a python script using the python 3 interpreter with the taskmonitor/data/describe_clusters/predict_clusters_intention.py file which is a python 3 script, text files, it serves as a predict clustersintention.
    - git commit -m describe_clusters, command, executed in terminal, used to commits staged changes to the local repository with a message
    - python3 predict_clusters_intention.py, command, executed in terminal, used to runs a python script using the python 3 interpreter with the predict_clusters_intention.py file which is a python 3 script, text files, it serves as a predict clustersintention.

─────────────────────────────────────────────────────────────────
Cluster 4  |  2 tache(s)  |  cohesion = 0.236
─────────────────────────────────────────────────────────────────
  Global Task Intention : Create files and directories

  Items :
    - git add ., command, executed in terminal, used to stage all changes in the current directory for the next commit
    - ls, command, executed in terminal, used to list directory contents

─────────────────────────────────────────────────────────────────
Cluster 5  |  8 tache(s)  |  cohesion = 0.356
─────────────────────────────────────────────────────────────────
  Global Task Intention : Manage data in taskmonitor

  Items :
    - ls taskmonitor/data/data_collect/, command, executed in terminal, used to list directory contents in taskmonitor/data/data_collect/
    - cd taskmonitor/, command, executed in terminal, used to go to the specified directory in taskmonitor/
    - ls taskmonitor/data/parse_data/, command, executed in terminal, used to list directory contents in taskmonitor/data/parse_data/
    - python3 taskmonitor/data/data_collect/, command, executed in terminal, used to runs a python script using the python 3 interpreter in taskmonitor/data/data_collect/
    - ls taskmonitor/data/dict/, command, executed in terminal, used to list directory contents in taskmonitor/data/dict/
    - ls taskmonitor/data/, command, executed in terminal, used to list directory contents in taskmonitor/data/
    - python3 taskmonitor/data/parse_data/parse.py, command, executed in terminal, used to runs a python script using the python 3 interpreter with the taskmonitor/data/parse_data/parse.py file which is a python 3 script, text files, it serves as a parse.
    - git commit -m reorganized taskmonitor, command, executed in terminal, used to commits staged changes to the local repository with a message

─────────────────────────────────────────────────────────────────
Cluster 6  |  2 tache(s)  |  cohesion = 0.438
─────────────────────────────────────────────────────────────────
  Global Task Intention : Active an environment

  Items :
    - conda activate mlproject_py311, command, executed in terminal, used to activate an environment
    - conda env list, command, executed in terminal

─────────────────────────────────────────────────────────────────
Autres petites tâches — singleton 1  |  singleton
─────────────────────────────────────────────────────────────────
  Global Task Intention : print the contents

  Items :
    - cat ~/.bash_history, command, executed in terminal, used to print the contents of a file to `stdout` targeting the special file ~/.bash_history which is user shell command history

─────────────────────────────────────────────────────────────────
Autres petites tâches — singleton 2  |  singleton
─────────────────────────────────────────────────────────────────
  Global Task Intention : run a python script using the python 3 interpreter

  Items :
    - python3 taskmonitor/data/describe_events/describe-event2.py, command, executed in terminal, used to runs a python script using the python 3 interpreter with the taskmonitor/data/describe_events/describe-event2.py file which is a python 3 script, text files, a description of events or events.

─────────────────────────────────────────────────────────────────
Autres petites tâches — singleton 3  |  singleton
─────────────────────────────────────────────────────────────────
  Global Task Intention : use chatgpt

  Items :
    - google chrome, application, used to use chatgpt

=================================================================
  FIN DU RAPPORT
=================================================================

```
Et voila, il faut desormais automatiser tout cela pour construire un vrai logiciel et faire l'interface graphique