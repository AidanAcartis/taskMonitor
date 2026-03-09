import json
import os

# Charger le dictionnaire
with open("mime_map.json", "r", encoding="utf-8") as f:
    MIME_MAP = json.load(f)

def guess_type(filename: str):
    """
    Retourne uniquement le commentaire associé à une extension.
    """
    _, ext = os.path.splitext(filename.lower())
    data = MIME_MAP.get(ext)
    if data:
        return data.get("comment")  # <-- correction ici
    return None

# Exemple d'utilisation
if __name__ == "__main__":
    filename = input("Entrez un fichier (ex: file.py): ")
    comment = guess_type(filename)
    if comment:
        print(f"{filename} -> {comment}")
    else:
        print(f"Extension inconnue: {filename}")
