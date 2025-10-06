from datetime import datetime
from collections import defaultdict

file = "collected_file.txt"
output_file = "file_duration2.txt"

# dictionnaire pour stocker les durées totales par titre
durations = defaultdict(float)

with open(file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) < 3:
            continue

        start_str, end_str = parts[0], parts[1]
        title = " ".join(parts[2:])

        # Normaliser le nom du fichier en retirant le "● " s'il y en a
        if title.startswith("● "):
            title = title[2:]

        # parser les heures
        try:
            time_format = "%H:%M:%S"
            start_time = datetime.strptime(start_str, time_format)
            end_time = datetime.strptime(end_str, time_format)
            duration_min = (end_time - start_time).total_seconds() / 60
            if duration_min > 0:
                durations[title] += duration_min
        except Exception as e:
            # ignorer les lignes mal formées
            continue

# écrire dans le fichier de sortie
with open(output_file, "w", encoding="utf-8") as f_out:
    for title, total_duration in sorted(durations.items(), key=lambda x: -x[1]):
        f_out.write(f"{total_duration:.2f}    {title}\n")
