#!/bin/bash

# Obtenir la date actuelle
today=$(date '+%Y-%m-%d')

# Trouver les fichiers ouverts aujourd'hui uniquement
find /home/aidan/ -type f ! -path '*/.*' -atime 0 2>/dev/null | while read file; do
    # Récupérer la date et l'heure d'accès (ouverture)
    open_time=$(stat --format='%x' "$file" | awk '{print $1, $2}')

    # Vérifier si la date d'ouverture correspond à aujourd'hui
    if [[ $(echo "$open_time" | awk '{print $1}') == "$today" ]]; then
        # Vérifier si le fichier est encore ouvert avec `lsof`
        if lsof -t -- "$file" > /dev/null 2>&1; then
            close_time="N/A"
        else
            # Si le fichier est fermé, récupérer la date de dernière modification
            close_time=$(stat --format='%y' "$file" | awk '{print $2}')
        fi

        # Afficher le résultat formaté
        #echo "$open_time $close_time $file"
        echo "$(basename "$file")"
    fi
done | sort -k1,1 -k2,2
