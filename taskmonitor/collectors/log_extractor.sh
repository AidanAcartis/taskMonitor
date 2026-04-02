#!/bin/bash

# Répertoire de base
BASE_DIR="$(cd "$(dirname "$0")/../../" && pwd)"
LOG_FILE="$BASE_DIR/data/logs/window_changes.log"

# Fichiers de sortie
OPENED_FILE="$BASE_DIR/data/file_log/open-closed_log/Opened_file.txt"
CLOSED_FILE="$BASE_DIR/data/file_log/open-closed_log/Closed_file.txt"

# Créer dossiers si absent
mkdir -p "$(dirname "$OPENED_FILE")"
mkdir -p "$(dirname "$CLOSED_FILE")"

> "$OPENED_FILE"
> "$CLOSED_FILE"

# Détecter automatiquement le hostname actuel
HOSTNAME_CURRENT=$(hostname)

# Extraction des fenêtres ouvertes avec horodatage
paste -d ' ' \
  <(grep -A 0 "Nouvelles fenêtres ajoutées" "$LOG_FILE" | grep -v "^--$" | awk '{print $1}' | grep .) \
  <(grep -A 0 "Nouvelles fenêtres ajoutées" "$LOG_FILE" | grep -v "^--$" | awk '{print $2}' | grep .) \
  <(grep -A 1 "Nouvelles fenêtres ajoutées" "$LOG_FILE" | grep -v "^--$" | awk -v host="$HOSTNAME_CURRENT" '{for (i=1;i<=NF;i++) if ($i ~ "^"host) {for (j=i+1;j<=NF;j++) printf $j" "; print ""}}' | grep .) \
  > "$OPENED_FILE"

# Extraction des fenêtres fermées avec horodatage
paste -d ' ' \
  <(grep -A 0 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk '{print $1}' | grep .) \
  <(grep -A 0 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk '{print $2}' | grep .) \
  <(grep -A 1 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk -v host="$HOSTNAME_CURRENT" '{for (i=1;i<=NF;i++) if ($i ~ "^"host) {for (j=i+1;j<=NF;j++) printf $j" "; print ""}}' | grep .) \
  > "$CLOSED_FILE"

echo "Fichiers générés :"
echo "- $OPENED_FILE"
echo "- $CLOSED_FILE"