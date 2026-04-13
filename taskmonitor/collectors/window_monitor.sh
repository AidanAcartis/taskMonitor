#!/bin/bash
export DISPLAY=:0
export XAUTHORITY="${XAUTHORITY:-/home/aidan/.Xauthority}"

# ─────────────────────────────────────────────
# BASE DIR (portable)
# ─────────────────────────────────────────────
BASE_DIR="$(cd "$(dirname "$0")/../../" && pwd)"

LOG_FILE="$BASE_DIR/data/logs/window_changes.log"
PREV_WINDOWS_FILE="$BASE_DIR/data/logs/prev_windows.txt"

# Créer dossier si absent
mkdir -p "$BASE_DIR/data/logs"

# Si le fichier précédent n'existe pas, créez-le avec l'état actuel des fenêtres
if [ ! -f "$PREV_WINDOWS_FILE" ]; then
    wmctrl -l > "$PREV_WINDOWS_FILE"
fi

echo "Window monitoring in progress..."

while true; do
    # Obtenir la date d'aujourd'hui
    CURRENT_DATE=$(date +"%Y-%m-%d")

    # Vérifier la dernière date enregistrée dans le fichier de log
    if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
        LAST_LOG_DATE=$(grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}" "$LOG_FILE" | tail -n 1 | awk '{print $1}')
    else
        LAST_LOG_DATE=""
    fi

    # Si la dernière date enregistrée est différente d'aujourd'hui, on vide le fichier de log
    if [ "$CURRENT_DATE" != "$LAST_LOG_DATE" ]; then
        echo "-----------------------------" > "$LOG_FILE"
        echo "$(date +"%Y-%m-%d %H:%M:%S") - Nouveau jour de surveillance" >> "$LOG_FILE"
    fi

    # Obtenez la liste actuelle des fenêtres
    CURRENT_WINDOWS=$(wmctrl -l)

    # Comparez l'état actuel avec l'état précédent
    NEW_WINDOWS=$(comm -13 <(sort "$PREV_WINDOWS_FILE") <(echo "$CURRENT_WINDOWS" | sort))
    CLOSED_WINDOWS=$(comm -23 <(sort "$PREV_WINDOWS_FILE") <(echo "$CURRENT_WINDOWS" | sort))

    # Si de nouvelles fenêtres ont été ajoutées, enregistrez-les dans le fichier log
    if [ -n "$NEW_WINDOWS" ]; then
        echo "$(date +"%Y-%m-%d %H:%M:%S") - Nouvelles fenêtres ajoutées :" >> "$LOG_FILE"
        echo "$NEW_WINDOWS" >> "$LOG_FILE"
        echo "-----------------------------" >> "$LOG_FILE"
    fi

    # Si des fenêtres ont été fermées, enregistrez-les dans le fichier log
    if [ -n "$CLOSED_WINDOWS" ]; then
        echo "$(date +"%Y-%m-%d %H:%M:%S") - Fenêtres fermées :" >> "$LOG_FILE"
        echo "$CLOSED_WINDOWS" >> "$LOG_FILE"
        echo "-----------------------------" >> "$LOG_FILE"
    fi

    # Mettez à jour le fichier de l'état précédent
    echo "$CURRENT_WINDOWS" > "$PREV_WINDOWS_FILE"

    # Pause de 2 secondes avant la prochaine vérification
    sleep 2
done
