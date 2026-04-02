#!/bin/bash

set -e  # stop le script si une commande échoue

# ───────────────────────────────
# Répertoires
# ───────────────────────────────
BASE_DIR="$(cd "$(dirname "$0")/../../" && pwd)"
EXTRACT_DIR="$BASE_DIR/data/file_log"
OPEN_CLOSED_DIR="$EXTRACT_DIR/open-closed_log"
COLLECTED_DIR="$EXTRACT_DIR/data_file"

# Créer dossiers si absents
mkdir -p "$OPEN_CLOSED_DIR"
mkdir -p "$COLLECTED_DIR"

# ───────────────────────────────
# Extraction des fenêtres ouvertes/fermées
# ───────────────────────────────
echo "Start extract the opened and closed file in window_changes.log..."
bash "$BASE_DIR/taskmonitor/collectors/log_extractor.sh" \
  "$BASE_DIR/data/logs/window_changes.log" \
  "$OPEN_CLOSED_DIR/Opened_file.txt" \
  "$OPEN_CLOSED_DIR/Closed_file.txt"
echo "Opened_file.txt and Closed_file.txt successfully extracted!"

# ───────────────────────────────
# Création du fichier collected_file.txt
# ───────────────────────────────
echo "Start create collected_file.txt"
python3 "$BASE_DIR/taskmonitor/collectors/requierements/get_collect_file.py" \
  "$OPEN_CLOSED_DIR/Opened_file.txt" \
  "$OPEN_CLOSED_DIR/Closed_file.txt" \
  "$COLLECTED_DIR/collected_file.txt"
echo "collected_file.txt successfully created!"

# ───────────────────────────────
# Création du fichier data_file.txt
# ───────────────────────────────
echo "Start to make the real data"
python3 "$BASE_DIR/taskmonitor/collectors/requierements/duration_file.py" \
  "$COLLECTED_DIR/collected_file.txt" \
  "$COLLECTED_DIR/data_file.txt"
echo "data_file.txt successfully created!"