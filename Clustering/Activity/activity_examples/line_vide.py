input_file = "50.txt"
output_file = "Sans_vides.txt"

with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    for line in f_in:
        if line.strip():  # ne garde que les lignes non vides
            f_out.write(line)

print(f"Les lignes vides ont été supprimées et sauvegardées dans {output_file}.")
