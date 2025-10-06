#!/bin/bash

LOG_FILE="$HOME/vs_code.log"
PROCESS_NAME="code"
START_TIME=""
OPENED_FILES=""

echo "Surveillance de VS Code en cours..."

while true; do
    # Vérifier si VS Code est en cours d'exécution
    if pgrep -x "$PROCESS_NAME" > /dev/null; then
        # Si c'est la première détection d'ouverture, enregistrer l'heure et les fichiers ouverts
        if [ -z "$START_TIME" ]; then
            START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
            OPENED_FILES=$(lsof -c "$PROCESS_NAME" | awk '{print $9}' | grep "/" | sort | uniq)

            echo "VS Code ouvert à : $START_TIME" >> "$LOG_FILE"
            echo "Fichiers ouverts lors de l'ouverture :" >> "$LOG_FILE"
            #echo "$OPENED_FILES" >> "$LOG_FILE"
            echo "-----------------------------" >> "$LOG_FILE"
        fi
    else
        # Si VS Code était ouvert mais plus maintenant, enregistrer l'heure et les fichiers fermés
        if [ -n "$START_TIME" ]; then
            END_TIME=$(date +"%Y-%m-%d %H:%M:%S")
            CLOSED_FILES=$(lsof -c "$PROCESS_NAME" | awk '{print $9}' | grep "/" | sort | uniq)

            echo "VS Code fermé à : $END_TIME" >> "$LOG_FILE"
            echo "Fichiers ouverts juste avant la fermeture :" >> "$LOG_FILE"
            #echo "$CLOSED_FILES" >> "$LOG_FILE"
            echo "-----------------------------" >> "$LOG_FILE"

            # Réinitialiser START_TIME
            START_TIME=""
        fi
    fi
    sleep 2  # Vérifie toutes les 2 secondes
done