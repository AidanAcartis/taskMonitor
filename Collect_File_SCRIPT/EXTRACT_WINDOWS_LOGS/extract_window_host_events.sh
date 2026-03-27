#!/bin/bash

# Répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Fichier log à analyser
LOG_FILE="$HOME/window_changes.log"

# Fichiers de sortie (dans le même répertoire que le script)
OPENED_FILE="$SCRIPT_DIR/Opened_file.txt"
CLOSED_FILE="$SCRIPT_DIR/Closed_file.txt"

# Vider les fichiers avant insertion
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