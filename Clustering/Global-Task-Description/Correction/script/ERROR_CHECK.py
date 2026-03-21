import json

def check_jsonl_file(file_path):
    with open(file_path, 'r') as file:
        line_number = 1
        for line in file:
            try:
                # Essayez de charger chaque ligne en tant que JSON
                json.loads(line.strip())
            except json.JSONDecodeError as e:
                # Si une erreur se produit, affichez la ligne et l'erreur
                print(f"Erreur à la ligne {line_number}: {e}")
            line_number += 1

# Remplacer le chemin d'accès par le fichier .jsonl à analyser
file_path = 'TSY_AZO_KITIHANA_activity_data_final.jsonl'

check_jsonl_file(file_path)