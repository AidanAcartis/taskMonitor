"""
run_clusterer.py
----------------
Point d'entrée pour exécuter le pipeline de clustering.
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
    print("\n📊 Résumé final :")
    print(f"    Clusters   : {result['metrics_after']['n_clusters']}")
    print(f"    Silhouette : {result['metrics_after']['silhouette']:.3f}")
    print(f"    Cohésion   : {result['metrics_after']['cohesion']:.3f}")


if __name__ == "__main__":
    main()