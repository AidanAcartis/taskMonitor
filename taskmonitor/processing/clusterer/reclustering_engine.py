# processing/clusterer/reclustering_engine.py
import numpy as np
from collections import defaultdict
from sklearn.cluster import AgglomerativeClustering
from .metrics import ClusterMetrics
from taskmonitor.core.config import CLUSTER_CONFIG

COHESION_THRESHOLD = CLUSTER_CONFIG["cohesion_threshold"]
SIZE_THRESHOLD     = CLUSTER_CONFIG["size_threshold"]
COHESION_SPLIT_MAX = CLUSTER_CONFIG["cohesion_split_max"]

class ReclusteringEngine:
    """
    Classe pour gérer le reclustering itératif des clusters existants.
    """

    def __init__(self, tasks, dist_matrix):
        """
        Args:
            tasks (list[str]): liste de toutes les tâches
            dist_matrix (np.ndarray): matrice de distance (n x n)
        """
        self.tasks = tasks
        self.dist  = dist_matrix
        self.metrics = ClusterMetrics(dist_matrix, tasks)

    # ─────────────────────────────────────────────
    # Cohésion d'un sous-cluster (utilise ClusterMetrics)
    # ─────────────────────────────────────────────
    def compute_cohesion(self, sub_dist):
        return self.metrics.compute_cohesion(sub_dist)

    # ─────────────────────────────────────────────
    # Best split by k (étape 7)
    # ─────────────────────────────────────────────
    def best_split_by_k(self, tasks_subset, dist_matrix_subset):
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
                self.compute_cohesion(
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

    # ─────────────────────────────────────────────
    # Reclustering itératif global
    # ─────────────────────────────────────────────
    def iterative_reclustering(self, groups):
        """
        Args:
            groups (dict[int, list[str]]): clusters initiaux
        Returns:
            dict[int, list[str]]: clusters après reclustering
        """
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

            idxs     = [self.tasks.index(t) for t in current]
            sub_dist = self.dist[np.ix_(idxs, idxs)]
            coh      = self.compute_cohesion(sub_dist)

            # Reclustering si cohésion trop haute OU cluster trop grand
            should_recluster = (coh > COHESION_THRESHOLD) or (n > SIZE_THRESHOLD)

            if should_recluster:
                split = self.best_split_by_k(current, sub_dist)
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

        print(f"    {len(final_groups)} clusters after iterative reclustering.")
        return final_groups