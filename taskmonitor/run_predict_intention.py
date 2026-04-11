#!/usr/bin/env python3
"""
Entry point for generating overall cluster intentions.
"""

import sys
from pathlib import Path
import argparse

from taskmonitor.core.config import INTENTION_OUTPUT_TXT, INTENTION_OUTPUT_JSONL, INTENTION_MODEL_DIR
from taskmonitor.processing.io_utils import write_txt, write_jsonl
from taskmonitor.processing.intention_predictor import load_model, predict, generate_simple_intention, clean_intention
from taskmonitor.processing.cluster_output_parser import parse_clusters

def parse_args():
    parser = argparse.ArgumentParser(description="Genere une global task intention pour chaque cluster.")
    parser.add_argument("--input", default=Path("data/exports/clusters_output.txt"), help="Fichier de clusters en entree")
    parser.add_argument("--model", default=INTENTION_MODEL_DIR, help="Chemin vers le modele Flan-T5 fine-tune")
    parser.add_argument("--out-txt", default=INTENTION_OUTPUT_TXT, help="Fichier texte de sortie")
    parser.add_argument("--out-jsonl", default=INTENTION_OUTPUT_JSONL, help="Fichier JSONL de sortie")
    return parser.parse_args()

def main():
    args = parse_args()

    print(f"\n{'='*65}")
    print("  CLUSTER GLOBAL TASK INTENTION PREDICTOR")
    print(f"{'='*65}\n")

    clusters = parse_clusters(args.input)
    print(f"{len(clusters)} clusters founded")

    model, tokenizer, device = load_model(args.model)

    results = []
    for cluster in clusters:
        if cluster.get("is_singleton"):
            intention = generate_simple_intention(cluster["items"][0])
        else:
            intention = predict(model, tokenizer, device, cluster["items"])
        intention = clean_intention(intention)
        cluster["intention"] = intention
        results.append(cluster)
        print(f"{cluster['cluster_id']} -> {intention}")

    write_txt(results, args.out_txt)
    write_jsonl(results, args.out_jsonl)

    print(f"\nOutputs generated : {args.out_txt}, {args.out_jsonl}")

if __name__ == "__main__":
    main()