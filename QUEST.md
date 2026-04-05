Le defaut vient du code de clustering. dans postprocessor.py :"import numpy as np
from collections import defaultdict
from sklearn.metrics import silhouette_score

from taskmonitor.core.config import CLUSTER_CONFIG
from .metrics import ClusterMetrics
from .reclustering_engine import ReclusteringEngine


class PostProcessor:
    """
    Étapes 10 → 14 :
    - Fusion finale
    - Reclustering final
    - Métriques
    - Post-processing avancé
    - Export
    """

    def __init__(self, tasks, dist_matrix):
        self.tasks = tasks
        self.dist = dist_matrix
        self.metrics = ClusterMetrics(dist_matrix, tasks)

        self.task_to_index = {t: i for i, t in enumerate(tasks)}

    # ─────────────────────────────────────────────
    # ÉTAPE 10 — Fusion finale
    # ─────────────────────────────────────────────
    def merge_groups(self, non_singleton_groups, singleton_clusters):
        print("\n[10] Fusion finale ...")

        final_merged = {}
        cid = 0

        for items in non_singleton_groups.values():
            final_merged[cid] = items
            cid += 1

        for items in singleton_clusters.values():
            final_merged[cid] = items
            cid += 1

        labels = np.full(len(self.tasks), -1, dtype=int)
        for c, items in final_merged.items():
            for t in items:
                labels[self.task_to_index[t]] = c

        assert np.all(labels != -1)

        print(f"    {len(final_merged)} clusters fusionnés.")
        return final_merged, labels

    # ─────────────────────────────────────────────
    # ÉTAPE 11 — Reclustering final
    # ─────────────────────────────────────────────
    def final_reclustering(self, labels):
        print("\n[11] Reclustering final ...")

        cfg = CLUSTER_CONFIG
        clusters = defaultdict(list)

        for idx, c in enumerate(labels):
            clusters[c].append(self.tasks[idx])

        clusters_to_recluster = []
        clusters_kept = {}

        for c, items in clusters.items():
            idxs = [self.task_to_index[t] for t in items]
            sub_dist = self.dist[np.ix_(idxs, idxs)]
            coh = self.metrics.compute_cohesion(sub_dist)

            if coh > cfg["cohesion_final"] and len(idxs) >= 2:
                clusters_to_recluster.append(items)
            else:
                clusters_kept[c] = items

        final_groups = {}
        new_cid = 0
        assigned = set()

        recluster_engine = ReclusteringEngine(self.tasks, self.dist)

        for items in clusters_to_recluster:
            queue = [items]

            while queue:
                current = queue.pop(0)
                idxs = [self.task_to_index[t] for t in current]
                sub_dist = self.dist[np.ix_(idxs, idxs)]
                coh = self.metrics.compute_cohesion(sub_dist)

                if coh > cfg["cohesion_split_max"]:
                    split = recluster_engine.best_split_by_k(current, sub_dist)

                    if split["labels"] is None:
                        final_groups[new_cid] = current
                        new_cid += 1
                        assigned.update(current)
                    else:
                        tmp = defaultdict(list)
                        for i, lbl in enumerate(split["labels"]):
                            tmp[lbl].append(current[i])

                        for sub_items in tmp.values():
                            sub_idxs = [self.task_to_index[t] for t in sub_items]
                            sub_d = self.dist[np.ix_(sub_idxs, sub_idxs)]

                            if self.metrics.compute_cohesion(sub_d) > cfg["cohesion_split_max"]:
                                queue.append(sub_items)
                            else:
                                final_groups[new_cid] = sub_items
                                new_cid += 1
                                assigned.update(sub_items)
                else:
                    final_groups[new_cid] = current
                    new_cid += 1
                    assigned.update(current)

        for items in clusters_kept.values():
            if not any(t in assigned for t in items):
                final_groups[new_cid] = items
                new_cid += 1

        print(f"    {len(final_groups)} clusters après reclustering final.")
        return final_groups

    # ─────────────────────────────────────────────
    # ÉTAPE 12 — Métriques
    # ─────────────────────────────────────────────
    def compute_metrics(self, groups, label=""):
        print(f"\n[Metrics {label}]")

        labels = np.full(len(self.tasks), -1)

        for c, items in groups.items():
            for t in items:
                labels[self.task_to_index[t]] = c

        n_clusters = len(set(labels))

        sil = (
            silhouette_score(self.dist, labels, metric="precomputed")
            if 1 < n_clusters < len(self.tasks) else 0.0
        )

        cohesions = []
        for items in groups.values():
            idxs = [self.task_to_index[t] for t in items]
            if len(idxs) >= 2:
                cohesions.append(
                    self.metrics.compute_cohesion(self.dist[np.ix_(idxs, idxs)])
                )

        mean_coh = np.mean(cohesions) if cohesions else 0.0

        print(f"    Clusters   : {n_clusters}")
        print(f"    Silhouette : {sil:.3f}")
        print(f"    Cohésion   : {mean_coh:.3f}")

        return {
            "n_clusters": n_clusters,
            "silhouette": sil,
            "cohesion": mean_coh
        }

    # ─────────────────────────────────────────────
    # ÉTAPE 14 — Post-processing
    # ─────────────────────────────────────────────
    def postprocess(self, groups):
        print("\n[14] Post-processing ciblé ...")

        cfg = CLUSTER_CONFIG

        recluster_engine = ReclusteringEngine(self.tasks, self.dist)

        sim_matrix = 1 - self.dist
        working = {c: list(items) for c, items in groups.items()}
        next_cid = max(working.keys()) + 1

        def mean_sim(idx, cluster_idxs):
            others = [i for i in cluster_idxs if i != idx]
            return float(sim_matrix[idx, others].mean()) if others else 0.0

        # A) split
        to_split = [
            cid for cid, items in working.items()
            if len(items) >= 2 and
            self.metrics.compute_cohesion(
                self.dist[np.ix_(
                    [self.task_to_index[t] for t in items],
                    [self.task_to_index[t] for t in items]
                )]
            ) >= cfg["postproc_split_min"]
        ]

        freed = []

        for cid in to_split:
            items = working.pop(cid)
            idxs = [self.task_to_index[t] for t in items]
            sub = self.dist[np.ix_(idxs, idxs)]
            split = recluster_engine.best_split_by_k(items, sub)

            if split["labels"] is None:
                freed.extend(items)
            else:
                freed.extend(items)

        # B) reassignment
        for cid, items in list(working.items()):
            if len(items) < 2:
                continue

            cluster_idxs = [self.task_to_index[t] for t in items]

            for t in items:
                idx = self.task_to_index[t]
                sim_self = mean_sim(idx, cluster_idxs)

                best_other = 0.0
                for ocid, oitems in working.items():
                    if ocid == cid:
                        continue
                    oidxs = [self.task_to_index[x] for x in oitems]
                    sim_other = mean_sim(idx, oidxs)
                    best_other = max(best_other, sim_other)

                if best_other > sim_self + cfg["postproc_reassign_margin"]:
                    freed.append(t)

        freed = list(set(freed))

        for t in freed:
            for cid in list(working.keys()):
                if t in working[cid]:
                    working[cid].remove(t)

        working = {c: v for c, v in working.items() if v}

        reassigned = 0

        for t in freed:
            idx = self.task_to_index[t]
            best_cid = None
            best_sim = cfg["postproc_merge_sim"]

            for cid, items in working.items():
                oidxs = [self.task_to_index[x] for x in items]
                sim = mean_sim(idx, oidxs)
                if sim > best_sim:
                    best_sim = sim
                    best_cid = cid

            if best_cid is not None:
                working[best_cid].append(t)
                reassigned += 1
            else:
                working[next_cid] = [t]
                next_cid += 1

        final = {i: v for i, v in enumerate(working.values())}

        print(f"    {reassigned} éléments réassignés.")
        print(f"    {len(final)} clusters après post-processing.")

        return final

    # ─────────────────────────────────────────────
    # EXPORT
    # ─────────────────────────────────────────────
    def export(self, groups, metrics, output_file):
        print(f"\n[Export] {output_file}")

        lines = []
        lines.append("=" * 60)
        lines.append("RAPPORT DE CLUSTERING")
        lines.append("=" * 60)

        lines.append(f"Tâches : {len(self.tasks)}")
        lines.append(f"Clusters : {metrics['n_clusters']}")
        lines.append(f"Silhouette : {metrics['silhouette']:.3f}")
        lines.append(f"Cohésion : {metrics['cohesion']:.3f}")
        lines.append("")

        for c, items in groups.items():
            idxs = [self.task_to_index[t] for t in items]
            coh = self.metrics.compute_cohesion(
                self.dist[np.ix_(idxs, idxs)]
            )

            lines.append(f"Cluster {c} ({len(items)} | {coh:.3f})")
            for t in items:
                lines.append(f"  • {t}")
            lines.append("")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print("✅ Export terminé")

    def merge_final_singletons(self, groups):
        print("\n[14bis] Fusion intelligente des singletons ...")

        SINGLETON_MERGE_SIM = 0.45
        sim_matrix = 1 - self.dist

        singletons = [
            items[0]
            for items in groups.values()
            if len(items) == 1
        ]

        # garder clusters non-singletons
        groups = {
            cid: items
            for cid, items in groups.items()
            if len(items) > 1
        }

        next_cid = max(groups.keys()) + 1 if groups else 0

        merged = 0
        orphans = []

        for t in singletons:
            idx = self.task_to_index[t]

            best_cid = None
            best_sim = SINGLETON_MERGE_SIM

            for cid, items in groups.items():
                idxs = [self.task_to_index[x] for x in items]
                sim = float(sim_matrix[idx, idxs].mean())

                if sim > best_sim:
                    best_sim = sim
                    best_cid = cid

            if best_cid is not None:
                groups[best_cid].append(t)
                merged += 1
            else:
                orphans.append(t)

        print(f"    {merged} singleton(s) fusionné(s).")
        print(f"    {len(orphans)} singleton(s) orphelins.")

        if orphans:
            groups[next_cid] = orphans

        # renuméroter
        final = {i: v for i, v in enumerate(groups.values())}

        return final", 
cette section de cluster.py est integre '
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
print(f"   {n_clusters_final} clusters | {len(tasks)} tâches")'

dans cette section, il y a l'inclusion du label 'Autres petites tâches' ce qui n'est pas inclus dans postprocessor.py. Il faut que la restructuration soit fidele a 100%, comment le corriger pour cela ?