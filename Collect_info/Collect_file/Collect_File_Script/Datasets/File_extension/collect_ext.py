import os
import json
import xml.etree.ElementTree as ET

MIME_DIR = "/usr/share/mime"

def parse_mime_xml(file_path):
    """Extrait type, comment et extensions depuis un fichier XML MIME"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        mime_type = root.attrib.get("type")
        if not mime_type:
            return []

        # premier commentaire sans attribut xml:lang
        comment = None
        for c in root.findall("{http://www.freedesktop.org/standards/shared-mime-info}comment"):
            if not c.attrib:  # sans xml:lang
                comment = c.text
                break

        # toutes les extensions dans glob
        extensions = []
        for glob in root.findall("{http://www.freedesktop.org/standards/shared-mime-info}glob"):
            pattern = glob.attrib.get("pattern")
            if pattern and pattern.startswith("*."):
                extensions.append(pattern[1:])  # enlève * → .ext

        # crée un dictionnaire pour chaque extension
        results = []
        for ext in extensions:
            results.append((ext, {"type": mime_type, "comment": comment}))
        return results

    except Exception as e:
        print(f"Erreur parsing {file_path}: {e}")
        return []


def build_mime_dict():
    mime_dict = {}
    for root, dirs, files in os.walk(MIME_DIR):
        for f in files:
            if f.endswith(".xml"):
                file_path = os.path.join(root, f)
                for ext, data in parse_mime_xml(file_path):
                    mime_dict[ext] = data
    return mime_dict


if __name__ == "__main__":
    mime_map = build_mime_dict()


    # Sauvegarde en JSON
    with open("mime_map.json", "w", encoding="utf-8") as f:
        json.dump(mime_map, f, indent=4, ensure_ascii=False)

    # Exemple d'affichage de quelques entrées
    for i, (ext, data) in enumerate(mime_map.items()):
        print(f"{ext} -> {data['type']} ({data['comment']})")
        if i > 20:  # afficher seulement les 20 premiers
            break

    print(f"\nNombre total d'extensions trouvées : {len(mime_map)}")