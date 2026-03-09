# Ouvrir et lire le fichier Titles.txt
with open('Opened_file.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Liste pour stocker les résultats modifiés
modified_lines = []

# Traiter chaque ligne du fichier
for line in lines:
    # Enlever les espaces en début et fin de ligne
    line = line.strip()
    
    # Chercher le dernier point '.' dans la ligne
    dot_index = line.rfind('.')
    
    if dot_index != -1:
        # Diviser la chaîne en deux parties : avant le point et après
        chaine1 = line[:dot_index]
        chaine2 = line[dot_index+1:]
        
        # Garder uniquement la première partie de la chaîne après le point (l'extension)
        chaine2 = chaine2.split()[0]  # Pour extraire juste l'extension sans les espaces
        
        # Combiner les deux parties
        result = chaine1 + '.' + chaine2
    else:
        # Si aucun point n'est trouvé, garder la ligne telle quelle
        result = line
    
    # Ajouter le résultat modifié à la liste
    modified_lines.append(result)

# Réécrire le fichier avec les lignes modifiées
with open('Opened_file_true.txt', 'w', encoding='utf-8') as file:
    file.writelines(line + '\n' for line in modified_lines)

print("Le fichier a été modifié avec succès.")
