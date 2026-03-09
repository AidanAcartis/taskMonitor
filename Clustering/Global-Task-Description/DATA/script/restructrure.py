
import json

input_file = "activity_data_augmented2.jsonl"
output_file = "activity_data_corrected.jsonl"

with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    
    for line in f_in:
        
        entry = json.loads(line)
        
        original_id = entry.get("original_id")
        
        raw_response = entry.get("raw_response")
        
        if raw_response:
            try:
                raw_json = json.loads(raw_response.replace('JSON {', '{').replace('} }', '}'))
                
                task_items_versions = raw_json.get("task_items_versions", [])
                
                new_structure = {
                    "id": original_id,
                    "task_items_versions": task_items_versions
                }
                
                f_out.write(json.dumps(new_structure, ensure_ascii=False) + "\n")
                print(f"Réponse restructurée pour l'ID {original_id} sauvegardée.")
            
            except json.JSONDecodeError:
                print(f"Erreur de décodage JSON pour l'ID {original_id}, réponse brute ignorée.")
                continue
        else:
            print(f"Pas de réponse brute pour l'ID {original_id}, ignoré.")

print("Restructuration terminée.")