import os
import json

# Chemins
TLDR_PATH = os.path.expanduser("~/.local/share/tldr/pages.en")
OUTPUT_DIR = os.path.expanduser("./dict_json")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_text(text):
    """Nettoie les espaces et backticks autour"""
    return text.strip().strip('`').replace('\n', ' ')

# Parcours des sous-dossiers
for folder_name in os.listdir(TLDR_PATH):
    folder_path = os.path.join(TLDR_PATH, folder_name)
    if not os.path.isdir(folder_path):
        continue

    output_file = os.path.join(OUTPUT_DIR, f"{folder_name}.json")
    folder_dict = {}

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if not file.endswith(".md"):
                continue

            filepath = os.path.join(root, file)
            # Nom du fichier sans extension comme titre
            title = os.path.splitext(file)[0]
            folder_dict[title] = []

            with open(filepath, "r", encoding="utf-8") as f:
                lines = [l.rstrip() for l in f]

            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Exemple : ligne qui commence par '- ' et finit par ':'
                if line.startswith("- ") and line.endswith(":"):
                    example_desc = line[2:].rstrip(":").strip()

                    # Cherche la prochaine ligne non vide qui contient la commande
                    j = i + 1
                    example_cmd = None
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if next_line == "":
                            j += 1
                            continue
                        # La ligne suivante non vide est considérée comme la commande
                        example_cmd = clean_text(next_line)
                        break

                    if example_cmd:
                        folder_dict[title].append({
                            "description": example_desc,
                            "cmd": example_cmd
                        })

                    i = j  # saute jusqu'à la ligne de commande traitée
                i += 1

    # Sauvegarde JSON
    with open(output_file, "w", encoding="utf-8") as out_file:
        json.dump(folder_dict, out_file, indent=2, ensure_ascii=False)

    print(f"{folder_name}.json generated")
