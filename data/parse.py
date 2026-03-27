import pandas as pd
import re

INPUT = "data_collect.txt"
OUTPUT = "events_normalized.csv"

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