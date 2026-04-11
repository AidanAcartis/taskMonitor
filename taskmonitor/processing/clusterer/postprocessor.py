import numpy as np
from collections import defaultdict
from sklearn.metrics import silhouette_score

from taskmonitor.core.config import CLUSTER_CONFIG
from .metrics import ClusterMetrics
from .reclustering_engine import ReclusteringEngine


class PostProcessor:
    """
    Steps 10 → 14:
    - Final merging
    - Final reclustering
    - Metrics
    - Advanced post-processing
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
        print("\n[10] Final merger ...")

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

        print(f"    {len(final_merged)} merged clusters.")
        return final_merged, labels

    # ─────────────────────────────────────────────
    # ÉTAPE 11 — Reclustering final
    # ─────────────────────────────────────────────
    def final_reclustering(self, labels):
        print("\n[11] Final reclustering ...")

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

        print(f"    {len(final_groups)} clusters after final reclustering.")
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
        print("\n[14] Targeted post-processing...")

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

        print(f"    {reassigned} elements reassigned.")
        print(f"    {len(final)} clusters after post-processing.")

        return final

    # ─────────────────────────────────────────────
    # EXPORT
    # ─────────────────────────────────────────────
    def export(self, groups, metrics, output_file, autres_cid=None):
        print(f"\n[Export] {output_file}")

        lines = []
        lines.append("=" * 60)
        lines.append("TASK CLUSTERING REPORT")
        lines.append("=" * 60)

        lines.append(f"Total tasks          : {len(self.tasks)}")
        lines.append(f"Number of clusters      : {metrics['n_clusters']}")
        lines.append(f"Final silhouette       : {metrics['silhouette']:.3f}")
        lines.append(f"Final average cohesion : {metrics['cohesion']:.3f}")
        lines.append("")

        for c, items in groups.items():
            idxs = [self.task_to_index[t] for t in items]
            coh = self.metrics.compute_cohesion(
                self.dist[np.ix_(idxs, idxs)]
            )

            label = "Other small tasks" if autres_cid is not None and c == autres_cid else f"Cluster {c}"

            lines.append("─" * 60)
            lines.append(f"{label}  |  {len(items)} task(s)  |  cohesion = {coh:.3f}")
            lines.append("─" * 60)

            for t in items:
                lines.append(f"  • {t}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("END OF REPORT")
        lines.append("=" * 60)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print("Export completed")

    def merge_final_singletons(self, groups):
        print("\n[14bis] Fusion of singletons...")

        SINGLETON_MERGE_SIM = 0.45
        sim_matrix_post = 1 - self.dist

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

        singletons_merged = 0
        singletons_orphans = []

        for t in singletons:
            idx = self.task_to_index[t]

            best_cid = None
            best_sim = SINGLETON_MERGE_SIM

            for cid, items in groups.items():
                if len(items) < 2:
                    continue

                idxs = [self.task_to_index[x] for x in items]
                sim = float(sim_matrix_post[idx, idxs].mean())

                if sim > best_sim:
                    best_sim = sim
                    best_cid = cid

            if best_cid is not None:
                groups[best_cid].append(t)
                singletons_merged += 1
            else:
                singletons_orphans.append(t)

        print(f"    {singletons_merged} singleton(s) merged into an existing cluster.")
        print(f"    {len(singletons_orphans)} orphaned singleton(s) → 'Other small tasks'.")

        AUTRES_CID = None

        if singletons_orphans:
            autres_cid = (max(groups.keys()) + 1) if groups else 0
            groups[autres_cid] = singletons_orphans

            groups = {i: v for i, v in enumerate(groups.values())}
            AUTRES_CID = len(groups) - 1

            print(f"    Cluster 'Other small tasks': {len(singletons_orphans)} task(s).")
        else:
            groups = {i: v for i, v in enumerate(groups.values())}
            print("    No orphaned singletons.")

        return groups, AUTRES_CID