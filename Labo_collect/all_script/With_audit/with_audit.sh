#!/bin/bash

# Obtenir la date actuelle
today=$(date '+%Y-%m-%d')

# Trouver les fichiers ouverts aujourd'hui uniquement
find /home/aidan/ -type f ! -path '*/.*' -atime 0 2>/dev/null | while read file; do
    # Récupérer la date et l'heure d'accès (ouverture)
    open_time=$(stat --format='%x' "$file" | awk '{print $1, $2}')
    
    # Vérifier si la date d'ouverture correspond à aujourd'hui
    if [[ $(echo "$open_time" | awk '{print $1}') == "$today" ]]; then
        # Chercher l'événement d'audit pour ce fichier
        close_time=$(ausearch -k file_access -f "$file" | tail -n 1 | awk '{print $1, $2}')
        
        # Si aucune fermeture n'a été trouvée, mettre "N/A"
        if [[ -z "$close_time" ]]; then
            close_time="N/A"
        fi

        # Afficher le résultat formaté
        echo "$open_time $close_time $file"
    fi
done | sort -k1,1 -k2,2
