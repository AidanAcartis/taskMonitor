"""
utils.py
--------
Utility functions for:
- Loading data
- Task normalization
- Deduplication
- Controlled shuffling
- Saving the final report
"""

import pandas as pd
import random
from pathlib import Path


# ─────────────────────────────────────────────
# NORMALISATION
# ─────────────────────────────────────────────
def normalize_task(text: str) -> str:
    """
    Minimal task description cleaning.
    """
    return text.replace('\\"', '').replace('"', '').lower().strip()


# ─────────────────────────────────────────────
# LOAD + PREPARE (ÉTAPES 1 & 2)
# ─────────────────────────────────────────────
def load_and_prepare_tasks(csv_path: Path, config: dict) -> list[str]:
    """
    Complete pipeline:
    1. CSV loading
    2. Normalization
    3. Filtering (empty entries)
    4. Deduplication
    5. Reproducible shuffle
    """

    print("=" * 60)
    print("CLUSTERING - DATA PREPARATION")
    print("=" * 60)

    # ───────────────
    # Chargement
    # ───────────────
    print(f"\n[1] Loading {csv_path} ...")

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()

    if "description" not in df.columns:
        raise ValueError("Column 'description' not found in the CSV.")

    # ───────────────
    # Normalisation
    # ───────────────
    tasks_raw = df["description"].fillna("").astype(str).tolist()
    tasks_raw = [normalize_task(t) for t in tasks_raw if t]

    print(f"    {len(tasks_raw)} descriptions loaded.")

    # ───────────────
    # Déduplication
    # ───────────────
    seen = set()
    tasks_unique = [t for t in tasks_raw if not (t in seen or seen.add(t))]

    print(f"    {len(tasks_unique)} descriptions after deduplication.")

    # ───────────────
    # Shuffle
    # ───────────────
    print("\n[2] Shuffle (seed={}) ...".format(config["random_seed"]))

    random.seed(config["random_seed"])
    random.shuffle(tasks_unique)

    return tasks_unique


# ─────────────────────────────────────────────
# RAPPORT FINAL
# ─────────────────────────────────────────────
def save_report(groups: dict, tasks: list, dist, metrics: dict, output_path: Path):
    """
    Generates the final text report of the clusters.
    """

    print(f"\n[10] Writing report to {output_path} ...")

    def compute_cohesion(idxs):
        if len(idxs) < 2:
            return 0.0
        sub = dist[np.ix_(idxs, idxs)]
        return sub[np.triu_indices_from(sub, 1)].mean()

    import numpy as np

    lines = []
    lines.append("=" * 60)
    lines.append("TASK CLUSTERING REPORT")
    lines.append("=" * 60)

    lines.append(f"Total tasks          : {len(tasks)}")
    lines.append(f"Number of clusters      : {metrics['n_clusters']}")
    lines.append(f"Final silhouette       : {metrics['silhouette']:.3f}")
    lines.append(f"Final average cohesion         : {metrics['cohesion']:.3f}")
    lines.append("")

    # mapping rapide
    task_to_index = {t: i for i, t in enumerate(tasks)}

    for cid, items in groups.items():
        idxs = [task_to_index[t] for t in items]
        coh = compute_cohesion(idxs)

        lines.append("─" * 60)
        lines.append(f"Cluster {cid} | {len(items)} task(s) | cohesion = {coh:.3f}")
        lines.append("─" * 60)

        for t in items:
            lines.append(f"  • {t}")

        lines.append("")

    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n Report saved : {output_path}")