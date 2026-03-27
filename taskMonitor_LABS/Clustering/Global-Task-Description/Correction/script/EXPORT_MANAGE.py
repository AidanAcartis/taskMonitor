import json
import csv
from collections import Counter

# ─────────────────────────────────────────────
# CHARGEMENT
# ─────────────────────────────────────────────
PATH = "activity_data_final.jsonl"

with open(PATH, "r", encoding="utf-8") as f:
    samples = [json.loads(l) for l in f if l.strip()]

print(f"Total exemples : {len(samples)}")

# ─────────────────────────────────────────────
# EXTRACTION DES LABELS "and manage"
# ─────────────────────────────────────────────
and_manage_samples = [
    s for s in samples
    if " and manage" in s["global_task_intention"].lower()
]

print(f"Labels 'and manage' trouvés : {len(and_manage_samples)}")

# ─────────────────────────────────────────────
# EXPORT CSV — une ligne par exemple
# colonnes : id | label_original | label_suggere | action
# ─────────────────────────────────────────────
OUTPUT_CSV = "labels_to_review.csv"

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id",
        "label_original",
        "label_suggere",   # à remplir manuellement
        "action",          # KEEP / EDIT / DELETE
        "nb_items",
    ])
    writer.writeheader()

    for s in and_manage_samples:
        writer.writerow({
            "id":             s["id"],
            "label_original": s["global_task_intention"],
            "label_suggere":  "",   # à compléter manuellement
            "action":         "KEEP",
            "nb_items":       len(s["task_items"]),
        })

print(f"Exporté : {OUTPUT_CSV}")

# ─────────────────────────────────────────────
# STATS — verbes avant "and manage"
# pour identifier les patterns les plus fréquents
# ─────────────────────────────────────────────
prefix_verbs = Counter()
for s in and_manage_samples:
    words = s["global_task_intention"].lower().split()
    if "and" in words:
        idx = words.index("and")
        if idx > 0:
            prefix_verbs[words[0]] += 1

print(f"\nVerbes avant 'and manage' les plus fréquents :")
print(f"{'Verbe':<20} {'Count':>6} {'%':>6}")
print("-" * 35)
total = len(and_manage_samples)
for verb, count in prefix_verbs.most_common(15):
    print(f"  {verb:<18} {count:>6}  {count/total*100:>5.1f}%")

# ─────────────────────────────────────────────
# EXPORT JSONL — uniquement les samples à revoir
# pour réinjecter facilement après correction
# ─────────────────────────────────────────────
OUTPUT_JSONL = "labels_to_review.jsonl"
with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
    for s in and_manage_samples:
        f.write(json.dumps(s) + "\n")

print(f"Exporté : {OUTPUT_JSONL}")
print(f"\nWorkflow suggéré :")
print(f"  1. Ouvrir {OUTPUT_CSV} dans un tableur")
print(f"  2. Pour chaque ligne, remplir 'label_suggere' et changer 'action' en EDIT")
print(f"  3. Relancer le script d'application ci-dessous pour patcher le dataset")