# processing/clusterer/metrics.py
import numpy as np
from collections import defaultdict
from sklearn.metrics import silhouette_score

class ClusterMetrics:
    """
    Class for calculating cluster cohesion and silhouette.
    """

    def __init__(self, dist_matrix, tasks):
        """
        Args:
            dist_matrix (np.ndarray): distance matrix (n x n)
            tasks (list[str]): list of corresponding tasks
        """
        self.dist = dist_matrix
        self.tasks = tasks

    # ─────────────────────────────────────────────
    # Cohesion of a sub-cluster (step 7)
    # ─────────────────────────────────────────────
    def compute_cohesion(self, sub_dist):
        n = sub_dist.shape[0]
        if n < 2:
            return 0.0
        return sub_dist[np.triu_indices_from(sub_dist, 1)].mean()

    # ─────────────────────────────────────────────
    # Cohesion per cluster (step 6)
    # ─────────────────────────────────────────────
    def cluster_cohesions(self, groups):
        """
        
        Calculate the cohesion of each cluster and the average cohesion.

        Args:
            groups (dict[int, list[str]]): dict cluster_id -> tasks

        Returns:
            tuple: (dict cohesion per cluster, average cohesion)
        """
        cluster_cohesions = []
        cohesion_map = {}

        for c, items in groups.items():
            idxs = [self.tasks.index(t) for t in items]
            if len(idxs) > 1:
                sub_dist = self.dist[np.ix_(idxs, idxs)]
                coh = self.compute_cohesion(sub_dist)
                cohesion_map[c] = coh
                cluster_cohesions.append(coh)
            else:
                cohesion_map[c] = 0.0

        mean_cohesion = np.mean(cluster_cohesions) if cluster_cohesions else 0.0
        return cohesion_map, mean_cohesion

    # ─────────────────────────────────────────────
    # Silhouette score pour clusters
    # ─────────────────────────────────────────────
    def silhouette_score(self, labels):
        """
        Calculate the silhouette on the distance matrix.

        Args:
            labels (list[int] | np.ndarray): cluster labels

        Returns:
            float: silhouette score
        """
        if len(set(labels)) < 2:
            return -1.0
        return silhouette_score(self.dist, labels, metric="precomputed")

    # ─────────────────────────────────────────────
    # Map cohesion cluster for reclustering
    # ─────────────────────────────────────────────
    def cluster_cohesion_map(self, labels):
        """
        Return the average cohesion of each cluster.

        Args:
            labels (list[int] | np.ndarray): cluster labels

        Returns:
            dict[int, float]: cluster_id -> cohesion
        """
        clusters = defaultdict(list)
        for i, c in enumerate(labels):
            clusters[c].append(i)

        cohesions = {}
        for c, idxs in clusters.items():
            if len(idxs) < 2:
                cohesions[c] = 0.0
                continue
            sub = self.dist[np.ix_(idxs, idxs)]
            cohesions[c] = self.compute_cohesion(sub)
        return cohesions