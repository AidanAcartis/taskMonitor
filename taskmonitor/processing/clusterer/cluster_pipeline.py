"""
cluster_pipeline.py
-------------------
Main pipeline orchestrating all clustering steps.

Order:
1. Load + prepare
2. Embeddings
3. Distance matrix
4. Initial clustering
5. Iterative reclustering
6. Singleton handling
7. Final merging
8. Final reclustering
9. Metrics (before post-processing)
10. Post-processing
11. Metrics (after post-processing)
12. Export
"""

from pathlib import Path

from taskmonitor.core.config import CLUSTER_CONFIG, CLUSTER_OUTPUT_FILE

from .utils import load_and_prepare_tasks, save_report
from .embedding_service import EmbeddingService
from .distance_builder import DistanceBuilder
from .clustering_engine import ClusteringEngine
from .reclustering_engine import ReclusteringEngine
from .singleton_handler import SingletonHandler
from .postprocessor import PostProcessor


class ClusterPipeline:
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.config   = CLUSTER_CONFIG

    # ─────────────────────────────────────────────
    # RUN PIPELINE
    # ─────────────────────────────────────────────
    def run(self):
        print("\n" + "=" * 60)
        print("CLUSTERING PIPELINE LAUNCH")
        print("=" * 60)

        # ─────────────────────────────────────────
        # [1-2] LOAD + PREPARE
        # ─────────────────────────────────────────
        tasks = load_and_prepare_tasks(self.csv_path, self.config)

        # ─────────────────────────────────────────
        # [3] EMBEDDINGS
        # ─────────────────────────────────────────
        embedder = EmbeddingService()
        embeddings = embedder.encode(tasks)

        # ─────────────────────────────────────────
        # [4] DISTANCE MATRIX
        # ─────────────────────────────────────────
        dist_builder = DistanceBuilder()
        dist_matrix = dist_builder.build(embeddings)

        # ─────────────────────────────────────────
        # [5] CLUSTERING INITIAL
        # ─────────────────────────────────────────
        clustering_engine = ClusteringEngine(
            thresholds=self.config["thresholds"]
        )
        initial_groups = clustering_engine.initial_clustering(
            tasks, dist_matrix
        )

        # ─────────────────────────────────────────
        # [6-7] RECLUSTERING ITÉRATIF
        # ─────────────────────────────────────────
        recluster_engine = ReclusteringEngine(tasks, dist_matrix)
        reclustered_groups = recluster_engine.iterative_reclustering(
            initial_groups
        )

        # ─────────────────────────────────────────
        # [8-9] SINGLETON HANDLING
        # ─────────────────────────────────────────
        singleton_handler = SingletonHandler(tasks, dist_matrix)

        non_singleton_groups, singletons = (
            singleton_handler.extract_singletons(reclustered_groups)
        )

        singleton_clusters = singleton_handler.recluster_singletons(
            singletons
        )

        # ─────────────────────────────────────────
        # [10 → 14] POST-PROCESSOR GLOBAL
        # ─────────────────────────────────────────
        post = PostProcessor(tasks, dist_matrix)

        # ── Étape 10 : Fusion
        merged_groups, labels = post.merge_groups(
            non_singleton_groups,
            singleton_clusters
        )

        # ── Étape 11 : Reclustering final
        final_groups = post.final_reclustering(labels)

        # ── Étape 12 : Metrics AVANT post-processing
        metrics_before = post.compute_metrics(
            final_groups,
            label="avant post-processing"
        )

        # ── Étape 14 : Post-processing avancé
        final_groups = post.postprocess(final_groups)

        final_groups, autres_cid = post.merge_final_singletons(final_groups)

        # ── Metrics APRÈS post-processing
        metrics_after = post.compute_metrics(
            final_groups,
            label="après post-processing"
        )

        # ─────────────────────────────────────────
        # EXPORT FINAL
        # ─────────────────────────────────────────
        post.export(
            groups=final_groups,
            metrics=metrics_after,
            output_file=CLUSTER_OUTPUT_FILE,
            autres_cid=autres_cid
        )

        print("\n" + "=" * 60)
        print("PIPELINE FINISHED")
        print("=" * 60)

        return {
            "tasks": tasks,
            "groups": final_groups,
            "metrics_before": metrics_before,
            "metrics_after": metrics_after
        }