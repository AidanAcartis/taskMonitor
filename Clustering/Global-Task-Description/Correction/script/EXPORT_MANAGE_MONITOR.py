import json
import csv
from collections import Counter

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
INPUT_JSONL = "activity_data_final_v2.jsonl"

# ─────────────────────────────────────────────
# CHARGEMENT
# ─────────────────────────────────────────────
with open(INPUT_JSONL, "r", encoding="utf-8") as f:
    samples = [json.loads(l) for l in f if l.strip()]

total = len(samples)
print(f"Dataset chargé : {total} exemples")

# ─────────────────────────────────────────────
# CALCUL DES BUDGETS
# cible : ramener manage et monitor sous 8%
# ─────────────────────────────────────────────
first_verbs = Counter(
    s["global_task_intention"].split()[0].lower()
    for s in samples
)

TARGET_MAX_PCT = 0.08
manage_count   = first_verbs["manage"]
monitor_count  = first_verbs["monitor"]
manage_target  = int(total * TARGET_MAX_PCT)
monitor_target = int(total * TARGET_MAX_PCT)
manage_to_fix  = max(0, manage_count  - manage_target)
monitor_to_fix = max(0, monitor_count - monitor_target)

print(f"\n  manage  : {manage_count} ({manage_count/total*100:.1f}%) → cible {manage_target} → à corriger : {manage_to_fix}")
print(f"  monitor : {monitor_count} ({monitor_count/total*100:.1f}%) → cible {monitor_target} → à corriger : {monitor_to_fix}")

# ─────────────────────────────────────────────
# EXTRACTION — prendre exactement N labels
# pour chaque verbe (les premiers dans le dataset)
# ─────────────────────────────────────────────
manage_samples  = [s for s in samples if s["global_task_intention"].split()[0].lower() == "manage"]
monitor_samples = [s for s in samples if s["global_task_intention"].split()[0].lower() == "monitor"]

to_export = manage_samples[:manage_to_fix] + monitor_samples[:monitor_to_fix]

print(f"\n  Exportés manage  : {len(manage_samples[:manage_to_fix])}")
print(f"  Exportés monitor : {len(monitor_samples[:monitor_to_fix])}")
print(f"  Total à corriger : {len(to_export)}")

# ─────────────────────────────────────────────
# EXPORT CSV
# ─────────────────────────────────────────────
OUTPUT_CSV = "labels_manage_monitor.csv"

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "verb", "label_original", "label_suggere", "action", "nb_items"
    ])
    writer.writeheader()
    for s in to_export:
        writer.writerow({
            "id":             s["id"],
            "verb":           s["global_task_intention"].split()[0].lower(),
            "label_original": s["global_task_intention"],
            "label_suggere":  "",
            "action":         "KEEP",
            "nb_items":       len(s["task_items"]),
        })

print(f"\nExporté : {OUTPUT_CSV}")