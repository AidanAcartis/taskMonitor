import json
import os

# === Chemins ===
files_ext_path = "./File_extension/Files_ext.jsonl"
data_path = "./data_file/data_train_file.jsonl"
output_path = "./data_train_file_with_filename_1.jsonl"

# vérification des fichiers
for path in [files_ext_path, data_path]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fichier introuvable : {path}")

# lecture du fichier contenant les noms de fichiers
file_map = {}
with open(files_ext_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        if "id" in entry and "file" in entry:
            file_map[entry["id"]] = entry["file"]

# lecture du dataset principal et insertion du champ "file" après "id"
with open(data_path, "r", encoding="utf-8") as f_in, open(output_path, "w", encoding="utf-8") as f_out:
    for line in f_in:
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        file_value = file_map.get(data["id"], "unknown")

        new_data = {"id": data["id"], "file": file_value}
        for k, v in data.items():
            if k != "id":
                new_data[k] = v

        json.dump(new_data, f_out, ensure_ascii=False)
        f_out.write("\n")

print(f"Fichier créé avec succès : {output_path}")
