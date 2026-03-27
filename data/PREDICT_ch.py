#!/usr/bin/env python3
"""
============================================================
  Cluster Global Task Intention Predictor - Version CORRIGÉE
============================================================
"""

import re
import json
import sys
import argparse
from pathlib import Path

import torch
from transformers import T5ForConditionalGeneration, T5TokenizerFast

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
DEFAULT_INPUT     = "clusters_output.txt"
DEFAULT_MODEL     = "./final_Model_V3/final_model"
DEFAULT_OUT_TXT   = "clusters_with_intentions_ch.txt"
DEFAULT_OUT_JSONL = "clusters_with_intentions_ch.jsonl"

INFERENCE_CONFIG = {
    "num_beams": 4,
    "do_sample": True,
    "temperature": 0.7,
    "top_p": 0.9,
    "num_return_sequences": 3,
    "no_repeat_ngram_size": 4,
    "repetition_penalty": 1.3,
    "max_new_tokens": 48,
    "early_stopping": True,
}

MAX_INPUT_LENGTH = 512

# ─────────────────────────────────────────────────────────────
# 1. PARSING
# ─────────────────────────────────────────────────────────────
def parse_clusters(filepath: str) -> list:
    clusters = []
    current  = None

    header_re = re.compile(
        r"^(Cluster\s+\d+|Autres\s+petites\s+t[aâ]ches)"
        r"\s*\|\s*(\d+)\s+t[aâ]che\(s\)"
        r"\s*\|\s*coh[eé]sion\s*=\s*([\d.]+)",
        re.IGNORECASE,
    )
    item_re = re.compile(r"^\s*[•\-\*]\s+(.+)$")

    with open(filepath, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip()

            m = header_re.search(line)
            if m:
                if current:
                    clusters.append(current)
                current = {
                    "cluster_id": m.group(1).strip(),
                    "num_tasks":  int(m.group(2)),
                    "cohesion":   float(m.group(3)),
                    "items":      [],
                }
                continue

            if current:
                m2 = item_re.match(line)
                if m2:
                    current["items"].append(m2.group(1).strip())

    if current:
        clusters.append(current)

    # Expansion des singletons
    expanded = []
    for c in clusters:
        if re.search(r"autres\s+petites\s+t[aâ]ches", c["cluster_id"], re.IGNORECASE):
            for idx, item in enumerate(c["items"]):
                expanded.append({
                    "cluster_id": f"Autres petites tâches — singleton {idx + 1}",
                    "num_tasks":  1,
                    "cohesion":   c["cohesion"],
                    "items":      [item],
                    "is_singleton": True,
                })
        else:
            c.setdefault("is_singleton", False)
            expanded.append(c)

    return expanded

# ─────────────────────────────────────────────────────────────
# 2. FORMAT INPUT (CRITIQUE FIX)
# ─────────────────────────────────────────────────────────────
def format_prompt(items):
    return "infer user intention: " + json.dumps({
        "task_items": items
    }, ensure_ascii=False)

# ─────────────────────────────────────────────────────────────
# 3. ENRICHMENT (OPTIONNEL MAIS PUISSANT)
# ─────────────────────────────────────────────────────────────
def enrich_items(items):
    text = " ".join(items).lower()

    enriched = list(items)

    if all(x in text for x in ["apt", "remove"]):
        enriched.append("system activity: uninstall software")

    if "pkill" in text:
        enriched.append("system activity: terminate running processes")

    if "grep" in text:
        enriched.append("system activity: analyze logs using pattern matching")

    if "docker" in text:
        enriched.append("system activity: manage containers")

    return enriched

# ─────────────────────────────────────────────────────────────
# 4. VALIDATION SÉMANTIQUE
# ─────────────────────────────────────────────────────────────
def is_semantically_valid(cluster, prediction):
    text = " ".join(cluster).lower()
    pred = prediction.lower()

    # incohérence suppression vs lancement
    if any(x in text for x in ["remove", "rm", "pkill"]):
        if any(x in pred for x in ["launch", "start", "open"]):
            return False

    # incohérence analyse logs
    if "grep" in text:
        if "regex" in pred and "analyze" not in pred:
            return False

    return True

# ─────────────────────────────────────────────────────────────
# 5. CLEAN
# ─────────────────────────────────────────────────────────────
def clean_intention(text):
    text = text.strip().capitalize()
    return text

# ─────────────────────────────────────────────────────────────
# 6. LOAD MODEL
# ─────────────────────────────────────────────────────────────
def load_model(model_path: str):
    path = Path(model_path)
    if not path.exists():
        sys.exit(f"[ERREUR] Modele introuvable : {model_path}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    tokenizer = T5TokenizerFast.from_pretrained(model_path)
    model = T5ForConditionalGeneration.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
    )

    if device == "cpu":
        model.to(device)

    model.eval()
    return model, tokenizer, device

# ─────────────────────────────────────────────────────────────
# 7. PREDICT (AMÉLIORÉ)
# ─────────────────────────────────────────────────────────────
def predict(model, tokenizer, device, items):
    if not items:
        return "(cluster vide)"

    items = enrich_items(items)

    prompt = format_prompt(items)

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=MAX_INPUT_LENGTH,
        truncation=True,
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(**inputs, **INFERENCE_CONFIG)

    candidates = [
        clean_intention(tokenizer.decode(o, skip_special_tokens=True))
        for o in outputs
    ]

    # sélection intelligente
    for c in candidates:
        if is_semantically_valid(items, c):
            return c

    return candidates[0]

# ─────────────────────────────────────────────────────────────
# 8. OUTPUT
# ─────────────────────────────────────────────────────────────
def write_txt(results, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        for c in results:
            f.write(f"{c['cluster_id']}\n")
            f.write(f"Intention: {c['intention']}\n\n")

def write_jsonl(results, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        for i, c in enumerate(results):
            f.write(json.dumps({
                "id": str(i),
                "task_items": c["items"],
                "global_task_intention": c["intention"],
            }, ensure_ascii=False) + "\n")

# ─────────────────────────────────────────────────────────────
# 9. MAIN
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out-txt", default=DEFAULT_OUT_TXT)
    parser.add_argument("--out-jsonl", default=DEFAULT_OUT_JSONL)
    args = parser.parse_args()

    if not Path(args.input).exists():
        sys.exit(f"[ERREUR] Fichier introuvable : {args.input}")

    clusters = parse_clusters(args.input)
    print(f"{len(clusters)} clusters trouvés")

    model, tokenizer, device = load_model(args.model)

    results = []
    for i, cluster in enumerate(clusters):
        intention = predict(model, tokenizer, device, cluster["items"])
        cluster["intention"] = intention
        results.append(cluster)

        print(f"[{i+1}/{len(clusters)}] {intention}")

    write_txt(results, args.out_txt)
    write_jsonl(results, args.out_jsonl)

    print("Terminé.")

if __name__ == "__main__":
    main()