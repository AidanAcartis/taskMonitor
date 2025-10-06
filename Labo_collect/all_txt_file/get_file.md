Pour réaliser cela, tu peux utiliser un script Python simple. Voici une solution complète respectant ta logique :

### Script Python (`merge_open_close_files.py`)
```python
def parse_line(line):
    parts = line.strip().split(" ", 1)
    time = parts[0]
    filename = parts[1]
    return time, filename

# Lire les deux fichiers
with open("Opened_files_true.txt", "r", encoding="utf-8") as f_open:
    opened_lines = f_open.readlines()

with open("Closed_files_true.txt", "r", encoding="utf-8") as f_close:
    closed_lines = f_close.readlines()

# Initialiser la liste pour les résultats
true_file_lines = []
used_close_indices = set()  # Pour éviter les doublons de fermeture

# Boucle sur chaque ligne d'ouverture
for i, open_line in enumerate(opened_lines):
    open_time, filename = parse_line(open_line)

    # Rechercher la fermeture correspondante à partir de la ligne i
    for j in range(i, len(closed_lines)):
        if j in used_close_indices:
            continue
        close_time, close_filename = parse_line(closed_lines[j])
        if close_filename == filename:
            used_close_indices.add(j)
            true_file_lines.append(f"{open_time} {close_time} {filename}\n")
            break

# Écriture dans le fichier de sortie
with open("true_file.txt", "w", encoding="utf-8") as f_true:
    f_true.writelines(true_file_lines)

print("Fichier 'true_file.txt' généré avec succès.")
```

### Exemple de sortie dans `true_file.txt`
```
21:28:17 21:28:19 THE_COMMAND.txt
21:28:19 21:28:21 Preview how_to_run.md
21:28:21 21:28:32 corrected_try_script.sh
21:28:32 21:28:17 window_changes.log
21:29:51 21:33:32 「 Nightcore 」→ Twinkle Star (Feat. Shiori)『 花澤 香菜 __ Kana Hanazawa 』.mp4
21:33:32 21:38:10 『Oh! My☆God!!』.mp4
```

Souhaites-tu une version du script en **C++** ou en **bash** à la place ?