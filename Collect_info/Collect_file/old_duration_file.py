from datetime import datetime
from collections import defaultdict

input_file = "collected_file.txt"
output_file = "data_file.txt"

# Dictionnaire pour stocker les durées cumulées par titre
durations = defaultdict(float)

def normalize_title(title):
    # Enlève le "● " devant le nom si présent
    return title.lstrip('● ').strip()

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

# # Écriture des résultats dans un fichier (une seule fois)
with open(output_file, "w", encoding="utf-8") as f_out:
    # for title, total_min in durations.items():
    #     f_out.write(f"{total_min:.2f} {title}\n")
    for title, total_min in sorted(durations.items(), key=lambda x: x[1], reverse=True):
        f_out.write(f"{date} {start_time_str} {end_time_str} {total_min:.2f} {"file-directory-App"}   {title}\n")



print(f"Durées totales (en minutes) enregistrées dans {output_file}")


