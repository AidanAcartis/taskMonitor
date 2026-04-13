#!/bin/bash
set -e

echo "======================================"
echo "  TaskMonitor — Installation"
echo "======================================"

# ── 1. Dépendances système ────────────────
echo "[1/6] Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    wmctrl \
    xdotool \
    libgl1 \
    libglib2.0-0 \
    libdbus-1-dev \
    pkg-config

# ── 2. Venv ───────────────────────────────
echo "[2/6] Creating virtual environment..."
python3.11 -m venv MLproject_py311
source MLproject_py311/bin/activate

# ── 3. Requirements ───────────────────────
echo "[3/6] Installing Python dependencies..."
pip install --upgrade pip
pip install \
    PyQt6==6.7.0 \
    pyqtgraph==0.14.0 \
    qtawesome \
    pandas \
    numpy \
    scikit-learn \
    sentence-transformers \
    transformers \
    torch \
    accelerate \
    safetensors \
    dbus-python \
    nltk \
    matplotlib

# ── 4. cmddesc ────────────────────────────
echo "[4/6] Installing cmddesc..."
pip install -e taskmonitor/external/command_desc/command_describer_project/

# ── 5. Variables Qt ───────────────────────
echo "[5/6] Setting up Qt environment variables..."
VENV_PATH="$(pwd)/MLproject_py311"

cat >> MLproject_py311/bin/activate << EOF

# TaskMonitor Qt setup
export QT_PLUGIN_PATH=\$VIRTUAL_ENV/lib/python3.11/site-packages/PyQt6/Qt6/plugins
export QML2_IMPORT_PATH=\$VIRTUAL_ENV/lib/python3.11/site-packages/PyQt6/Qt6/qml
export LD_LIBRARY_PATH=\$VIRTUAL_ENV/lib/python3.11/site-packages/PyQt6/Qt6/lib:\$LD_LIBRARY_PATH
EOF

# ── 6. Modèles ────────────────────────────
echo "[6/6] Checking AI models..."
MODELS_DIR="../Vis_Models"
if [ ! -d "$MODELS_DIR/final_model" ]; then
    echo "⚠️  Models not found in $MODELS_DIR"
    echo "   Please place the following folders next to the project:"
    echo "   - Vis_Models/Gen_Desc_Model/full_finetuned"
    echo "   - Vis_Models/final_model"
    echo "   - Vis_Models/final_Model_V3/final_model"
else
    echo "✅ Models found"
fi

echo ""
echo "======================================"
echo "  Installation complete!"
echo ""
echo "  To run TaskMonitor:"
echo "  source MLproject_py311/bin/activate"
echo "  python -m taskmonitor.gui.app"
echo "======================================"