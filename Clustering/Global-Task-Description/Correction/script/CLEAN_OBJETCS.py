#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nettoyer les objets génériques dans activity_data_semantic.jsonl
Seuls les objets dans GENERIC_OBJECTS seront supprimés
s'ils apparaissent comme éléments indépendants.
"""

import json
from pathlib import Path

INPUT_FILE  = "activity_data_semantic.jsonl"
OUTPUT_FILE = "activity_data_semantic_clean.jsonl"

# Objets génériques à supprimer si présents seuls
GENERIC_OBJECTS = {
    "app", "application", "command", "command line",
    "command tool", "tool", "software", "program"
}

if not Path(INPUT_FILE).exists():
    print(f"❌ File not found: {INPUT_FILE}")
    exit(1)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

cleaned_entries = []

for line in lines:
    data = json.loads(line)
    objects = data.get("semantic_features", {}).get("objects", [])

    # Supprimer uniquement les objets qui sont strictement dans GENERIC_OBJECTS
    filtered_objects = [o for o in objects if o not in GENERIC_OBJECTS]

    # Mise à jour
    data["semantic_features"]["objects"] = filtered_objects
    cleaned_entries.append(data)

# Sauvegarde
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for entry in cleaned_entries:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

print(f"✅ Done. Saved cleaned file to {OUTPUT_FILE}")