#!/bin/bash
# =============================================================
# setup_env.sh — Installation complète de TaskMonitor
# Compatible : Ubuntu 22.04 / 24.04 LTS
#
# Usage :
#   chmod +x setup_env.sh
#   ./setup_env.sh
#
# Ce script :
#   1. Installe wmctrl (dépendance système)
#   2. Crée l'environnement conda MLproject_py311
#   3. Installe toutes les dépendances Python
#   4. Installe TaskMonitor en mode éditable (pip install -e .)
#   5. Installe cmddesc
#   6. Configure l'autostart et les raccourcis
#   7. Vérifie que les modèles IA sont présents
# =============================================================

set -e

CONDA_ENV="MLproject_py311"
PYTHON_VERSION="3.11"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║         Installation de TaskMonitor          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 1. Dépendances système ─────────────────────────────────
echo "▶ [1/7] Installation des dépendances système..."
sudo apt-get update -qq
sudo apt-get install -y wmctrl libdbus-1-dev python3-dbus > /dev/null
echo "  ✓ wmctrl installé"

# ── 2. Vérifier conda ─────────────────────────────────────
echo ""
echo "▶ [2/7] Configuration de l'environnement conda..."

if ! command -v conda &> /dev/null; then
    echo "  ✗ conda introuvable."
    echo "    Installer Anaconda/Miniconda depuis https://conda.io/miniconda.html"
    exit 1
fi

# Créer l'env si nécessaire
if conda env list | grep -q "^$CONDA_ENV "; then
    echo "  ✓ Environnement $CONDA_ENV existant"
else
    echo "  Création de l'environnement $CONDA_ENV (Python $PYTHON_VERSION)..."
    conda create -n "$CONDA_ENV" python="$PYTHON_VERSION" -y -q
    echo "  ✓ Environnement créé"
fi

# Obtenir le chemin de l'env
CONDA_ENV_PATH=$(conda env list | grep "^$CONDA_ENV " | awk '{print $NF}')
PIP="$CONDA_ENV_PATH/bin/pip"
PYTHON="$CONDA_ENV_PATH/bin/python"

# ── 3. Installer les dépendances Python ───────────────────
echo ""
echo "▶ [3/7] Installation des dépendances Python..."
echo "  (Cela peut prendre plusieurs minutes selon votre connexion)"
$PIP install -q --upgrade pip
$PIP install -q -r "$PROJECT_DIR/requirements.txt"
echo "  ✓ Dépendances Python installées"

# ── 4. Installer TaskMonitor ──────────────────────────────
echo ""
echo "▶ [4/7] Installation de TaskMonitor..."
$PIP install -q -e "$PROJECT_DIR"
echo "  ✓ TaskMonitor installé (mode éditable)"

# ── 5. Installer cmddesc ──────────────────────────────────
echo ""
echo "▶ [5/7] Installation de cmddesc..."
CMDDESC_DIR="$PROJECT_DIR/taskmonitor/PROCESSING/DESCRIBE_EVENTS/command_desc/command_describer_project"

if [ -d "$CMDDESC_DIR" ]; then
    $PIP install -q -e "$CMDDESC_DIR"
    echo "  ✓ cmddesc installé"
else
    echo "  ⚠ Dossier cmddesc introuvable : $CMDDESC_DIR"
    echo "    Copier le dossier command_describer_project ici et relancer."
fi

# ── 6. Autostart + raccourcis ─────────────────────────────
echo ""
echo "▶ [6/7] Configuration de l'autostart et des raccourcis..."
$PYTHON -c "
from taskmonitor.autostart.install_autostart import install
results = install()
for k, v in results.items():
    print(f'  {\"✓\" if v else \"✗\"}  {k}')
"

# ── 7. Vérification des modèles IA ────────────────────────
echo ""
echo "▶ [7/7] Vérification des modèles IA..."

MODELS_DIR="$HOME/Documents/Projects/Visualization/Vis_Models"

check_model() {
    local path="$1"
    local name="$2"
    if [ -d "$path" ]; then
        echo "  ✓ $name"
    else
        echo "  ✗ $name manquant : $path"
        MODELS_OK=false
    fi
}

MODELS_OK=true
check_model "$MODELS_DIR/Gen_Desc_Model/full_finetuned"    "Gen_Desc_Model"
check_model "$MODELS_DIR/final_model"                       "Clustering model"
check_model "$MODELS_DIR/final_Model_V3/final_model"        "Intention model"

if [ "$MODELS_OK" = false ]; then
    echo ""
    echo "  ⚠ Certains modèles sont manquants."
    echo "  Copier les dossiers de modèles dans : $MODELS_DIR"
    echo "  ou définir la variable : export TASKMONITOR_MODELS_DIR=/chemin/vers/models"
fi

# ── Créer le wrapper de lancement ─────────────────────────
LAUNCHER="$HOME/.local/bin/taskmonitor"
mkdir -p "$HOME/.local/bin"
cat > "$LAUNCHER" << EOF
#!/bin/bash
source \$(conda info --base)/etc/profile.d/conda.sh
conda activate $CONDA_ENV
exec python -m taskmonitor.main "\$@"
EOF
chmod +x "$LAUNCHER"
echo ""
echo "  ✓ Launcher créé : $LAUNCHER"

# Vérifier que ~/.local/bin est dans le PATH
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo ""
    echo "  Ajouter à votre ~/.bashrc :"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# ── Résumé ────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║           Installation terminée !            ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  Pour lancer TaskMonitor :"
echo "    taskmonitor"
echo ""
echo "  TaskMonitor démarrera automatiquement"
echo "  à la prochaine connexion de session."
echo ""