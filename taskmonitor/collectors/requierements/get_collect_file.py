#!/usr/bin/env python3
import sys
from pathlib import Path

def parse_line(line):
    parts = line.strip().split(" ", 2)

    # ❌ Ligne invalide (vide ou incomplète)
    if len(parts) < 3:
        return None

    date = parts[0]
    time = parts[1]
    filename = parts[2].strip()

    # ❌ Nom vide (cas réel dans tes logs)
    if filename == "":
        return None

    return date, time, filename

# Récupérer les fichiers depuis les arguments
if len(sys.argv) != 4:
    print("Usage: get_collect_file.py <Opened_file.txt> <Closed_file.txt> <collected_file.txt>")
    sys.exit(1)

opened_file_path = Path(sys.argv[1])
closed_file_path = Path(sys.argv[2])
collected_file_path = Path(sys.argv[3])

# Lire les fichiers
with opened_file_path.open("r", encoding="utf-8") as f_open:
    opened_lines = f_open.readlines()

with closed_file_path.open("r", encoding="utf-8") as f_close:
    closed_lines = f_close.readlines()

true_file_lines = []
used_close_indices = set()

for i, open_line in enumerate(opened_lines):
    parsed_open = parse_line(open_line)

    # ❌ ignorer lignes invalides
    if parsed_open is None:
        continue

    open_date, open_time, filename = parsed_open

    for j in range(i, len(closed_lines)):
        if j in used_close_indices:
            continue

        parsed_close = parse_line(closed_lines[j])

        # ❌ ignorer lignes invalides
        if parsed_close is None:
            continue

        close_date, close_time, close_filename = parsed_close

        if close_filename == filename:
            used_close_indices.add(j)
            true_file_lines.append(
                f"{open_date} {open_time} {close_time} {filename}\n"
            )
            break

# Créer dossier si absent
collected_file_path.parent.mkdir(parents=True, exist_ok=True)

with collected_file_path.open("w", encoding="utf-8") as f_true:
    f_true.writelines(true_file_lines)

print(f"Fichier '{collected_file_path}' généré avec succès.")