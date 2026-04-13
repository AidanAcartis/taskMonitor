#!/bin/bash
set -e

# ── Vérifications préliminaires ───────────────────────────────────────────────
if [ -z "$DISPLAY" ]; then
    echo "❌ No DISPLAY variable found. Make sure you are on Xorg."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo "   Install it with: sudo apt install docker.io"
    exit 1
fi

if ! xset q &>/dev/null; then
    echo "❌ Cannot connect to X server."
    exit 1
fi

# ── Chemin des modèles ────────────────────────────────────────────────────────
# Modifiable par l'utilisateur
VIS_MODELS_PATH="${VIS_MODELS_PATH:-$HOME/Vis_Models}"

if [ ! -d "$VIS_MODELS_PATH/final_model" ]; then
    echo "❌ AI models not found in: $VIS_MODELS_PATH"
    echo ""
    echo "   Expected structure:"
    echo "   $VIS_MODELS_PATH/"
    echo "   ├── Gen_Desc_Model/full_finetuned/"
    echo "   ├── final_model/"
    echo "   └── final_Model_V3/final_model/"
    echo ""
    echo "   Set the path with:"
    echo "   VIS_MODELS_PATH=/your/path ./run_taskmonitor.sh"
    exit 1
fi

# ── Autorisation X11 ──────────────────────────────────────────────────────────
echo "🔑 Setting up X11 authentication..."
touch /tmp/.docker.xauth
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | \
    xauth -f /tmp/.docker.xauth nmerge -

# Autoriser Docker à accéder à X11
xhost +local:docker > /dev/null 2>&1

# ── Créer les répertoires nécessaires ────────────────────────────────────────
mkdir -p ~/.taskmonitor/db
mkdir -p data/logs data/exports data/processed data/command_log data/file_log

# ── Lancer ───────────────────────────────────────────────────────────────────
echo "🚀 Starting TaskMonitor..."
echo "   Models: $VIS_MODELS_PATH"
echo "   Display: $DISPLAY"
echo ""

VIS_MODELS_PATH="$VIS_MODELS_PATH" docker compose up

# ── Nettoyage ─────────────────────────────────────────────────────────────────
xhost -local:docker > /dev/null 2>&1
echo ""
echo "👋 TaskMonitor stopped."