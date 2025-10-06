import re

# Ouvrir et lire le fichier Titles.txt
with open('Titles.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Filtrer les lignes non vides
non_empty_lines = [line for line in lines if line.strip()]

# Réécrire le fichier sans les lignes vides
with open('Titles.txt', 'w', encoding='utf-8') as file:
    file.writelines(non_empty_lines)
