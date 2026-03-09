import json
import os

input_file = "Files_list.txt"
output_file = "Files_list.jsonl"

with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    for line in f_in:
        parts = line.strip().split(maxsplit=1)
        if len(parts) < 2:
            continue

        idx = parts[0]
        content = parts[1]

        #Slice into filename - directory - application
        subparts = content.split(" - ")
        if len(subparts) != 3:
            continue

        filename_full, directory, application = subparts

        #Separate the name and the extension
        filename, extension = os.path.splitext(filename_full)
        extension = extension.lstrip(".") #Leave the point
        
        obj = {
            "id": str(int(idx) - 1),
            "filename": filename,
            "extension": extension,
            "directory": directory,
            "application": application
        }

        f_out.write(json.dumps(obj, ensure_ascii=False) + "\n")

print(f"JSON created in {output_file}")