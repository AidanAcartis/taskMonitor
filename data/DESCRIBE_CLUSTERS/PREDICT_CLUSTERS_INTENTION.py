#!/usr/bin/env python3
"""
============================================================
  Cluster Global Task Intention Predictor
  Usage: python predict_cluster_intentions.py [--input FILE] [--model PATH]
============================================================

Entrée  : clusters_output.txt  (rapport de clustering formaté)
Modèle  : kaggle/working/flan-t5-task-intention/final_model/
Sorties : clusters_with_intentions.txt   — rapport lisible
          clusters_with_intentions.jsonl — format structuré
============================================================
"""

import re
import json
import sys
import argparse
from pathlib import Path
import os

import torch
from transformers import T5ForConditionalGeneration, T5TokenizerFast


# ─────────────────────────────────────────────────────────────
# CONFIG  — modifie ces valeurs selon ton environnement
# ─────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(__file__)

DEFAULT_INPUT     = os.path.join(BASE_DIR, "../CLUSTERING/clusters_output.txt")
DEFAULT_MODEL     = os.path.join(BASE_DIR, "../../../Vis_Models/final_Model_V3/final_model")
DEFAULT_OUT_TXT   = os.path.join(BASE_DIR, "clusters_with_intentions.txt")
DEFAULT_OUT_JSONL = os.path.join(BASE_DIR, "clusters_with_intentions.jsonl")

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

VERB_MAP = load_json(os.path.join(BASE_DIR, "../DICT/VERB_MAP_EXTENDED.json"))
VERB_MAP = {k.lower(): v.lower() for k, v in VERB_MAP.items()}

# Identique aux hyperparamètres d'inférence utilisés à l'entraînement
INFERENCE_CONFIG = {
    "num_beams":            4,
    "no_repeat_ngram_size": 4,
    "repetition_penalty":   1.3,
    "max_new_tokens":       48,
    "early_stopping":       True,
}

MAX_INPUT_LENGTH = 448   # même valeur que CONFIG["max_input_length"]


# ─────────────────────────────────────────────────────────────
# 1. PARSING  clusters_output.txt
# ─────────────────────────────────────────────────────────────
def parse_clusters(filepath: str) -> list:
    """
    Lit le rapport de clustering et retourne une liste de dicts :
        {
            "cluster_id" : str,   ex. "Cluster 0" / "Autres petites tâches"
            "num_tasks"  : int,
            "cohesion"   : float,
            "items"      : [str, ...]   # items déjà formatés dans le fichier
        }

    Format attendu dans le fichier :
        Cluster N  |  K tâche(s)  |  cohésion = X.XXX
        Autres petites tâches  |  K tâche(s)  |  cohésion = X.XXX
    suivi de lignes "  • <item>"
    """
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

    # ── Éclater "Autres petites tâches" en singletons ────────
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
# 2. FORMATAGE DU PROMPT
#    Identique au format utilisé pendant l'entraînement
# ─────────────────────────────────────────────────────────────
def format_prompt(items):
    items_text = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(items))
    return (
        "Based on the following list of task items, "
        "generate a concise global task intention in one sentence:\n"
        f"{items_text}"
    )


# ─────────────────────────────────────────────────────────────
# 3. CHARGEMENT DU MODÈLE
# ─────────────────────────────────────────────────────────────
def load_model(model_path: str):
    path = Path(model_path)
    if not path.exists():
        sys.exit(
            f"\n[ERREUR] Modèle introuvable : {model_path}\n"
            "  → Vérifie DEFAULT_MODEL ou utilise --model <chemin>\n"
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Device : {device}")
    if device == "cuda":
        print(f"  GPU    : {torch.cuda.get_device_name(0)}")
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"  VRAM   : {vram:.1f} GB")

    print(f"  Chargement depuis : {model_path}")
    tokenizer = T5TokenizerFast.from_pretrained(model_path)
    model = T5ForConditionalGeneration.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
    )
    if device == "cpu":
        model.to(device)
    model.eval()
    print("  Modele pret\n")

    return model, tokenizer, device

# ─────────────────────────────────────────────
# SIMPLE ACTION EXTRACTION (pour singletons)
# ─────────────────────────────────────────────


STOP_WORDS = {
    "of", "to", "for", "with", "in", "on", "at", "from",
    "by", "about", "as", "into", "after", "before"
}

COMMON_VERBS = {
    "create", "run", "execute", "install", "remove", "update",
    "send", "open", "read", "write", "build", "compile",
    "check", "verify", "record", "display", "launch",
    "render", "provide", "handle", "manage", "analyze",
    "list", "clear", "exit", "play", "search"
}

def clean_segment(seg):
    seg = seg.lower().strip()
    seg = re.sub(
        r"(command used to|used to|used for|used in|opened with|written in|executed in)",
        "",
        seg
    )
    return seg.strip()

def detect_verb(word):
    if word in VERB_MAP:
        return VERB_MAP[word]
    if word in COMMON_VERBS:
        return word
    return None

def extract_action(item):
    parts = [p.strip() for p in item.split(",") if p.strip()]

    INVALID_STARTS = {
        "text", "data", "file", "application", "plain", "script", "document"
    }

    # ── 1. PRIORITÉ : segments avec "used to"
    for part in parts:
        if "used to" in part:
            segment = clean_segment(part)
            words = segment.split()

            if not words:
                continue

            # 🔥 ignorer bruit
            if words[0] in INVALID_STARTS:
                continue

            verb = detect_verb(words[0])
            if not verb:
                continue

            obj_words = []
            for w in words[1:]:
                if w in STOP_WORDS:
                    break
                obj_words.append(w)

            return verb + (" " + " ".join(obj_words) if obj_words else "")

    # ── 2. FALLBACK : mais filtré
    for part in reversed(parts):
        segment = clean_segment(part)
        words = segment.split()

        if not words:
            continue

        # 🔥 ignorer bruit direct
        if words[0] in INVALID_STARTS:
            continue

        verb = detect_verb(words[0])
        if not verb:
            continue

        obj_words = []
        for w in words[1:]:
            if w in STOP_WORDS:
                break
            obj_words.append(w)

        return verb + (" " + " ".join(obj_words) if obj_words else "")

    return None


def generate_simple_intention(item: str) -> str:
    item_lower = item.lower()
    obj = item.split(",")[0].strip()
    obj_lower = obj.lower()

    # ─────────────────────────────────────────────
    # 🔥 1. PRIORITÉ MAX — FILE OPENED WITH APP
    # ─────────────────────────────────────────────
    if "file" in item_lower and "opened with" in item_lower:
        match = re.search(r"opened with ([^,]+)", item_lower)
        if match:
            app = match.group(1).strip().title()
            return f"open {obj} with {app}"

    # ─────────────────────────────────────────────
    # 🔥 2. EXTRACTION ACTION
    # ─────────────────────────────────────────────
    action = extract_action(item)

    # ─────────────────────────────────────────────
    # 🔥 3. FILTRE ANTI-BRUIT
    # ─────────────────────────────────────────────
    INVALID_ACTIONS = {
        "text files", "plain text", "data related", "file",
        "application log", "script", "document"
    }

    if action and action.lower() in INVALID_ACTIONS:
        action = None

    # ─────────────────────────────────────────────
    # 🔥 4. ENRICHIR + ANTI-REPEAT
    # ─────────────────────────────────────────────
    if action:
        words = action.split()

        # Cas : verbe seul
        if len(words) == 1:
            verb = words[0]

            # éviter : "exit exit"
            if verb == obj_lower:
                return verb

            return f"{verb} {obj_lower}"

        return action

    # ─────────────────────────────────────────────
    # 🔥 5. FALLBACKS INTELLIGENTS
    # ─────────────────────────────────────────────

    # CAS APPLICATION
    if "application" in item_lower:
        if "desktop" in item_lower:
            return f"manage {obj_lower}"
        return f"use {obj_lower}"

    # CAS FILE
    if "file" in item_lower:
        return f"open {obj_lower}"

    # CAS COMMAND
    if "command" in item_lower:
        return f"run {obj_lower}"

    # ─────────────────────────────────────────────
    # 🔥 6. ULTIME FALLBACK
    # ─────────────────────────────────────────────
    return obj_lower


# ─────────────────────────────────────────────────────────────
# 4. INFÉRENCE
# ─────────────────────────────────────────────────────────────
def predict(model, tokenizer, device, items):
    if not items:
        return "(cluster vide — pas de prediction)"

    prompt = format_prompt(items)
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=MAX_INPUT_LENGTH,
        truncation=True,
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(**inputs, **INFERENCE_CONFIG)

    return tokenizer.decode(outputs[0], skip_special_tokens=True)


# ─────────────────────────────────────────────────────────────
# 5. ÉCRITURE DES SORTIES
# ─────────────────────────────────────────────────────────────
SEP  = "=" * 65
DASH = "─" * 65


def write_txt(results, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{SEP}\n")
        f.write("  CLUSTERS — GLOBAL TASK INTENTIONS\n")
        f.write(f"{SEP}\n\n")

        for c in results:
            f.write(f"{DASH}\n")
            label = (
                f"{c['cluster_id']}  |  singleton"
                if c.get("is_singleton") else
                f"{c['cluster_id']}  |  {c['num_tasks']} tache(s)  |  cohesion = {c['cohesion']:.3f}"
            )
            f.write(f"{label}\n")
            f.write(f"{DASH}\n")
            f.write(f"  Global Task Intention : {c['intention']}\n\n")
            f.write("  Items :\n")
            for item in c["items"]:
                f.write(f"    - {item}\n")
            f.write("\n")

        f.write(f"{SEP}\n")
        f.write("  FIN DU RAPPORT\n")
        f.write(f"{SEP}\n")


def write_jsonl(results, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        for i, c in enumerate(results):
            record = {
                "id":                    str(i),
                "cluster_id":            c["cluster_id"],
                "num_tasks":             c["num_tasks"],
                "cohesion":              c["cohesion"],
                "task_items":            c["items"],
                "global_task_intention": c["intention"],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ─────────────────────────────────────────────────────────────
# 6. MAIN
# ─────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Genere une global task intention pour chaque cluster."
    )
    parser.add_argument(
        "--input",     default=DEFAULT_INPUT,
        help=f"Fichier de clusters en entree (defaut : {DEFAULT_INPUT})"
    )
    parser.add_argument(
        "--model",     default=DEFAULT_MODEL,
        help=f"Chemin vers le modele Flan-T5 fine-tune (defaut : {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--out-txt",   default=DEFAULT_OUT_TXT,
        help=f"Fichier texte de sortie (defaut : {DEFAULT_OUT_TXT})"
    )
    parser.add_argument(
        "--out-jsonl", default=DEFAULT_OUT_JSONL,
        help=f"Fichier JSONL de sortie (defaut : {DEFAULT_OUT_JSONL})"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"\n{'='*65}")
    print("  CLUSTER GLOBAL TASK INTENTION PREDICTOR")
    print(f"{'='*65}\n")

    # ── 1. Parse ──────────────────────────────────────────────
    print(f"Lecture : {args.input}")
    if not Path(args.input).exists():
        sys.exit(
            f"\n[ERREUR] Fichier introuvable : {args.input}\n"
            "  Verifie DEFAULT_INPUT ou utilise --input <chemin>\n"
        )

    clusters = parse_clusters(args.input)
    if not clusters:
        sys.exit(
            "\n[ERREUR] Aucun cluster trouve.\n"
            "  Verifie que le format du fichier correspond au rapport de clustering.\n"
        )
    print(f"  {len(clusters)} clusters trouves\n")

    # ── 2. Modèle ─────────────────────────────────────────────
    print("Chargement du modele...")
    model, tokenizer, device = load_model(args.model)

    # ── 3. Inférence ──────────────────────────────────────────
    print(f"Inference ({len(clusters)} clusters)...\n")
    print(f"{'─'*65}")

    results = []
    for i, cluster in enumerate(clusters):

        # ── CAS 1 : singleton → PAS DE MODELE ───────────────
        if cluster.get("is_singleton"):
            item = cluster["items"][0]
            intention = generate_simple_intention(item)

        # ── CAS 2 : cluster normal → MODELE ────────────────
        else:
            intention = predict(model, tokenizer, device, cluster["items"])

        cluster["intention"] = intention
        results.append(cluster)

        print(f"[{i+1:02d}/{len(clusters)}] {cluster['cluster_id']}")
        print(f"         {len(cluster['items'])} item(s) | cohesion = {cluster['cohesion']:.3f}")
        print(f"         -> {intention}\n")

    print(f"{'─'*65}\n")

    # ── 4. Écriture ───────────────────────────────────────────
    write_txt(results,   args.out_txt)
    write_jsonl(results, args.out_jsonl)

    print(f"Sorties generees :")
    print(f"  {args.out_txt}")
    print(f"  {args.out_jsonl}")
    print(f"\n{'='*65}\n")


if __name__ == "__main__":
    main()