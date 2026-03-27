import pandas as pd
import re

INPUT  = "data_collect.txt"
OUTPUT = "events_normalized2.csv"

# ─────────────────────────────────────────────
# Constantes pour la détection de type
# ─────────────────────────────────────────────

file_regex = re.compile(r"\.[a-zA-Z0-9]+$")

# Répertoires connus de l'environnement
KNOWN_DIRS = {
    "Desktop", "Music", "Public", "Documents", "Videos",
    "Downloads", "Pictures", "Templates",
    # racine filesystem Linux
    "bin", "etc", "lib", "lib32", "lib64", "libx32", "opt", "sbin",
    "tmp", "usr", "var", "home", "root", "boot", "dev", "proc",
    "run", "srv", "sys", "mnt", "media", "snap", "cdrom",
    "lost+found",
}

# Mot simple sans extension, ne commence pas par majuscule,
# peut contenir _ ou -, ou commence par /
dir_regex = re.compile(r"^(/|[a-z][a-zA-Z0-9_\-]*$)")


def detect_file(name: str) -> bool:
    return bool(file_regex.search(name))


def detect_directory(name: str) -> bool:
    """
    Retourne True si le nom est un répertoire :
      - présent dans KNOWN_DIRS
      - commence par '/' (chemin absolu)
      - mot simple en minuscule (avec _ ou -), sans extension
    """
    if name in KNOWN_DIRS:
        return True
    if name.startswith("/"):
        return True
    # mot simple : minuscule, pas d'extension, peut avoir _ ou -
    if re.match(r"^[a-z][a-z0-9_\-]*$", name):
        return True
    return False


def parse_event(raw: str) -> tuple[str, str, str, str, str]:
    """
    Retourne (event_type, file, directory, app, command)
    event_type : "file" | "directory" | "app"
    """
    parts = raw.split(" - ")

    if len(parts) >= 2:
        filename = parts[0].strip()
        app      = parts[-1].strip()

        if detect_file(filename):
            return "file", filename, "", app, ""
        elif detect_directory(filename):
            return "directory", "", filename, app, ""
        else:
            return "app", "", "", app, ""

    else:
        name = raw.strip()
        if detect_file(name):
            return "file", name, "", "", ""
        elif detect_directory(name):
            return "directory", "", name, "", ""
        return "app", "", "", name, ""


# ─────────────────────────────────────────────
# Lecture et construction des lignes
# ─────────────────────────────────────────────

rows = []

with open(INPUT) as f:
    for line in f:
        cols = line.strip().split("\t")

        if len(cols) < 6:
            continue

        date, start, end, duration, type_raw, raw_event = cols

        if type_raw == "Commande":
            rows.append({
                "date":       date,
                "start":      start,
                "end":        end,
                "duration":   float(duration),
                "event_type": "command",
                "file":       "",
                "directory":  "",
                "app":        "Terminal",
                "command":    raw_event,
                "raw":        raw_event,
            })

        else:
            event_type, file, directory, app, command = parse_event(raw_event)

            rows.append({
                "date":       date,
                "start":      start,
                "end":        end,
                "duration":   float(duration),
                "event_type": event_type,
                "file":       file,
                "directory":  directory,
                "app":        app,
                "command":    command,
                "raw":        raw_event,
            })

df = pd.DataFrame(rows)
df.to_csv(OUTPUT, index=False)
print("Saved:", OUTPUT)