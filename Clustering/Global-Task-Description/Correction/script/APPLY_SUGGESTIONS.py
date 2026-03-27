import json
import csv

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
ORIGINAL_JSONL   = "activity_data_final.jsonl"
SUGGESTIONS_CSV  = "labels_with_suggestions.csv"
OUTPUT_JSONL     = "activity_data_final_v2.jsonl"

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
from collections import Counter
final_verbs = Counter(
    s["global_task_intention"].split()[0].lower()
    for s in samples
)
remaining_and_manage = sum(
    1 for s in samples
    if " and manage" in s["global_task_intention"].lower()
)

print(f"\n{'=' * 50}")
print(f"RAPPORT")
print(f"{'=' * 50}")
print(f"  Labels modifiés          : {modified}")
print(f"  'and manage' restants    : {remaining_and_manage} (était 305)")
print(f"  Fichier de sortie        : {OUTPUT_JSONL}")
print(f"\nTop 10 verbes après correction :")
print(f"  {'Verbe':<22} {'Count':>6} {'%':>6}")
print(f"  {'-'*35}")
total = len(samples)
for verb, count in final_verbs.most_common(10):
    pct = count / total * 100
    bar = "█" * int(pct)
    print(f"  {verb:<22} {count:>6}  {pct:>5.1f}%  {bar}")

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