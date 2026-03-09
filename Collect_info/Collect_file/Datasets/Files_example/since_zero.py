input_file = "Files_list.txt"
output_file = "Files_list_renumbered.txt"  # on peut sauvegarder dans un nouveau fichier

with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    for new_idx, line in enumerate(f_in, start=0):
        parts = line.strip().split(maxsplit=1)
        if len(parts) < 2:
            continue
        # Récupérer le reste de la ligne
        rest = parts[1]
        f_out.write(f"{new_idx} {rest}\n")

print(f"Fichier renuméroté créé dans {output_file}")
