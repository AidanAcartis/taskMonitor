import json

def check_for_duplicate_ids(file_path):
    seen_ids = set()  # Set pour stocker les IDs déjà rencontrés
    duplicate_ids = []  # Liste pour stocker les IDs des lignes redondantes

    with open(file_path, 'r') as file:
        line_number = 1
        for line in file:
            try:
                # Essayer de charger chaque ligne en tant qu'objet JSON
                data = json.loads(line.strip())
                
                # Récupérer l'ID de la ligne
                item_id = data.get("id")
                
                if item_id in seen_ids:
                    # Si l'ID est déjà dans le set, on l'ajoute à la liste des doublons
                    duplicate_ids.append(item_id)
                else:
                    seen_ids.add(item_id)
                
            except json.JSONDecodeError as e:
                print(f"Erreur à la ligne {line_number}: {e}")
            
            line_number += 1
    
    if duplicate_ids:
        print("Doublons détectés (ID de ligne) :")
        for item_id in duplicate_ids:
            print(f"ID redondant : {item_id}")
    else:
        print("Aucun doublon d'ID détecté.")

# Remplacez 'chemin/vers/votre/fichier.jsonl' par le chemin réel du fichier JSONL à vérifier
file_path = 'TSY_AZO_KITIHANA_activity_data_final.jsonl'
check_for_duplicate_ids(file_path)