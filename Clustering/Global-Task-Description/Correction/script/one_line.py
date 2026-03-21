import json

input_file = "ID.jsonl"
output_file = "activity_data_restructured.jsonl"

def split_objects(text):
    """Divise le texte en objets JSON séparés par les accolades externes."""
    objs = []
    brace_count = 0
    start = 0
    for i, char in enumerate(text):
        if char == "{":
            if brace_count == 0:
                start = i
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                objs.append(text[start:i+1])
    return objs

with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

json_objects = split_objects(content)

with open(output_file, "w", encoding="utf-8") as f_out:
    for obj_str in json_objects:
        try:
            data = json.loads(obj_str)
            
            f_out.write(json.dumps(data, ensure_ascii=False) + "\n")
        except json.JSONDecodeError as e:
            print("Erreur JSON:", e)