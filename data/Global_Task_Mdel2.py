"""
describe_clusters_plain.py
--------------------------
Lit clusters_output.txt, génère une description globale pour chaque cluster
(sauf 'Autres petites tâches') via le modèle T5 fine-tuné standard,
et réécrit le fichier avec les descriptions ajoutées.

Usage
-----
    python describe_clusters_plain.py
"""

import re
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
INPUT_FILE   = "clusters_output.txt"
OUTPUT_FILE  = "DESCRIBE_clusters_output.txt"
AUTRES_LABEL = "Autres petites tâches"
PLAIN_PATH   = "./checkpoint-600"
DEVICE       = "cuda" if torch.cuda.is_available() else "cpu"

CONFIG = {
    "prefix"           : "What is the user's main goal based on these actions: ",
    "separator"        : " | ",
    "max_input_length" : 512,
    "max_target_length": 64,
}


# ─────────────────────────────────────────────
# ÉTAPE 1 — Parsing de clusters_output.txt
# ─────────────────────────────────────────────
def parse_clusters(filepath: str) -> list[dict]:
    clusters = []
    current  = None

    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("─"):
            i += 1
            if i < len(lines):
                header = lines[i].rstrip()
                i += 1
                if i < len(lines) and lines[i].rstrip().startswith("─"):
                    i += 1

                coh_match = re.search(r"cohésion\s*=\s*([\d.]+)", header)
                cohesion  = float(coh_match.group(1)) if coh_match else 0.0
                label     = header.split("|")[0].strip()

                current = {
                    "label":    label,
                    "cohesion": cohesion,
                    "items":    [],
                }
                clusters.append(current)

        elif line.startswith("  •") and current is not None:
            item = line.lstrip("  •").strip()
            current["items"].append(item)
            i += 1
        else:
            i += 1

    return clusters


# ─────────────────────────────────────────────
# ÉTAPE 2 — Chargement du modèle
# ─────────────────────────────────────────────
print("=" * 60)
print("describe_clusters_plain.py")
print("=" * 60)

print(f"\n[1] Chargement du modèle depuis {PLAIN_PATH} ...")
tokenizer = T5Tokenizer.from_pretrained(PLAIN_PATH)
model     = T5ForConditionalGeneration.from_pretrained(PLAIN_PATH)
model     = model.to(DEVICE)
model.eval()
print(f"    Modèle chargé. Device : {DEVICE}")


# ─────────────────────────────────────────────
# ÉTAPE 3 — Preprocessing
# ─────────────────────────────────────────────
def normalize_syntax(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = text.replace('\\"', '"').replace('"', '')
    text = re.sub(r'[\u200b\u200e\u200f]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_paths(text: str) -> str:
    return re.sub(r"(/\S+)+", "<PATH>", text)


def preprocess_items(items: list[str]) -> list[str]:
    return [normalize_paths(normalize_syntax(item)) for item in items]


# ─────────────────────────────────────────────
# ÉTAPE 4 — Génération (identique au notebook)
# ─────────────────────────────────────────────
def predict(task_items: list[str]) -> str:
    task_text  = CONFIG["separator"].join(task_items)
    input_text = CONFIG["prefix"] + task_text

    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        max_length=CONFIG["max_input_length"],
        truncation=True,
    ).to(DEVICE)

    with torch.no_grad():
        outputs = model.generate(
            inputs["input_ids"],
            max_length           = CONFIG["max_target_length"],
            num_beams            = 5,
            length_penalty       = 1.0,
            early_stopping       = True,
            no_repeat_ngram_size = 2,
        )

    return tokenizer.decode(outputs[0], skip_special_tokens=True).strip()


# ─────────────────────────────────────────────
# ÉTAPE 5 — Traitement de chaque cluster
# ─────────────────────────────────────────────
print(f"\n[2] Parsing de {INPUT_FILE} ...")
clusters = parse_clusters(INPUT_FILE)
print(f"    {len(clusters)} cluster(s) trouvé(s).")

print("\n[3] Génération des descriptions globales ...")

for i, cluster in enumerate(clusters):
    label = cluster["label"]

    if label == AUTRES_LABEL:
        cluster["global_desc"] = None
        print(f"    [{i+1}/{len(clusters)}] '{label}' → ignoré.")
        continue

    preprocessed           = preprocess_items(cluster["items"])
    desc                   = predict(preprocessed)
    cluster["global_desc"] = desc
    print(f"    [{i+1}/{len(clusters)}] '{label}' → {desc}")


# ─────────────────────────────────────────────
# ÉTAPE 6 — Réécriture du rapport
# ─────────────────────────────────────────────
print(f"\n[4] Réécriture du rapport dans {OUTPUT_FILE} ...")

with open(INPUT_FILE, encoding="utf-8") as f:
    original_lines = f.readlines()

# En-tête (avant le premier ─)
header_lines = []
for line in original_lines:
    if line.startswith("─"):
        break
    header_lines.append(line.rstrip())

# Footer (═ et FIN DU RAPPORT)
footer_lines = []
for line in reversed(original_lines):
    stripped = line.rstrip()
    if stripped.startswith("═") or "FIN DU RAPPORT" in stripped:
        footer_lines.insert(0, stripped)
    elif footer_lines:
        break

# Reconstruire
output_lines = header_lines + [""]

for cluster in clusters:
    label    = cluster["label"]
    cohesion = cluster["cohesion"]
    items    = cluster["items"]
    desc     = cluster.get("global_desc")
    n        = len(items)

    output_lines.append("─" * 60)
    output_lines.append(f"{label}  |  {n} tâche(s)  |  cohésion = {cohesion:.3f}")
    output_lines.append("─" * 60)

    if desc:
        output_lines.append(f"  ➤ {desc}")
        output_lines.append("")

    for item in items:
        output_lines.append(f"  • {item}")
    output_lines.append("")

output_lines += footer_lines

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"\n✅ Rapport mis à jour : {OUTPUT_FILE}")
print(f"   {sum(1 for c in clusters if c['global_desc'])} cluster(s) décrits.")