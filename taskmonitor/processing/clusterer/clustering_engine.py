# clustering_engine.py
# ─────────────────────────────────────────────
# CLUSTERING INITIAL
# ─────────────────────────────────────────────

import numpy as np
from collections import defaultdict
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

class ClusteringEngine:
    """
    Classe pour gérer le clustering initial avec recherche automatique
    du meilleur threshold basé sur la silhouette et la cohésion interne.
    """

    def __init__(self, thresholds: np.ndarray):
        """
        Args:
            thresholds: array-like des thresholds à tester pour le clustering
        """
        self.thresholds = thresholds

    # ─────────────────────────────────────────────
    # Méthodes privées
    # ─────────────────────────────────────────────

    def _compute_cohesion_map(self, dist_matrix: np.ndarray, labels: np.ndarray) -> dict:
        """
        Calcule la cohésion moyenne de chaque cluster.
        """
        clusters = defaultdict(list)
        for i, c in enumerate(labels):
            clusters[c].append(i)

        cohesions = {}
        for c, idxs in clusters.items():
            if len(idxs) < 2:
                cohesions[c] = 0.0
                continue
            sub = dist_matrix[np.ix_(idxs, idxs)]
            cohesions[c] = sub[np.triu_indices_from(sub, 1)].mean()

        return cohesions

    def _cluster(self, dist_matrix: np.ndarray, threshold: float) -> np.ndarray:
        """
        Applique l'agglomerative clustering pour un threshold donné.
        """
        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric="precomputed",
            linkage="average",
            distance_threshold=threshold
        )
        return clustering.fit_predict(dist_matrix)

    def _find_best_threshold(self, tasks: list, dist_matrix: np.ndarray) -> dict:
        """
        Recherche le meilleur threshold basé sur la silhouette score.
        """
        best = {"threshold": None, "silhouette": -1, "labels": None, "cohesion": None}

        for th in self.thresholds:
            labels = self._cluster(dist_matrix, th)
            n_clusters = len(set(labels))

            # Ignore clustering trivial ou trop fragmenté
            if n_clusters <= 1 or n_clusters > len(tasks) // 2:
                continue

            sil = silhouette_score(dist_matrix, labels, metric="precomputed")
            cohesion = self._compute_cohesion_map(dist_matrix, labels)

            if sil > best["silhouette"]:
                best.update({
                    "threshold": th,
                    "silhouette": sil,
                    "labels": labels,
                    "cohesion": cohesion
                })

        if best["labels"] is None:
            raise RuntimeError("Aucun clustering valide trouvé.")

        return best

    def _labels_to_groups(self, tasks: list, labels: np.ndarray) -> dict:
        """
        Transforme les labels en dictionnaire de clusters {cluster_id: [tasks]}.
        """
        groups = defaultdict(list)
        for task, lbl in zip(tasks, labels):
            groups[lbl].append(task)
        return dict(groups)

    # ─────────────────────────────────────────────
    # Méthode publique
    # ─────────────────────────────────────────────

    def initial_clustering(self, tasks: list, dist_matrix: np.ndarray) -> dict:
        """
        Réalise le clustering initial avec recherche du meilleur threshold.
        Args:
            tasks: liste des descriptions
            dist_matrix: matrice de distance (1 - cos_sim)
        Returns:
            dict: {cluster_id: [tasks]}
        """
        print("\n[5] Clustering initial (recherche meilleur threshold) ...")
        best = self._find_best_threshold(tasks, dist_matrix)
        print(
            f"    Meilleur threshold : {best['threshold']:.2f} "
            f"| silhouette : {best['silhouette']:.3f}"
        )
        groups = self._labels_to_groups(tasks, best["labels"])
        return groups