
def parse_line(line):
    parts = line.strip().split(" ", 2)
    date = parts[0]
    time = parts[1]
    filename = parts[2]
    return date, time, filename

# Lire les deux fichiers
with open("Opened_file.txt", "r", encoding="utf-8") as f_open:
    opened_lines = f_open.readlines()

with open("Closed_file.txt", "r", encoding="utf-8") as f_close:
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