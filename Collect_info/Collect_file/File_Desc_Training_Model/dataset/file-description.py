import json
import os

input_file = "../Get_data_process/File_scrap_desc/response.jsonl"
output_file = "./file_desc_data/file_description.jsonl"

with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    for line in f_in:
        entry = json.loads(line.strip())
        obj = {
            "id": entry["id"],
            "filename": entry["filename"],
            "file_desc": entry["description"]
        }
        f_out.write(json.dumps(obj, ensure_ascii=False) + "\n")

print(f"file_description created on {output_file}")
