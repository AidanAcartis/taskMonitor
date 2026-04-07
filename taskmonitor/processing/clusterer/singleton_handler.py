# processing/clusterer/singleton_handler.py
import numpy as np
from collections import defaultdict
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from taskmonitor.core.config import CLUSTER_CONFIG

SINGLETON_RATIO = CLUSTER_CONFIG["singleton_ratio"]
THRESHOLDS = CLUSTER_CONFIG["thresholds"]

class SingletonHandler:
    """
    Gère l'extraction des singletons et le reclustering global des singletons.
    """

    def __init__(self, tasks, dist_matrix):
        """
        Args:
            tasks (list[str]): liste complète des tâches
            dist_matrix (np.ndarray): matrice de distance (n x n)
        """
        self.tasks = tasks
        self.dist  = dist_matrix

    # ─────────────────────────────────────────────
    # Extraction des singletons (étape 8)
    # ─────────────────────────────────────────────
    def extract_singletons(self, groups):
        """
        Sépare les singletons des clusters normaux.

        Args:
            groups (dict[int, list[str]]): clusters après reclustering itératif

        Returns:
            tuple:
                non_singleton_groups (dict[int, list[str]]),
                singletons (list[str])
        """
        singletons = []
        non_singleton_groups = {}

        for cid, items in groups.items():
            if len(items) == 1:
                singletons.append(items[0])
            else:
                non_singleton_groups[cid] = items

        print(f"    {len(singletons)} singletons sur {len(self.tasks)} tâches.")
        return non_singleton_groups, singletons

    # ─────────────────────────────────────────────
    # Reclustering global des singletons (étape 9)
    # ─────────────────────────────────────────────
    def recluster_singletons(self, singletons):
        """
        Reclustering global des singletons si le ratio est suffisant.

        Args:
            singletons (list[str]): liste des singletons à traiter

        Returns:
            dict[int, list[str]]: clusters de singletons après reclustering
        """
        singleton_clusters = {}

        if len(singletons) / len(self.tasks) < SINGLETON_RATIO:
            print("    Ratio insuffisant → singletons conservés tels quels.")
            for t in singletons:
                singleton_clusters[len(singleton_clusters)] = [t]
            return singleton_clusters

        print("    Reclustering global des singletons activé.")
        singleton_idxs = [self.tasks.index(t) for t in singletons]
        new_dist = self.dist[np.ix_(singleton_idxs, singleton_idxs)]
        new_dist = np.clip(new_dist, 0, None)

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
            labels = clustering.fit_predict(new_dist)
            n_clusters = len(set(labels))

            if n_clusters <= 1 or n_clusters > len(singletons) // 2:
                continue

            sil = silhouette_score(new_dist, labels, metric="precomputed")
            if sil > best_singleton["silhouette"]:
                best_singleton.update({
                    "th": th,
                    "silhouette": sil,
                    "labels": labels
                })

        if best_singleton["labels"] is None:
            for t in singletons:
                singleton_clusters[len(singleton_clusters)] = [t]
        else:
            tmp = defaultdict(list)
            for task, lbl in zip(singletons, best_singleton["labels"]):
                tmp[lbl].append(task)
            singleton_clusters = dict(tmp)

        print(f"    {len(singleton_clusters)} clusters of singletons after reclustering.")
        return singleton_clusters