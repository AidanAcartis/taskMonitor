#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

# ─────────────────────────────────────────────
# VERB MAP INITIAL
# ─────────────────────────────────────────────
verb_map_path = "./DICT/VERB_MAP.json"
with open(verb_map_path, "r", encoding="utf-8") as f:
    verb_map = json.load(f)

# ─────────────────────────────────────────────
# AJOUTER LES CONJUGAISONS 3ème PERSONNE
# ─────────────────────────────────────────────
def conjugate_third_person(verb):
    """
    Retourne la conjugaison 3e personne singulier en anglais simple.
    Règles de base (approximation):
    - verb + s
    - verb + es si se termine par s, x, z, ch, sh
    """
    verb = verb.lower()
    if verb.endswith(("s", "x", "z", "ch", "sh")):
        return verb + "es"
    elif verb.endswith("y") and len(verb) > 1 and verb[-2] not in "aeiou":
        return verb[:-1] + "ies"
    else:
        return verb + "s"

# dictionnaire étendu
extended_map = {}

for k, v in verb_map.items():
    extended_map[k] = v
    extended_map[conjugate_third_person(k)] = v

# ─────────────────────────────────────────────
# SAUVEGARDE DU VERB_MAP ÉTENDU
# ─────────────────────────────────────────────
output_path = "./DICT/VERB_MAP_EXTENDED.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(extended_map, f, ensure_ascii=False, indent=2)

print(f"✅ VERB_MAP étendu sauvegardé dans {output_path}")
print("Nombre de verbes :", len(extended_map))