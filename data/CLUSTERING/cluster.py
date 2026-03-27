"""
cluster_tasks.py
----------------
Lit events_described.csv, regroupe les descriptions en clusters
de tâches globales via le modèle fine-tuné (all-MiniLM-L6-v2).

Suit exactement les étapes d'inférence du notebook :
  1.  Chargement + normalisation
  2.  Shuffle (seed=42)
  3.  Embeddings (normalize=True)
  4.  Matrice de distance cosinus
  5.  Clustering initial → meilleur threshold par silhouette
  6.  Cohésion par cluster
  7.  Reclustering itératif (recluster_subset)
  8.  Extraction des singletons
  9.  Reclustering global des singletons (si ratio >= 20%)
  10. Fusion finale
  11. Reclustering final par cohésion (best_split_by_k)
  12. Métriques finales (silhouette + cohésion)
  13. Sauvegarde du rapport texte → clusters_output.txt
"""

import random
import numpy as np
import pandas as pd
import os

from collections import defaultdict
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sentence_transformers import SentenceTransformer, util

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
CSV_INPUT          = os.path.join(BASE_DIR, "../DESCRIBE_EVENTS/events_described.csv")
OUTPUT_FILE        = os.path.join(BASE_DIR, "clusters_output.txt")
MODEL_DIR          = os.path.join(BASE_DIR, "../../../Vis_Models/final_model")
COHESION_THRESHOLD = 0.34    # seuil cohésion reclustering itératif (étape 7)
SIZE_THRESHOLD     = 10      # taille max avant reclustering forcé   (étape 7)
COHESION_FINAL     = 0.55    # seuil reclustering final              (étape 11)
COHESION_SPLIT_MAX = 0.45    # seuil acceptation d'un split
SINGLETON_RATIO    = 0.10    # ratio min singletons pour reclustering global
THRESHOLDS         = np.arange(0.45, 0.85, 0.01)
RANDOM_SEED        = 42


# ─────────────────────────────────────────────
# ÉTAPE 1 — Chargement + normalisation
# ─────────────────────────────────────────────
def normalize_task(text: str) -> str:
    text = text.replace('\\"', '').replace('"', '')
    return text.lower().strip()


print("=" * 60)
print("cluster_tasks.py")
print("=" * 60)

print(f"\n[1] Chargement de {CSV_INPUT} ...")
df = pd.read_csv(CSV_INPUT)
df.columns = df.columns.str.strip().str.lower()

if "description" not in df.columns:
    raise ValueError("Colonne 'description' introuvable dans le CSV.")

df["description"] = df["description"].fillna("").astype(str)
tasks_raw = [normalize_task(t) for t in df["description"].tolist()]
tasks_raw = [t for t in tasks_raw if t]
print(f"    {len(tasks_raw)} descriptions chargées.")

# Déduplication — on garde uniquement les descriptions uniques
seen      = set()
tasks_raw = [t for t in tasks_raw if not (t in seen or seen.add(t))]
print(f"    {len(tasks_raw)} descriptions après déduplication.")


# ─────────────────────────────────────────────
# ÉTAPE 2 — Shuffle (seed=42)
# ─────────────────────────────────────────────
print("\n[2] Shuffle (seed=42) ...")
tasks = tasks_raw[:]
random.seed(RANDOM_SEED)
random.shuffle(tasks)


# ─────────────────────────────────────────────
# ÉTAPE 3 — Embeddings
# ─────────────────────────────────────────────
print(f"\n[3] Chargement du modèle : {MODEL_DIR} ...")
model = SentenceTransformer(MODEL_DIR)
model.eval()

print("    Calcul des embeddings ...")
embeddings = model.encode(
    tasks,
    convert_to_tensor=True,
    normalize_embeddings=True
)


# ─────────────────────────────────────────────
# ÉTAPE 4 — Matrice de distance
# ─────────────────────────────────────────────
print("\n[4] Calcul de la matrice de distance ...")
sim  = util.cos_sim(embeddings, embeddings).cpu().numpy()
dist = 1 - sim
dist = np.clip(dist, 0, None)


# ─────────────────────────────────────────────
# ÉTAPE 5 — Clustering initial
# ─────────────────────────────────────────────
print("\n[5] Clustering initial (recherche meilleur threshold) ...")

def cluster_cohesion_map(dist, labels):
    clusters = defaultdict(list)
    for i, c in enumerate(labels):
        clusters[c].append(i)
    cohesions = {}
    for c, idxs in clusters.items():
        if len(idxs) < 2:
            cohesions[c] = 0.0
            continue
        sub = dist[np.ix_(idxs, idxs)]
        cohesions[c] = sub.mean()
    return cohesions

best = {"th": None, "silhouette": -1, "labels": None, "cohesion": None}

for th in THRESHOLDS:
    clustering = AgglomerativeClustering(
        n_clusters=None,
        metric="precomputed",
        linkage="average",
        distance_threshold=th
    )
    labels     = clustering.fit_predict(dist)
    n_clusters = len(set(labels))

    if n_clusters <= 1 or n_clusters > len(tasks) // 2:
        continue

    sil      = silhouette_score(dist, labels, metric="precomputed")
    cohesion = cluster_cohesion_map(dist, labels)

    if sil > best["silhouette"]:
        best.update({"th": th, "silhouette": sil,
                     "labels": labels, "cohesion": cohesion})

print(f"    Meilleur threshold : {best['th']:.2f} | silhouette : {best['silhouette']:.3f}")

groups = defaultdict(list)
for task, lbl in zip(tasks, best["labels"]):
    groups[lbl].append(task)


# ─────────────────────────────────────────────
# ÉTAPE 6 — Cohésion par cluster
# ─────────────────────────────────────────────
print("\n[6] Cohésion par cluster ...")

cluster_cohesions = []
for c, items in groups.items():
    idxs = [tasks.index(t) for t in items]
    if len(idxs) > 1:
        d   = dist[np.ix_(idxs, idxs)]
        coh = d[np.triu_indices_from(d, 1)].mean()
        cluster_cohesions.append(coh)

mean_cohesion = np.mean(cluster_cohesions) if cluster_cohesions else 0.0
print(f"    Cohésion moyenne initiale : {mean_cohesion:.3f}")


# ─────────────────────────────────────────────
# ÉTAPE 7 — Reclustering itératif (best_split_by_k)
# ─────────────────────────────────────────────
print("\n[7] Reclustering itératif ...")

def compute_cohesion(sub_dist):
    n = sub_dist.shape[0]
    if n < 2:
        return 0.0
    return sub_dist[np.triu_indices_from(sub_dist, 1)].mean()


def best_split_by_k(tasks_subset, dist_matrix_subset):
    """
    Cherche le plus petit k (2..n) tel que cohésion moyenne <= COHESION_SPLIT_MAX.
    """
    n = len(tasks_subset)
    for k in range(2, n + 1):
        clustering = AgglomerativeClustering(
            n_clusters=k,
            metric="precomputed",
            linkage="average"
        )
        labels = clustering.fit_predict(dist_matrix_subset)
        total  = sum(
            compute_cohesion(
                dist_matrix_subset[np.ix_(
                    np.where(labels == lbl)[0],
                    np.where(labels == lbl)[0]
                )]
            )
            for lbl in set(labels)
        )
        avg = total / k
        if avg <= COHESION_SPLIT_MAX:
            return {"k": k, "labels": labels, "avg_cohesion": avg}
    return {"k": None, "labels": None, "avg_cohesion": None}


final_groups      = {}
new_label_counter = 0
clusters_to_check = list(groups.values())

while clusters_to_check:
    current = clusters_to_check.pop(0)
    n       = len(current)

    if n < 2:
        final_groups[new_label_counter] = current
        new_label_counter += 1
        continue

    idxs     = [tasks.index(t) for t in current]
    sub_dist = dist[np.ix_(idxs, idxs)]
    coh      = compute_cohesion(sub_dist)

    # Reclustering si cohésion trop haute OU cluster trop grand
    should_recluster = (coh > COHESION_THRESHOLD) or (n > SIZE_THRESHOLD)

    if should_recluster:
        split = best_split_by_k(current, sub_dist)
        if split["labels"] is None:
            final_groups[new_label_counter] = current
            new_label_counter += 1
        else:
            new_sub_groups = defaultdict(list)
            for i, lbl in enumerate(split["labels"]):
                new_sub_groups[lbl].append(current[i])
            for sub_items in new_sub_groups.values():
                clusters_to_check.append(sub_items)
    else:
        final_groups[new_label_counter] = current
        new_label_counter += 1

print(f"    {len(final_groups)} clusters après reclustering itératif.")


# ─────────────────────────────────────────────
# ÉTAPE 8 — Extraction des singletons
# ─────────────────────────────────────────────
print("\n[8] Extraction des singletons ...")

singletons           = []
non_singleton_groups = {}

for cid, items in final_groups.items():
    if len(items) == 1:
        singletons.append(items[0])
    else:
        non_singleton_groups[cid] = items

print(f"    {len(singletons)} singletons sur {len(tasks)} tâches.")


# ─────────────────────────────────────────────
# ÉTAPE 9 — Reclustering global des singletons
# ─────────────────────────────────────────────
print("\n[9] Reclustering global des singletons ...")

singleton_clusters = {}

if len(singletons) / len(tasks) < SINGLETON_RATIO:
    print("    Ratio insuffisant → singletons conservés tels quels.")
    for t in singletons:
        singleton_clusters[len(singleton_clusters)] = [t]
else:
    print("    Reclustering global des singletons activé.")
    singleton_idxs = [tasks.index(t) for t in singletons]
    new_dist       = dist[np.ix_(singleton_idxs, singleton_idxs)]
    new_dist       = np.clip(new_dist, 0, None)

    best_singleton = {"th": None, "silhouette": -1, "labels": None}

    for th in THRESHOLDS:
        if len(singletons) < 2:
            break
        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric="precomputed",
            linkage="average",
            distance_threshold=th
        )
        labels     = clustering.fit_predict(new_dist)
        n_clusters = len(set(labels))

        if n_clusters <= 1 or n_clusters > len(singletons) // 2:
            continue

        sil = silhouette_score(new_dist, labels, metric="precomputed")
        if sil > best_singleton["silhouette"]:
            best_singleton.update({"th": th, "silhouette": sil,
                                   "labels": labels})

    if best_singleton["labels"] is None:
        for t in singletons:
            singleton_clusters[len(singleton_clusters)] = [t]
    else:
        tmp = defaultdict(list)
        for task, lbl in zip(singletons, best_singleton["labels"]):
            tmp[lbl].append(task)
        singleton_clusters = dict(tmp)


# ─────────────────────────────────────────────
# ÉTAPE 10 — Fusion finale
# ─────────────────────────────────────────────
print("\n[10] Fusion finale ...")

final_merged_groups = {}
cid = 0
for items in non_singleton_groups.values():
    final_merged_groups[cid] = items
    cid += 1
for items in singleton_clusters.values():
    final_merged_groups[cid] = items
    cid += 1

task_to_index = {t: i for i, t in enumerate(tasks)}
labels_final  = np.full(len(tasks), -1, dtype=int)
for c, items in final_merged_groups.items():
    for t in items:
        labels_final[task_to_index[t]] = c

assert np.all(labels_final != -1), "Certaines tâches n'ont pas été assignées."
print(f"    {len(final_merged_groups)} clusters fusionnés.")


# ─────────────────────────────────────────────
# ÉTAPE 11 — Reclustering final (best_split_by_k)
# ─────────────────────────────────────────────
print(f"\n[11] Reclustering final (seuil cohésion = {COHESION_FINAL}) ...")

clusters_from_labels = defaultdict(list)
for idx, c in enumerate(labels_final):
    clusters_from_labels[c].append(tasks[idx])

clusters_to_recluster = []
clusters_kept         = {}

for c, items in clusters_from_labels.items():
    idxs     = [tasks.index(t) for t in items]
    sub_dist = dist[np.ix_(idxs, idxs)]
    coh      = compute_cohesion(sub_dist)
    if coh > COHESION_FINAL and len(idxs) >= 2:
        clusters_to_recluster.append((c, items))
    else:
        clusters_kept[c] = items

final_reclustered = {}
new_cid           = 0
assigned_tasks    = set()

for cid, items in clusters_to_recluster:
    queue = [items]
    while queue:
        current  = queue.pop(0)
        idxs     = [tasks.index(t) for t in current]
        sub_dist = dist[np.ix_(idxs, idxs)]
        coh      = compute_cohesion(sub_dist)

        if coh > COHESION_SPLIT_MAX:
            split = best_split_by_k(current, sub_dist)
            if split["labels"] is None:
                final_reclustered[new_cid] = current
                new_cid += 1
                assigned_tasks.update(current)
            else:
                new_groups = defaultdict(list)
                for i, lbl in enumerate(split["labels"]):
                    new_groups[lbl].append(current[i])
                for sub_items in new_groups.values():
                    sub_idxs = [tasks.index(t) for t in sub_items]
                    sub_d    = dist[np.ix_(sub_idxs, sub_idxs)]
                    if compute_cohesion(sub_d) > COHESION_SPLIT_MAX:
                        queue.append(sub_items)
                    else:
                        final_reclustered[new_cid] = sub_items
                        new_cid += 1
                        assigned_tasks.update(sub_items)
        else:
            final_reclustered[new_cid] = current
            new_cid += 1
            assigned_tasks.update(current)

for items in clusters_kept.values():
    if not any(t in assigned_tasks for t in items):
        final_reclustered[new_cid] = items
        new_cid += 1
        assigned_tasks.update(items)

print(f"    {len(final_reclustered)} clusters après reclustering final.")


# ─────────────────────────────────────────────
# ÉTAPE 12 — Métriques finales
# ─────────────────────────────────────────────
print("\n[12] Métriques finales ...")

labels_final2 = np.full(len(tasks), -1, dtype=int)
for c, items in final_reclustered.items():
    for t in items:
        labels_final2[tasks.index(t)] = c

n_clusters_final = len(set(labels_final2))

sil_final = (
    silhouette_score(dist, labels_final2, metric="precomputed")
    if 1 < n_clusters_final < len(tasks) else 0.0
)

cohesions_list = []
for c, items in final_reclustered.items():
    idxs = [tasks.index(t) for t in items]
    if len(idxs) >= 2:
        d   = dist[np.ix_(idxs, idxs)]
        coh = compute_cohesion(d)
        cohesions_list.append(coh)

mean_cohesion_final = np.mean(cohesions_list) if cohesions_list else 0.0

print(f"    Nombre de clusters   : {n_clusters_final}")
print(f"    Silhouette finale    : {sil_final:.3f}")
print(f"    Cohésion moyenne     : {mean_cohesion_final:.3f}")


# ─────────────────────────────────────────────
# ÉTAPE 14 — Post-processing ciblé
#
# Pour chaque cluster :
#   A) Cohésion >= POSTPROC_SPLIT_MIN → rediviser,
#      chaque fragment rejoint le cluster existant
#      le plus proche (si sim >= POSTPROC_MERGE_SIM),
#      sinon devient singleton.
#   B) Cohésion < POSTPROC_SPLIT_MIN → vérifier chaque
#      élément : s'il est plus proche d'un autre cluster
#      que du sien (marge >= POSTPROC_REASSIGN_MARGIN),
#      on le réassigne, sinon il reste.
# ─────────────────────────────────────────────
print("\n[14] Post-processing ciblé ...")

POSTPROC_SPLIT_MIN      = 0.40   # cohésion min pour forcer redivision
POSTPROC_MERGE_SIM      = 0.55   # similarité min pour fusionner dans un cluster existant
POSTPROC_REASSIGN_MARGIN = 0.05  # marge min pour réassigner un élément


def mean_sim_to_cluster(task_idx: int, cluster_idxs: list[int], sim_matrix: np.ndarray) -> float:
    """Similarité moyenne d'un élément avec les membres d'un cluster (lui exclu)."""
    others = [i for i in cluster_idxs if i != task_idx]
    if not others:
        return 0.0
    return float(sim_matrix[task_idx, others].mean())


# Matrice de similarité (1 - dist)
sim_matrix = 1 - dist

# Travailler sur une copie mutable
working_groups = {c: list(items) for c, items in final_reclustered.items()}
next_cid       = max(working_groups.keys()) + 1

# ── A) Rediviser les clusters trop cohésifs ──────────────
to_split = [
    cid for cid, items in working_groups.items()
    if len(items) >= 2 and compute_cohesion(
        dist[np.ix_([tasks.index(t) for t in items],
                    [tasks.index(t) for t in items])]
    ) >= POSTPROC_SPLIT_MIN
]

freed_elements = []   # éléments libérés après division

for cid in to_split:
    items    = working_groups.pop(cid)
    idxs     = [tasks.index(t) for t in items]
    sub_dist = dist[np.ix_(idxs, idxs)]
    split    = best_split_by_k(items, sub_dist)

    if split["labels"] is None:
        # Pas de split valide → libérer tous les éléments
        freed_elements.extend(items)
    else:
        sub_groups = defaultdict(list)
        for i, lbl in enumerate(split["labels"]):
            sub_groups[lbl].append(items[i])
        freed_elements.extend(items)   # on libère tout pour réassignation

print(f"    {len(to_split)} cluster(s) redivisé(s) → {len(freed_elements)} élément(s) libérés.")

# ── B) Réassigner chaque élément libéré ─────────────────
# (et aussi les éléments des clusters incohérents détectés par B)

# Détecter les éléments mal placés dans les clusters restants
for cid, items in list(working_groups.items()):
    if len(items) < 2:
        continue
    cluster_idxs = [tasks.index(t) for t in items]
    for t in items:
        t_idx    = tasks.index(t)
        sim_self = mean_sim_to_cluster(t_idx, cluster_idxs, sim_matrix)

        # Chercher le meilleur cluster alternatif
        best_other_sim = 0.0
        for other_cid, other_items in working_groups.items():
            if other_cid == cid or len(other_items) == 0:
                continue
            other_idxs   = [tasks.index(x) for x in other_items]
            sim_other    = mean_sim_to_cluster(t_idx, other_idxs, sim_matrix)
            if sim_other > best_other_sim:
                best_other_sim = sim_other

        if best_other_sim > sim_self + POSTPROC_REASSIGN_MARGIN:
            freed_elements.append(t)

# Dédupliquer freed_elements (un élément peut avoir été libéré deux fois)
seen_freed = set()
freed_elements = [t for t in freed_elements if not (t in seen_freed or seen_freed.add(t))]

# Retirer les éléments libérés de leurs clusters actuels
for t in freed_elements:
    for cid in list(working_groups.keys()):
        if t in working_groups[cid]:
            working_groups[cid].remove(t)

# Supprimer les clusters vides
working_groups = {c: items for c, items in working_groups.items() if items}

# Réassigner chaque élément libéré
reassigned = 0
new_singletons = 0

for t in freed_elements:
    t_idx      = tasks.index(t)
    best_cid   = None
    best_sim   = POSTPROC_MERGE_SIM   # seuil minimum

    for cid, items in working_groups.items():
        if not items:
            continue
        other_idxs = [tasks.index(x) for x in items]
        sim        = mean_sim_to_cluster(t_idx, other_idxs, sim_matrix)
        if sim > best_sim:
            best_sim = sim
            best_cid = cid

    if best_cid is not None:
        working_groups[best_cid].append(t)
        reassigned += 1
    else:
        # Singleton
        working_groups[next_cid] = [t]
        next_cid += 1
        new_singletons += 1

# Renuméroter proprement
final_reclustered = {i: items for i, items in enumerate(working_groups.values())}

print(f"    {reassigned} élément(s) réassigné(s), {new_singletons} nouveau(x) singleton(s).")
print(f"    {len(final_reclustered)} clusters après post-processing.")

# ── Fusion intelligente des singletons avant 'Autres petites tâches' ──
SINGLETON_MERGE_SIM = 0.45

singletons_to_group = [
    items[0]
    for items in final_reclustered.values()
    if len(items) == 1
]

# Retirer les singletons
final_reclustered = {
    cid: items
    for cid, items in final_reclustered.items()
    if len(items) > 1
}

sim_matrix_post = 1 - dist
singletons_merged  = 0
singletons_orphans = []

for t in singletons_to_group:
    t_idx    = tasks.index(t)
    best_cid = None
    best_sim = SINGLETON_MERGE_SIM

    for cid, items in final_reclustered.items():
        if len(items) < 2:
            continue
        other_idxs = [tasks.index(x) for x in items]
        sim = float(sim_matrix_post[t_idx, other_idxs].mean())
        if sim > best_sim:
            best_sim = sim
            best_cid = cid

    if best_cid is not None:
        final_reclustered[best_cid].append(t)
        singletons_merged += 1
    else:
        singletons_orphans.append(t)

print(f"    {singletons_merged} singleton(s) fusionné(s) dans un cluster existant.")
print(f"    {len(singletons_orphans)} singleton(s) orphelins → 'Autres petites tâches'.")

if singletons_orphans:
    autres_cid = (max(final_reclustered.keys()) + 1) if final_reclustered else 0
    final_reclustered[autres_cid] = singletons_orphans
    final_reclustered = {i: items for i, items in enumerate(final_reclustered.values())}
    AUTRES_CID = len(final_reclustered) - 1
    print(f"    Cluster 'Autres petites tâches' : {len(singletons_orphans)} tâche(s).")
else:
    final_reclustered = {i: items for i, items in enumerate(final_reclustered.values())}
    AUTRES_CID = None
    print("    Aucun singleton orphelin.")


# ─────────────────────────────────────────────
# Recalcul métriques après étape 14
# ─────────────────────────────────────────────
labels_final2 = np.full(len(tasks), -1, dtype=int)
for c, items in final_reclustered.items():
    for t in items:
        labels_final2[tasks.index(t)] = c

n_clusters_final = len(set(labels_final2))

sil_final = (
    silhouette_score(dist, labels_final2, metric="precomputed")
    if 1 < n_clusters_final < len(tasks) else 0.0
)

cohesions_list = []
for c, items in final_reclustered.items():
    idxs = [tasks.index(t) for t in items]
    if len(idxs) >= 2:
        cohesions_list.append(compute_cohesion(dist[np.ix_(idxs, idxs)]))

mean_cohesion_final = np.mean(cohesions_list) if cohesions_list else 0.0

print(f"    Silhouette après post-processing : {sil_final:.3f}")
print(f"    Cohésion moyenne après           : {mean_cohesion_final:.3f}")


# ─────────────────────────────────────────────
# ÉTAPE 13 — Sauvegarde du rapport texte
# ─────────────────────────────────────────────
print(f"\n[13] Écriture du rapport dans {OUTPUT_FILE} ...")

lines = []
lines.append("=" * 60)
lines.append("RAPPORT DE CLUSTERING DES TÂCHES")
lines.append("=" * 60)
lines.append(f"Tâches totales          : {len(tasks)}")
lines.append(f"Nombre de clusters      : {n_clusters_final}")
lines.append(f"Silhouette finale       : {sil_final:.3f}")
lines.append(f"Cohésion moyenne finale : {mean_cohesion_final:.3f}")
lines.append("")

for c, items in final_reclustered.items():
    idxs  = [tasks.index(t) for t in items]
    coh   = compute_cohesion(dist[np.ix_(idxs, idxs)])
    label = "Autres petites tâches" if c == AUTRES_CID else f"Cluster {c}"

    lines.append("─" * 60)
    lines.append(f"{label}  |  {len(items)} tâche(s)  |  cohésion = {coh:.3f}")
    lines.append("─" * 60)
    for t in items:
        lines.append(f"  • {t}")
    lines.append("")

lines.append("=" * 60)
lines.append("FIN DU RAPPORT")
lines.append("=" * 60)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n✅ Rapport sauvegardé : {OUTPUT_FILE}")
print(f"   {n_clusters_final} clusters | {len(tasks)} tâches")