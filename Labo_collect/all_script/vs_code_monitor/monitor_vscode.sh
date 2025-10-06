#!/bin/bash

LOG_FILE="$HOME/vs_code.log"
PROCESS_NAME="code"
START_TIME=""
OPENED_FILES_AT_START=""
OPENED_FILES_AT_END=""

echo "Surveillance de VS Code en cours..."

while true; do
    if pgrep -x "$PROCESS_NAME" > /dev/null; then
        if [ -z "$START_TIME" ]; then
            START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
            
            # Récupérer les fichiers ouverts au moment de l'ouverture
            OPENED_FILES_AT_START=$(wmctrl -l | grep "Visual Studio Code" | awk '{print $4}')

            echo "VS Code ouvert à : $START_TIME" >> "$LOG_FILE"
            echo "Fichiers ouverts lors de l'ouverture :" >> "$LOG_FILE"
            echo "$OPENED_FILES_AT_START" >> "$LOG_FILE"
            echo "-----------------------------" >> "$LOG_FILE"
        fi
    else
        if [ -n "$START_TIME" ]; then
            END_TIME=$(date +"%Y-%m-%d %H:%M:%S")

            # Récupérer les fichiers ouverts lors de la fermeture
            OPENED_FILES_AT_END=$(wmctrl -l | grep "Visual Studio Code" | awk '{print $4}')

            # Comparer les fichiers et afficher ceux qui ont été fermés
            CLOSED_FILES=$(comm -23 <(echo "$OPENED_FILES_AT_START") <(echo "$OPENED_FILES_AT_END"))

            echo "VS Code fermé à : $END_TIME" >> "$LOG_FILE"
            echo "Fichiers fermés :" >> "$LOG_FILE"
            echo "$CLOSED_FILES" >> "$LOG_FILE"
            echo "-----------------------------" >> "$LOG_FILE"

            START_TIME=""
        fi
    fi
    sleep 2
done
