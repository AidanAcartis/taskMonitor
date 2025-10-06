#!/bin/bash

# Exécute la commande donnée et filtre les résultats
grep -A 1 "Fenêtres fermées" ~/window_changes.log | \
grep -v "^--$" | \
awk -F ' aidan ' '{print $2}' | \
sed 's/^[[:space:]]*//' | \
while read -r line; do
    # Cherche la dernière occurrence d'un point pour récupérer l'extension
    extension=$(echo "$line" | grep -o '\.[a-zA-Z0-9]*$')
    
    # Si une extension est trouvée, affiche le fichier
    if [[ -n "$extension" ]]; then
        echo "$line"
    fi
done
