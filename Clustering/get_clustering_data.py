import json

# Fichiers sources
files_jsonl = "data_train_file.jsonl"
commands_jsonl = "commands_descriptions_1.jsonl"

# Fichier de sortie
output_jsonl = "merged_descriptions.jsonl"

output_data = []

# Lire les descriptions des fichiers
with open(files_jsonl, "r", encoding="utf-8") as f_files:
    for line in f_files:
        obj = json.loads(line.strip())
        output_data.append({
            "id": obj["id"],
            "descriptions": [obj["description"]]
        })

# Lire les descriptions des commandes
with open(commands_jsonl, "r", encoding="utf-8") as f_cmds:
    for idx, line in enumerate(f_cmds):
        obj = json.loads(line.strip())
        # On peut utiliser idx + len(output_data) pour avoir un id unique si nécessaire
        output_data.append({
            "id": str(idx + len(output_data)),
            "descriptions": obj["descriptions"]
        })

# Écrire le fichier JSONL final
with open(output_jsonl, "w", encoding="utf-8") as f_out:
    for item in output_data:
        f_out.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"Fichier généré: {output_jsonl}, {len(output_data)} entrées")
