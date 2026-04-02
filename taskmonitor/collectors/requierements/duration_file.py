#!/usr/bin/env python3
import sys
from datetime import datetime
from collections import defaultdict
from pathlib import Path

def normalize_title(title): 
    return title.lstrip('● ').strip()

def get_entry_type(title):
    if " - " in title:
        return "file-directory-App"
    return "directory/App"

if len(sys.argv) != 3:
    print("Usage: duration_file.py <collected_file.txt> <data_file.txt>")
    sys.exit(1)

input_file = Path(sys.argv[1])
output_file = Path(sys.argv[2])

durations = defaultdict(float)
last_info = {}

with input_file.open("r", encoding="utf-8") as f:
    for line in f:
        columns = line.strip().split()
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

# Créer dossier si absent
output_file.parent.mkdir(parents=True, exist_ok=True)

with output_file.open("w", encoding="utf-8") as f_out:
    for title, total_min in sorted(durations.items(), key=lambda x: x[1], reverse=True):
        date, start_time_str, end_time_str = last_info[title]
        entry_type = get_entry_type(title)
        f_out.write(f"{date} {start_time_str} {end_time_str} {total_min:.2f} {entry_type}   {title}\n")

print(f"Total durations (in minutes) recorded in {output_file}")