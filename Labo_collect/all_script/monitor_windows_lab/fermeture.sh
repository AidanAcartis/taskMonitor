#!/bin/bash

# Définir le fichier de log des fenêtres
LOG_FILE="$HOME/window_changes.log"
# Définir le fichier pour stocker les informations sur les fenêtres fermées
CLOSED_FILES_LOG="$HOME/closed_files.log"
# Définir la date d'aujourd'hui
today=$(date '+%Y-%m-%d')

# Vérifier si le fichier closed_files.log existe déjà
if [ ! -f "$CLOSED_FILES_LOG" ]; then
    touch "$CLOSED_FILES_LOG"
fi

# Lire le fichier window_changes.log et récupérer les fenêtres fermées
grep "Fenêtres fermées" "$LOG_FILE" | while read -r line; do
    # Extraire la date, l'heure et le nom du fichier de la ligne
    close_time=$(echo "$line" | awk '{print $1, $2}')
    file_name=$(echo "$line" | awk '{print $5, $6, $7, $8}')

    # Si la date de fermeture est aujourd'hui, vérifier si le fichier existe encore
    if [[ $(echo "$close_time" | awk '{print $1}') == "$today" ]]; then
        # Chercher si le fichier est encore ouvert dans le log (recherche de nouvelles fenêtres ajoutées)
        if grep -q "$file_name" "$LOG_FILE"; then
            # Si le fichier est trouvé, c'est un fichier ouvert, pas encore fermé
            echo "$file_name est encore ouvert."
        else
            # Si le fichier n'est pas trouvé, il est considéré comme fermé
            echo "$close_time - Le fichier $file_name a été fermé." >> "$CLOSED_FILES_LOG"
        fi
    fi
done
