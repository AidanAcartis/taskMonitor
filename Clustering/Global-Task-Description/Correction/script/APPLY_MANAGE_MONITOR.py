import json
import csv
from collections import Counter

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
ORIGINAL_JSONL  = "activity_data_final_v2.jsonl"
SUGGESTIONS_CSV = "labels_manage_monitor_suggestions.csv"
OUTPUT_JSONL    = "activity_data_final_v3.jsonl"

# ─────────────────────────────────────────────
# CHARGEMENT DES SUGGESTIONS
# ─────────────────────────────────────────────
corrections = {}
with open(SUGGESTIONS_CSV, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["action"].strip().upper() == "EDIT" and row["label_suggere"].strip():
            corrections[str(row["id"])] = row["label_suggere"].strip()

print(f"Corrections chargées : {len(corrections)}")

# ─────────────────────────────────────────────
# APPLICATION
# ─────────────────────────────────────────────
with open(ORIGINAL_JSONL, "r", encoding="utf-8") as f:
    samples = [json.loads(l) for l in f if l.strip()]

modified = 0
for s in samples:
    sid = str(s["id"])
    if sid in corrections:
        s["global_task_intention"] = corrections[sid]
        modified += 1

# ─────────────────────────────────────────────
# SAUVEGARDE
# ─────────────────────────────────────────────
with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
    for s in samples:
        f.write(json.dumps(s) + "\n")

# ─────────────────────────────────────────────
# RAPPORT
# ─────────────────────────────────────────────
total = len(samples)
final_verbs = Counter(
    s["global_task_intention"].split()[0].lower()
    for s in samples
)

print(f"\n{'=' * 55}")
print(f"RAPPORT")
print(f"{'=' * 55}")
print(f"  Labels modifiés  : {modified}")
print(f"  Fichier de sortie: {OUTPUT_JSONL}")

print(f"\nTop 15 verbes après correction :")
print(f"  {'Verbe':<22} {'Count':>6} {'%':>6}  Barre")
print(f"  {'-'*50}")
for verb, count in final_verbs.most_common(15):
    pct = count / total * 100
    bar = "█" * int(pct)
    flag = " ⚠" if pct > 8 else ""
    print(f"  {verb:<22} {count:>6}  {pct:>5.1f}%  {bar}{flag}")

print(f"\n  Verbes uniques : {len(final_verbs)}")
print(f"  Top 3 cumul    : {sum(c for _,c in final_verbs.most_common(3))/total*100:.1f}%")

# Aperçu
print(f"\nAperçu 10 premières corrections :")
orig_index = {}
with open(ORIGINAL_JSONL) as f:
    for l in f:
        s = json.loads(l)
        orig_index[str(s["id"])] = s["global_task_intention"]

shown = 0
for s in samples:
    sid = str(s["id"])
    if sid in corrections:
        print(f"  [{sid}] {orig_index[sid]}")
        print(f"       → {s['global_task_intention']}")
        shown += 1
        if shown >= 10:
            break