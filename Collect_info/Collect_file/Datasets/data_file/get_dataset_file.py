import json

# Input files
file_ext = "../File_extension/Files_ext_with_comments.jsonl"   # contains id, file, ext_def
file_desc = "../File_desc/file_description.jsonl"             # contains id, filename, file_desc
file_dir_app = "../File_scrap_desc/response.jsonl"            # contains id, filename, extension, directory, application, description

# Output file
output_file = "data_train_file.jsonl"

# Load files into dictionaries indexed by id
def load_jsonl(path):
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line.strip())
            data[obj["id"]] = obj
    return data

ext_data = load_jsonl(file_ext)
desc_data = load_jsonl(file_desc)
dir_app_data = load_jsonl(file_dir_app)

# Merge
with open(output_file, "w", encoding="utf-8") as f_out:
    for id_, ext_entry in ext_data.items():
        merged = {
            "id": id_,
            "extension_def": ext_entry.get("ext_def"),
            "filename_desc": desc_data.get(id_, {}).get("file_desc"),
            "directory": dir_app_data.get(id_, {}).get("directory"),
            "app": dir_app_data.get(id_, {}).get("application"),
            "description": dir_app_data.get(id_, {}).get("description"),
        }
        f_out.write(json.dumps(merged, ensure_ascii=False) + "\n")

print(f"data_train_file.jsonl created successfully : {output_file}")
