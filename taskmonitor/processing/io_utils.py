#!/usr/bin/env python3
"""
Fonctions utilitaires d'entrée/sortie pour le prédicteur d'intentions.
"""

import json
from pathlib import Path

def load_json(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier JSON introuvable : {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def write_txt(results, filepath):
    SEP  = "=" * 65
    DASH = "─" * 65
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{SEP}\n")
        f.write("  CLUSTERS — GLOBAL TASK INTENTIONS\n")
        f.write(f"{SEP}\n\n")

        for c in results:
            f.write(f"{DASH}\n")
            label = (
                f"{c['cluster_id']}  |  singleton"
                if c.get("is_singleton") else
                f"{c['cluster_id']}  |  {c['num_tasks']} tache(s)  |  cohesion = {c['cohesion']:.3f}"
            )
            f.write(f"{label}\n")
            f.write(f"{DASH}\n")
            f.write(f"  Global Task Intention : {c['intention']}\n\n")
            f.write("  Items :\n")
            for item in c["items"]:
                f.write(f"    - {item}\n")
            f.write("\n")

        f.write(f"{SEP}\n")
        f.write("  FIN DU RAPPORT\n")
        f.write(f"{SEP}\n")

def write_jsonl(results, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        for i, c in enumerate(results):
            record = {
                "id":                    str(i),
                "cluster_id":            c["cluster_id"],
                "num_tasks":             c["num_tasks"],
                "cohesion":              c["cohesion"],
                "task_items":            c["items"],
                "global_task_intention": c["intention"],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")