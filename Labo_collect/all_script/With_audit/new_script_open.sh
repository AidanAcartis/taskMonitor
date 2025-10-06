#!/bin/bash

# Exécuter 'try_script.sh' et stocker les fichiers ouverts aujourd'hui
mapfile -t opened_files < <(./try_script.sh)

# Exécuter la commande pour récupérer les titres et horaires des fenêtres ouvertes
mapfile -t windows_info < <(paste <(grep -A 0 "Nouvelles fenêtres ajoutées" ~/window_changes.log | grep -v "^--$" | awk '{print $2}') <(grep -A 1 "Nouvelles fenêtres ajoutées" ~/window_changes.log | grep -v "^--$" | awk -F ' aidan ' 'NF>1 {split($2, arr, " - "); title=""; for (i=1; i<=length(arr)-2; i++) title = title (i>1 ? " - " : "") arr[i]; print title ? title : arr[1]}'))

# Fonction pour trouver la meilleure correspondance dans opened_files
find_best_match() {
    local input="$1"
    local best_match=""
    local best_score=0

    for file in "${opened_files[@]}"; do
        # On calcule le nombre de mots en commun
        common_words=$(echo "$file" "$input" | tr ' ' '\n' | sort | uniq -d | wc -l)
        if [[ $common_words -gt $best_score ]]; then
            best_score=$common_words
            best_match=$file
        fi
    done

    echo "$best_match"
}

# Parcourir chaque ligne de windows_info et corriger les noms
for line in "${windows_info[@]}"; do
    time_part=$(echo "$line" | awk '{print $1}')
    name_part=$(echo "$line" | cut -d' ' -f2-)

    best_match=$(find_best_match "$name_part")

    if [[ -n "$best_match" ]]; then
        echo "$time_part $best_match"
    fi
done
