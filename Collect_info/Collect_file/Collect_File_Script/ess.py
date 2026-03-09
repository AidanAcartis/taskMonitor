from datetime import datetime, timedelta
from collections import defaultdict
import re

# Fichier à lire
filename = "collected_file.txt"

# Dictionnaire pour stocker la durée cumulée de chaque fichier
durations = defaultdict(timedelta)

# Expression régulière pour extraire les données
pattern = re.compile(r"(\d{2}:\d{2}:\d{2})\s+(\d{2}:\d{2}:\d{2})\s+[\u25CF]*\s*(.+)")

with open(filename, "r", encoding="utf-8") as file:
    for line in file:
        match = pattern.match(line.strip())
        if match:
            start_str, end_str, title = match.groups()
            try:
                start = datetime.strptime(start_str, "%H:%M:%S")
                end = datetime.strptime(end_str, "%H:%M:%S")
                if end < start:
                    end += timedelta(days=1)
                duration = end - start
                normalized_title = title.replace("●", "").strip()
                durations[normalized_title] += duration
            except Exception as e:
                print(f"Erreur sur la ligne: {line.strip()} -- {e}")

# Affichage du résultat
print(f"{'Fichier':40} | Durée totale (minutes)")
print("-" * 60)
for title, duration in sorted(durations.items(), key=lambda x: -x[1]):
    minutes = round(duration.total_seconds() / 60, 2)
    print(f"{title:40} | {minutes}")
