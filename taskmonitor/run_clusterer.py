"""
run_clusterer.py
----------------
Entry point for running the clustering pipeline.
"""

from pathlib import Path

from taskmonitor.processing.clusterer.cluster_pipeline import ClusterPipeline
from taskmonitor.core.config import DESCRIBED_EVENTS_FILE

def main():
    # ─────────────────────────────────────────────
    # INPUT / OUTPUT
    # ─────────────────────────────────────────────
    input_file = DESCRIBED_EVENTS_FILE  # fichier réel existant

    # ─────────────────────────────────────────────
    # RUN PIPELINE
    # ─────────────────────────────────────────────
    pipeline = ClusterPipeline(input_file)
    result = pipeline.run()

    # ─────────────────────────────────────────────
    # DEBUG RAPIDE
    # ─────────────────────────────────────────────
    print("\nFinal summary :")
    print(f"    Clusters   : {result['metrics_after']['n_clusters']}")
    print(f"    Silhouette : {result['metrics_after']['silhouette']:.3f}")
    print(f"    Cohesion   : {result['metrics_after']['cohesion']:.3f}")


if __name__ == "__main__":
    main()