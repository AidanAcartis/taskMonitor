#!/usr/bin/env python3
"""
============================================================
  Cluster Global Task Intention Predictor - V5 (Action-Focus)
============================================================
"""

import re
import json
import sys
import argparse
import platform
import getpass
from pathlib import Path

import torch
from transformers import T5ForConditionalGeneration, T5TokenizerFast

# ─────────────────────────────────────────────────────────────
# CONFIGURATION V5
# ─────────────────────────────────────────────────────────────
DEFAULT_INPUT     = "clusters_output.txt"
DEFAULT_MODEL     = "./final_Model_V3/final_model"
DEFAULT_OUT_TXT   = "clusters_with_intentions_Ge.txt"
DEFAULT_OUT_JSONL = "clusters_with_intentions_Ge.jsonl"

# Optimisation des paramètres pour éviter les hallucinations (ex: Virtual Machine)
INFERENCE_CONFIG = {
    "num_beams":            5,
    "no_repeat_ngram_size": 3,
    "repetition_penalty":   1.1, # Réduit pour être moins agressif sur le texte
    "max_new_tokens":       40,
    "early_stopping":       True,
    "temperature":          0.7,
    "do_sample":            False # On reste sur du Beam Search pour la précision
}

MAX_INPUT_LENGTH = 512

# ─────────────────────────────────────────────────────────────
# 1. PARSING (Inchangé, robuste)
# ─────────────────────────────────────────────────────────────
def parse_clusters(filepath: str) -> list:
    clusters = []
    current  = None
    header_re = re.compile(r"^(Cluster\s+\d+|Autres\s+petites\s+t[aâ]ches)\s*\|\s*(\d+)\s+t[aâ]che\(s\)\s*\|\s*coh[eé]sion\s*=\s*([\d.]+)", re.IGNORECASE)
    item_re = re.compile(r"^\s*[•\-\*]\s+(.+)$")

    with open(filepath, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip()
            m = header_re.search(line)
            if m:
                if current: clusters.append(current)
                current = {"cluster_id": m.group(1).strip(), "num_tasks": int(m.group(2)), "cohesion": float(m.group(3)), "items": []}
                continue
            if current:
                m2 = item_re.match(line)
                if m2: current["items"].append(m2.group(1).strip())
    if current: clusters.append(current)
    
    expanded = []
    for c in clusters:
        if "autres" in c["cluster_id"].lower():
            for idx, item in enumerate(c["items"]):
                expanded.append({"cluster_id": f"Singleton {idx+1}", "num_tasks": 1, "cohesion": c["cohesion"], "items": [item], "is_singleton": True})
        else:
            c["is_singleton"] = False
            expanded.append(c)
    return expanded

# ─────────────────────────────────────────────────────────────
# 2. FORMATAGE V5 (ACTION-DRIVEN)
# ─────────────────────────────────────────────────────────────
def format_prompt_v5(items):
    os_name = platform.system()
    user_name = getpass.getuser()
    items_text = "\n".join(f"- {item}" for item in items)
    
    # On force le modèle à agir comme un analyste système
    return (
        f"Context: {os_name} terminal, User: {user_name}.\n"
        "Task: Analyze the following command line items and identify the SINGLE most accurate "
        "common technical action (e.g., Manage, Edit, Monitor, Delete, Configure) and its target object.\n"
        f"Items:\n{items_text}\n"
        "Intention: [Action] [Target]"
    )

def clean_intention_v5(text):
    """
    Nettoyage chirurgical des erreurs persistantes identifiées en V4.
    """
    # 1. Correction du biais Microsoft (OS vs GUI)
    text = re.sub(r"\bWindows\b", "graphical windows", text, flags=re.IGNORECASE)
    
    # 2. Suppression des hallucinations de contexte type 'Virtual Machine'
    text = re.sub(r"in (a )?virtual machine", "", text, flags=re.IGNORECASE)
    
    # 3. Correction des verbes de paquets (Apt/Pkill -> Manage/Remove, pas Launch)
    if any(word in text.lower() for word in ["browser", "chrome", "firefox"]):
        if any(word in text.lower() for word in ["remove", "kill", "purge"]):
            text = text.replace("Launch", "Manage and remove")
            
    # 4. Correction des logs (Cluster 0)
    if "log file" in text.lower() or "window_changes" in text.lower():
        text = text.replace("Change", "Analyze logs of")

    return text.strip().capitalize()

# ─────────────────────────────────────────────────────────────
# 3. CHARGEMENT ET INFÉRENCE
# ─────────────────────────────────────────────────────────────
def load_model(model_path: str):
    tokenizer = T5TokenizerFast.from_pretrained(model_path)
    model = T5ForConditionalGeneration.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None
    )
    return model, tokenizer, "cuda" if torch.cuda.is_available() else "cpu"

def predict(model, tokenizer, device, items):
    prompt = format_prompt_v5(items)
    inputs = tokenizer(prompt, return_tensors="pt", max_length=MAX_INPUT_LENGTH, truncation=True).to(device)
    
    with torch.no_grad():
        outputs = model.generate(**inputs, **INFERENCE_CONFIG)
        
    res = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return clean_intention_v5(res)

# ─────────────────────────────────────────────────────────────
# 4. MAIN & EXPORT
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    print(f"\n--- Running V5: Action-Focus Prediction ---")
    
    if not Path(args.input).exists():
        sys.exit(f"Erreur: {args.input} introuvable.")

    clusters = parse_clusters(args.input)
    model, tokenizer, device = load_model(args.model)

    results = []
    for i, cluster in enumerate(clusters):
        intention = predict(model, tokenizer, device, cluster["items"])
        cluster["intention"] = intention
        results.append(cluster)
        print(f"[{i+1}/{len(clusters)}] {cluster['cluster_id']} -> {intention}")

    # Export TXT
    with open(DEFAULT_OUT_TXT, "w", encoding="utf-8") as f:
        for c in results:
            f.write(f"Cluster: {c['cluster_id']}\nIntention: {c['intention']}\n")
            f.write("Items:\n" + "\n".join(f"  - {it}" for it in c['items']) + "\n\n")

    print(f"\n✅ Rapport V5 généré dans {DEFAULT_OUT_TXT}")

if __name__ == "__main__":
    main()