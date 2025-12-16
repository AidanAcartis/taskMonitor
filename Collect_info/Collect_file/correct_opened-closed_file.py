#!/usr/bin/env python3

def treat_lines(infile, outfile):
    """Lit un fichier ligne par ligne, traite chaque ligne et écrit le résultat dans un nouveau fichier."""

    try:
        # Lire toutes les lignes du fichier source
        with open(infile, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Liste temporaire pour stocker les lignes modifiées
        modified_lines = []

        for line in lines:
            line = line.strip()  # Supprimer les espaces autour
            dot_index = line.rfind('.')  # Trouver le dernier point

            if dot_index != -1:
                # Séparer avant et après le dernier point
                part1 = line[:dot_index]
                part2 = line[dot_index + 1:]

                # Garder uniquement le premier mot après le point
                part2 = part2.split()[0]

                result = f'{part1}.{part2}'
            else:
                result = line  # Aucun point → on garde la ligne telle quelle

            modified_lines.append(result)

        # Écrire les lignes modifiées dans le fichier de sortie
        with open(outfile, 'w', encoding='utf-8') as file:
            file.writelines(line + '\n' for line in modified_lines)

        print(f"[✓] Le fichier '{outfile}' a été généré avec succès.")

    except FileNotFoundError:
        print(f"[!] Fichier introuvable : {infile}")
    except Exception as e:
        print(f"[!] Erreur lors du traitement de {infile} : {e}")

# Traitement des deux fichiers
treat_lines('Opened_file.txt', 'Opened_file_true.txt')
treat_lines('Closed_file.txt', 'Closed_file_true.txt')
