"""
CMD_Describe.py
---------------
Lit events_normalized.csv, décrit chaque commande shell via cmddesc,
et insère la description dans une nouvelle colonne juste après la commande.

Résultat écrit dans : events_normalized_described.csv
"""

import re
import csv
import subprocess
import sys
import os

# ─────────────────────────────────────────────
# CONFIGURATION — modifier ici si besoin
# ─────────────────────────────────────────────
INPUT_CSV      = "events_normalized.csv"
OUTPUT_CSV     = "events_normalized_described.csv"
COMMAND_COL    = "command" # nom de la colonne dans le CSV
DESC_COL_NAME  = "description"
DELIMITER      = ","
HAS_HEADER     = True

# Labels sans valeur sémantique réelle
NOISE_PREFIXES = (
    "Command '", "Argument '", "String '",
    "Number '", "IP address '", "URL '", "JSON '",
    "File '", "Folder '", "Server '",
)


# ─────────────────────────────────────────────
# STEP 1 — run cmddesc
# ─────────────────────────────────────────────
def run_cmddesc(command: str) -> str:
    result = subprocess.run(
        ["cmddesc"],
        input=command,
        capture_output=True,
        text=True
    )
    return result.stdout


# ─────────────────────────────────────────────
# STEP 2 — parse cmddesc output
# ─────────────────────────────────────────────
def parse_cmddesc_output(raw_output: str) -> str:
    """
    Construit la description finale à partir de la sortie de cmddesc.
    """

    def is_noise(value: str) -> bool:
        return any(value.startswith(p) for p in NOISE_PREFIXES)

    def extract_value(line: str) -> str:
        return re.sub(r"^(desc_\w+|with sudo privilege):\s*", "", line.strip()).strip()

    sub_commands = []
    current      = []
    mode         = None

    for line in raw_output.splitlines():
        s = line.strip()

        if re.match(r"^=== Command \d+", s):
            if current:
                sub_commands.append(" + ".join(current))
            current = []
            mode    = None

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

    return " | ".join(sub_commands) if sub_commands else "No description found"


def describe_command(command: str) -> str:
    """Wrapper: run cmddesc + parse, handle empty/error gracefully."""
    command = command.strip()
    if not command:
        return ""
    try:
        raw_output = run_cmddesc(command)
        return parse_cmddesc_output(raw_output)
    except Exception as e:
        return f"[ERROR: {e}]"


# ─────────────────────────────────────────────
# STEP 3 — CSV mode
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if not os.path.isfile(INPUT_CSV):
    print(f"[ERREUR] Fichier introuvable : {INPUT_CSV}")
    sys.exit(1)

# --- Lecture ---
with open(INPUT_CSV, newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f, delimiter=DELIMITER))

if not rows:
    print("[ERREUR] Le fichier CSV est vide.")
    sys.exit(1)

header    = rows[0] if HAS_HEADER else None
data_rows = rows[1:] if HAS_HEADER else rows

# Résolution de la colonne commande par nom
if not header or COMMAND_COL not in header:
    print(f"[ERREUR] Colonne '{COMMAND_COL}' introuvable dans le CSV. Colonnes disponibles : {header}")
    sys.exit(1)
command_col = header.index(COMMAND_COL)
insert_pos  = command_col + 1   # description insérée juste après

print(f"[INFO] Colonne commande : index {command_col}  |  entrée : {INPUT_CSV}  |  sortie : {OUTPUT_CSV}")

# --- Nouvel en-tête ---
new_header = None
if HAS_HEADER and header:
    new_header = header[:insert_pos] + [DESC_COL_NAME] + header[insert_pos:]

# --- Traitement ---
new_rows = []
total    = len(data_rows)

for i, row in enumerate(data_rows, 1):
    if command_col >= len(row):
        desc = ""
    else:
        cmd  = row[command_col].strip()
        desc = describe_command(cmd)
        print(f"[{i}/{total}] {cmd!r:50s} → {desc}")

    new_row = row[:insert_pos] + [desc] + row[insert_pos:]
    new_rows.append(new_row)

# --- Écriture ---
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=DELIMITER)
    if new_header:
        writer.writerow(new_header)
    writer.writerows(new_rows)

print(f"\n✅ Fichier enrichi écrit dans : {OUTPUT_CSV}")
print(f"   {total} ligne(s) traitée(s), colonne '{DESC_COL_NAME}' ajoutée.")