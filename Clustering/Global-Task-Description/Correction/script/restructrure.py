"""
restructure.py
--------------
Lit activity_data_corrected.jsonl (réponses brutes scrapées),
extrait le JSON de chaque raw_response,
et écrit le résultat propre dans activity_data_final.jsonl.
"""

import json
import re

INPUT_FILE  = "activity_data_corrected.jsonl"
OUTPUT_FILE = "activity_data_structured.jsonl"


def extract_json(raw: str) -> dict | None:
    """
    Extrait le premier objet JSON valide depuis une chaîne brute.
    Gère les préfixes comme "JSON {", "```json {", etc.
    """
    # Retirer les préfixes courants
    raw = re.sub(r"^(JSON\s*|```json\s*|```\s*)", "", raw.strip(), flags=re.IGNORECASE)
    raw = re.sub(r"```\s*$", "", raw.strip())

    # Trouver le premier { et le dernier }
    start = raw.find("{")
    end   = raw.rfind("}")
    if start == -1 or end == -1:
        return None

    json_str = raw[start:end+1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Tentative de nettoyage : retirer les espaces multiples
        json_str = re.sub(r"\s+", " ", json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None


# ─────────────────────────────────────────────
# Traitement
# ─────────────────────────────────────────────
ok      = 0
skipped = 0

with open(INPUT_FILE, "r", encoding="utf-8") as f_in, \
     open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:

    for line_idx, line in enumerate(f_in, 1):
        line = line.strip()
        if not line:
            continue

        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            print(f"[{line_idx}] ❌ Ligne non parsable, ignorée.")
            skipped += 1
            continue

        raw_response = entry.get("raw_response", "")
        parsed       = extract_json(raw_response)

        if parsed is None:
            print(f"[{line_idx}] ❌ JSON introuvable dans raw_response (original_id={entry.get('original_id')})")
            skipped += 1
            continue

        # Vérifier les champs requis
        if "task_items" not in parsed or "global_task_intention" not in parsed:
            print(f"[{line_idx}] ⚠️  Champs manquants (original_id={entry.get('original_id')}): {list(parsed.keys())}")
            skipped += 1
            continue

        # Construire la ligne finale
        final = {
            "id"                  : parsed.get("id", entry.get("original_id", str(line_idx))),
            "task_items"          : parsed["task_items"],
            "global_task_intention": parsed["global_task_intention"],
        }

        f_out.write(json.dumps(final, ensure_ascii=False) + "\n")
        ok += 1

print(f"\n✅ {ok} lignes restructurées → {OUTPUT_FILE}")
print(f"   {skipped} lignes ignorées.")