import json
import os

input_file = "Files_list.txt"
output_file = "Files_list.jsonl"

# Lire le JSON existant pour savoir jusqu'où on est
existing_ids = set()
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                existing_ids.add(int(obj["id"]))
            except:
                pass

# On continue à partir du numéro 36 dans Files_list.txt
with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "a", encoding="utf-8") as f_out:
    for line in f_in:
        parts = line.strip().split(maxsplit=1)
        if len(parts) < 2:
            continue

        idx = int(parts[0])
        if idx < 36:  # Ignorer les lignes déjà présentes dans le JSON
            continue

        content = parts[1]

        # Découper en filename - directory - application
        subparts = content.split(" - ")
        if len(subparts) != 3:
            continue

        filename_full, directory, application = subparts

        # Séparer nom et extension
        filename, extension = os.path.splitext(filename_full)
        extension = extension.lstrip(".")

        obj = {
            "id": str(idx),  # on garde le même numéro que dans Files_list.txt
            "filename": filename,
            "extension": extension,
            "directory": directory,
            "application": application
        }

        f_out.write(json.dumps(obj, ensure_ascii=False) + "\n")

print(f"JSON mis à jour dans {output_file}, à partir du numéro 36 de Files_list.txt")
