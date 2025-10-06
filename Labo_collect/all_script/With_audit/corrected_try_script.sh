#!/bin/bash

# Obtenir la date actuelle
today=$(date '+%Y-%m-%d')

# Fichier de log des fenêtres
LOG_FILE="$HOME/window_changes.log"

# Trouver les fichiers ouverts aujourd'hui uniquement
find /home/aidan/ -type f ! -path '*/.*' -atime 0 2>/dev/null | while read file; do
    # Récupérer la date et l'heure d'accès (ouverture)
    open_time=$(stat --format='%x' "$file" | awk '{print $1, $2}')

    # Extraire la liste des fenêtres fermées et leurs heures
    closed_windows=$(paste \
        <(grep -A 0 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk '{print $2}') \
        <(grep -A 1 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk -F ' aidan ' 'NF>1 {
            split($2, arr, " - "); 
            title=""; 
            for (i=1; i<=length(arr)-2; i++) 
                title = title (i>1 ? " - " : "") arr[i]; 
            print title ? title : arr[1]
        }'))

    # Vérifier si le fichier est dans la liste des fenêtres fermées
    closed_time=""
    while IFS=$'\t' read -r pid title; do
        if [[ "$file" == *"$title"* ]]; then
            closed_time=$(grep "$pid" "$LOG_FILE" | awk '{print $1, $2}')
            break
        fi
    done <<< "$closed_windows"

    # Affichage des résultats
    if [[ -n "$closed_time" ]]; then
        echo "$file | Ouvert à: $open_time | Fermé à: $closed_time"
    else
        echo "$file | Ouvert à: $open_time | Toujours ouvert"
    fi

# Filtrer les lignes pour éviter d'afficher les dates isolées
done | grep '|' | sort -k1,1 -k2,2
