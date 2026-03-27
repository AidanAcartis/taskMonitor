#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nettoyage des objets inutiles dans DATA_V4_ABSTRACTION.jsonl

- Supprime les objets génériques (app, command, etc.)
- Supprime les objets trop vagues (data transfer, text files, etc.)
- Garde uniquement les objets à forte valeur sémantique
"""

import json
from pathlib import Path

INPUT_FILE  = "DATA_V4_ABSTRACTION.jsonl"
OUTPUT_FILE = "DATA_V4_ABSTRACTION_CLEAN.jsonl"

# 🔥 Objets génériques (déjà identifiés)
GENERIC_OBJECTS = {
    "app", "application", "command", "command line",
    "command tool", "tool", "software", "program"
}

# 🔥 Objets bruités / non discriminants
NOISE_OBJECTS = {
    "data transfer",
    "data exchange format",
    "other files",
    "text files",
    "files",
    "documents",
    "image files",
    "text format"
}

# 🔥 Fusion
REMOVE_OBJECTS = GENERIC_OBJECTS | NOISE_OBJECTS

# Vérification fichier
if not Path(INPUT_FILE).exists():
    print(f"❌ File not found: {INPUT_FILE}")
    exit(1)

cleaned_entries = []

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)

        objects = data.get("semantic_features", {}).get("objects", [])

        # 🧹 Nettoyage
        filtered_objects = [
            o for o in objects
            if o not in REMOVE_OBJECTS
        ]

        # (Optionnel mais conseillé) supprimer doublons + tri
        filtered_objects = sorted(set(filtered_objects))

        # Mise à jour
        data["semantic_features"]["objects"] = filtered_objects

        cleaned_entries.append(data)

# 💾 Sauvegarde
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for entry in cleaned_entries:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

print(f"✅ Done. Cleaned file saved to: {OUTPUT_FILE}")