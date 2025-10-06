# Charger les fichiers dans des listes
def load_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f]

opened_files = load_file('Opened_files_true.txt')
closed_files = load_file('Closed_files_true.txt')

# Stocker les résultats
output_lines = []

# Traiter les ouvertures
while opened_files:
    open_entry = opened_files.pop(0)  # Prendre la première ligne
    open_time, filename = open_entry.split(' ', 1)
    
    temp_list = [open_time, "", filename]  # Stocker l'entrée temporairement
    
    # Chercher la première occurrence du fichier dans les fermetures
    for i, close_entry in enumerate(closed_files):
        close_time, closed_filename = close_entry.split(' ', 1)
        if closed_filename == filename:
            temp_list[1] = close_time  # Ajouter l'heure de fermeture
            del closed_files[i]  # Supprimer cette fermeture utilisée
            break
    
    # Écrire dans le fichier de sortie
    output_lines.append(" ".join(temp_list))

# Écrire le fichier final
with open('Matched_files.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))
