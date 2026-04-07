"""
processing/clusterer.py
=======================
Cluster les descriptions d'événements en groupes thématiques.
Refactorisation de cluster.py.
"""

import random
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sentence_transformers import SentenceTransformer, util

from taskmonitor.core import config, storage
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


class Clusterer:
    """
    Effectue le clustering des descriptions d'événements.
    Suit le même pipeline en 14 étapes que cluster.py original.
    """

    def __init__(self):
        self._model: SentenceTransformer | None = None

    def _ensure_model(self) -> bool:
        if self._model is not None:
            return True
        model_dir = config.MODEL_CLUSTERING
        if not model_dir.exists():
            log.error(f"Clustering model not found : {model_dir}")
            return False
        log.info(f"Loading the clustering model : {model_dir}")
        self._model = SentenceTransformer(str(model_dir))
        self._model.eval()
        return True

    # ── Helpers cohésion ─────────────────────

    @staticmethod
    def _compute_cohesion(sub_dist: np.ndarray) -> float:
        n = sub_dist.shape[0]
        if n < 2:
            return 0.0
        return float(sub_dist[np.triu_indices_from(sub_dist, 1)].mean())

    @staticmethod
    def _best_split_by_k(tasks_subset: list[str], dist_matrix: np.ndarray) -> dict:
        n = len(tasks_subset)
        for k in range(2, n + 1):
            clustering = AgglomerativeClustering(
                n_clusters=k, metric="precomputed", linkage="average"
            )
            labels = clustering.fit_predict(dist_matrix)
            idxs_per_label = [np.where(labels == lbl)[0] for lbl in set(labels)]
            total = sum(
                Clusterer._compute_cohesion(dist_matrix[np.ix_(idx, idx)])
                for idx in idxs_per_label
            )
            avg = total / k
            if avg <= config.CLUSTER_COHESION_SPLIT_MAX:
                return {"k": k, "labels": labels, "avg_cohesion": avg}
        return {"k": None, "labels": None, "avg_cohesion": None}

    # ── Pipeline principal ───────────────────

    def cluster(self, date_str: str) -> dict[int, list[str]]:
        """
        Lit events_described.csv, effectue le clustering complet,
        écrit clusters_output.txt et retourne les groupes.

        Args:
            date_str: date au format "YYYY-MM-DD"

        Returns:
            dict {cluster_id: [description, ...]}
        """
        if not self._ensure_model():
            return {}

        df = storage.read_events_described(date_str)
        if df.empty:
            log.error(f"empty events_described.csv for {date_str}")
            return {}

        # ── Étape 1 : normalisation ──────────
        def _norm(t: str) -> str:
            return t.replace('\\"', '').replace('"', '').lower().strip()

        tasks_raw = [_norm(t) for t in df["description"].fillna("").tolist() if t]
        seen: set[str] = set()
        tasks_raw = [t for t in tasks_raw if not (t in seen or seen.add(t))]
        log.info(f"[1] {len(tasks_raw)} unique descriptions")

        if len(tasks_raw) < 2:
            log.warning("Not enough descriptions to cluster")
            return {0: tasks_raw}

        # ── Étape 2 : shuffle ────────────────
        tasks = tasks_raw[:]
        random.seed(config.CLUSTER_RANDOM_SEED)
        random.shuffle(tasks)

        # ── Étape 3 : embeddings ─────────────
        log.info("[3] Calcul des embeddings...")
        embeddings = self._model.encode(
            tasks, convert_to_tensor=True, normalize_embeddings=True
        )

        # ── Étape 4 : matrice distance ───────
        sim  = util.cos_sim(embeddings, embeddings).cpu().numpy()
        dist = np.clip(1 - sim, 0, None)

        # ── Étape 5 : clustering initial ─────
        thresholds = np.arange(
            config.CLUSTER_THRESHOLDS_START,
            config.CLUSTER_THRESHOLDS_END,
            config.CLUSTER_THRESHOLDS_STEP,
        )
        best = {"th": None, "silhouette": -1, "labels": None}

        for th in thresholds:
            clustering = AgglomerativeClustering(
                n_clusters=None, metric="precomputed",
                linkage="average", distance_threshold=th
            )
            labels = clustering.fit_predict(dist)
            n_cl   = len(set(labels))
            if n_cl <= 1 or n_cl > len(tasks) // 2:
                continue
            sil = silhouette_score(dist, labels, metric="precomputed")
            if sil > best["silhouette"]:
                best.update({"th": th, "silhouette": sil, "labels": labels})

        if best["labels"] is None:
            log.warning("No valid clustering found")
            return {0: tasks}

        log.info(f"[5] Best threshold: {best['th']:.2f} | silhouette: {best['silhouette']:.3f}")

        groups: dict[int, list[str]] = defaultdict(list)
        for task, lbl in zip(tasks, best["labels"]):
            groups[lbl].append(task)

        # ── Étapes 6–11 : reclustering itératif et post-processing ──
        final_groups = self._recluster_iterative(groups, tasks, dist)
        final_groups = self._postprocess(final_groups, tasks, dist, sim)

        # ── Étape 13 : sauvegarde ────────────
        self._write_report(date_str, final_groups, tasks, dist)

        log.info(f"Clustering completed : {len(final_groups)} clusters")
        return final_groups

    def _recluster_iterative(
        self, groups: dict, tasks: list[str], dist: np.ndarray
    ) -> dict[int, list[str]]:
        """Étapes 7–11 : reclustering itératif par cohésion."""
        final: dict[int, list[str]] = {}
        counter = 0
        queue   = list(groups.values())

        while queue:
            current = queue.pop(0)
            n = len(current)
            if n < 2:
                final[counter] = current
                counter += 1
                continue
            idxs     = [tasks.index(t) for t in current]
            sub_dist = dist[np.ix_(idxs, idxs)]
            coh      = self._compute_cohesion(sub_dist)
            should   = (coh > config.CLUSTER_COHESION_THRESHOLD) or (n > config.CLUSTER_SIZE_THRESHOLD)

            if should:
                split = self._best_split_by_k(current, sub_dist)
                if split["labels"] is None:
                    final[counter] = current
                    counter += 1
                else:
                    new_groups: dict[int, list[str]] = defaultdict(list)
                    for i, lbl in enumerate(split["labels"]):
                        new_groups[lbl].append(current[i])
                    queue.extend(new_groups.values())
            else:
                final[counter] = current
                counter += 1

        return final

    def _postprocess(
        self, groups: dict[int, list[str]], tasks: list[str],
        dist: np.ndarray, sim: np.ndarray
    ) -> dict[int, list[str]]:
        """Étape 14 : post-processing, réassignation des singletons."""
        POSTPROC_SPLIT_MIN       = 0.40
        POSTPROC_MERGE_SIM       = 0.55
        POSTPROC_REASSIGN_MARGIN = 0.05
        SINGLETON_MERGE_SIM      = 0.45

        working = {c: list(items) for c, items in groups.items()}
        next_cid = max(working.keys()) + 1 if working else 0

        def mean_sim_to(t_idx: int, cluster_idxs: list[int]) -> float:
            others = [i for i in cluster_idxs if i != t_idx]
            if not others:
                return 0.0
            return float(sim[t_idx, others].mean())

        # Libérer les clusters trop cohésifs
        freed: list[str] = []
        to_split = [
            cid for cid, items in working.items()
            if len(items) >= 2 and self._compute_cohesion(
                dist[np.ix_([tasks.index(t) for t in items],
                             [tasks.index(t) for t in items])]
            ) >= POSTPROC_SPLIT_MIN
        ]
        for cid in to_split:
            items = working.pop(cid)
            freed.extend(items)

        # Libérer les éléments mal placés
        for cid, items in list(working.items()):
            if len(items) < 2:
                continue
            c_idxs = [tasks.index(t) for t in items]
            for t in items:
                t_idx    = tasks.index(t)
                sim_self = mean_sim_to(t_idx, c_idxs)
                best_other = max(
                    (mean_sim_to(t_idx, [tasks.index(x) for x in other_items])
                     for oc, other_items in working.items() if oc != cid and other_items),
                    default=0.0
                )
                if best_other > sim_self + POSTPROC_REASSIGN_MARGIN:
                    freed.append(t)

        # Dédupliquer
        seen_f: set[str] = set()
        freed = [t for t in freed if not (t in seen_f or seen_f.add(t))]

        # Retirer des clusters
        for t in freed:
            for cid in list(working.keys()):
                if t in working[cid]:
                    working[cid].remove(t)
        working = {c: items for c, items in working.items() if items}

        # Réassigner
        for t in freed:
            t_idx    = tasks.index(t)
            best_cid = None
            best_sim = POSTPROC_MERGE_SIM
            for cid, items in working.items():
                if not items:
                    continue
                s = mean_sim_to(t_idx, [tasks.index(x) for x in items])
                if s > best_sim:
                    best_sim = s
                    best_cid = cid
            if best_cid is not None:
                working[best_cid].append(t)
            else:
                working[next_cid] = [t]
                next_cid += 1

        # Fusionner singletons
        singletons = [items[0] for items in working.values() if len(items) == 1]
        working    = {c: items for c, items in working.items() if len(items) > 1}
        orphans    = []

        for t in singletons:
            t_idx    = tasks.index(t)
            best_cid = None
            best_sim = SINGLETON_MERGE_SIM
            for cid, items in working.items():
                if len(items) < 2:
                    continue
                s = float(sim[t_idx, [tasks.index(x) for x in items]].mean())
                if s > best_sim:
                    best_sim = s
                    best_cid = cid
            if best_cid is not None:
                working[best_cid].append(t)
            else:
                orphans.append(t)

        if orphans:
            autres = (max(working.keys()) + 1) if working else 0
            working[autres] = orphans

        return {i: items for i, items in enumerate(working.values())}

    def _write_report(
        self, date_str: str, groups: dict[int, list[str]],
        tasks: list[str], dist: np.ndarray
    ) -> None:
        """Écrit clusters_output.txt."""
        AUTRES_CID = len(groups) - 1 if groups else None
        labels_arr = np.full(len(tasks), -1, dtype=int)
        for c, items in groups.items():
            for t in items:
                labels_arr[tasks.index(t)] = c

        valid = [l for l in labels_arr if l != -1]
        n_cl  = len(set(valid))
        sil   = (
            silhouette_score(dist, labels_arr, metric="precomputed")
            if 1 < n_cl < len(tasks) else 0.0
        )
        cohs  = []
        for c, items in groups.items():
            if len(items) >= 2:
                idxs = [tasks.index(t) for t in items]
                cohs.append(self._compute_cohesion(dist[np.ix_(idxs, idxs)]))
        mean_coh = float(np.mean(cohs)) if cohs else 0.0

        lines = [
            "=" * 60,
            "TASK CLUSTERING REPORT",
            "=" * 60,
            f"Total tasks          : {len(tasks)}",
            f"Number of clusters      : {n_cl}",
            f"Final silhouette       : {sil:.3f}",
            f"Average cohesion : {mean_coh:.3f}",
            "",
        ]

        for c, items in groups.items():
            idxs  = [tasks.index(t) for t in items]
            coh   = self._compute_cohesion(dist[np.ix_(idxs, idxs)])
            label = "Other small tasks" if c == AUTRES_CID and len(items) == 1 else f"Cluster {c}"
            lines += [
                "─" * 60,
                f"{label}  |  {len(items)} task(s)  |  cohesion = {coh:.3f}",
                "─" * 60,
            ]
            for t in items:
                lines.append(f"  • {t}")
            lines.append("")

        lines += ["=" * 60, "END OF REPORT", "=" * 60]
        storage.write_clusters_output(date_str, "\n".join(lines))