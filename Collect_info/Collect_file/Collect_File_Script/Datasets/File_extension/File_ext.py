import json
import os

# Load the dictionnary
with open("mime_map.json", "r", encoding="utf-8") as f:
    MIME_MAP = json.load(f)

def guess_type(filename: str):
    """
    Return the comment related to the file's extension
    """
    _,ext = os.path.splitext(filename.lower())
    
    if not ext:  # cas sans extension
        return "file"
    
    data = MIME_MAP.get(ext)
    if data:
        return data.get("comment")
    return None

INPUT_FILE = "Files_ext.jsonl"
OUTPUT_FILE = "Files_ext_with_comments.jsonl"

with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
     open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
    
    for line in infile:
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        filename = item.get("file", "")
        ext_def = guess_type(filename)
        new_item = {
            "id": item.get("id"),
            "file": filename,
            "ext_def": ext_def
        }
        outfile.write(json.dumps(new_item, ensure_ascii=False) + "\n")

print(f"Processing complete. Results saved to {OUTPUT_FILE}")

