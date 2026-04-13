## Déploiement Docker — Guide complet

---

### Étape 1 — Fichiers à créer dans le projet

**Structure finale :**
```
taskMonitor/
├── Dockerfile
├── docker-compose.yml
├── requirements_docker.txt
├── run_taskmonitor.sh          ← script pour l'utilisateur final
├── .dockerignore
└── taskmonitor/
    └── core/
        └── config.py           ← à modifier légèrement
```

---

**`requirements_docker.txt`** — uniquement ce qui est utile :

```
PyQt6==6.11.0
PyQt6-Qt6==6.11.0
PyQt6_sip==13.11.1
pyqtgraph==0.14.0
QtAwesome==1.4.2
QtPy==2.4.3
pandas==3.0.1
numpy==1.26.4
scikit-learn==1.8.0
scipy==1.17.1
sentence-transformers==5.3.0
transformers==5.3.0
torch==2.10.0
accelerate==1.13.0
safetensors==0.7.0
tokenizers==0.22.2
huggingface_hub==1.7.1
peft==0.18.1
tensorflow==2.21.0
keras==3.13.2
tqdm==4.67.3
regex==2026.2.28
requests==2.32.5
packaging==25.0
filelock==3.25.2
fsspec==2026.2.0
PyYAML==6.0.3
psutil==7.2.2
rich==14.3.3
```

---

**`Dockerfile`** :

```dockerfile
FROM python:3.11-slim

# ── Variables build ───────────────────────────────────────────────────────────
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ── Dépendances système ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    # Monitoring fenêtres X11
    wmctrl \
    xdotool \
    x11-utils \
    # Qt / OpenGL
    libgl1-mesa-glx \
    libglib2.0-0 \
    libdbus-1-3 \
    libdbus-1-dev \
    pkg-config \
    # XCB plugins Qt
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxkbcommon-x11-0 \
    libxkbcommon0 \
    libegl1 \
    libegl-mesa0 \
    libfontconfig1 \
    libfreetype6 \
    libx11-6 \
    libx11-xcb1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    # Utilitaires
    bash \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ── Répertoire de travail ─────────────────────────────────────────────────────
WORKDIR /app

# ── Installer les dépendances Python ─────────────────────────────────────────
COPY requirements_docker.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_docker.txt

# ── Copier le projet ──────────────────────────────────────────────────────────
COPY taskmonitor/ ./taskmonitor/
COPY data/ ./data/

# ── Installer cmddesc ─────────────────────────────────────────────────────────
RUN pip install --no-cache-dir -e \
    taskmonitor/external/command_desc/command_describer_project/

# ── Variables Qt ──────────────────────────────────────────────────────────────
ENV QT_PLUGIN_PATH=/usr/local/lib/python3.11/site-packages/PyQt6/Qt6/plugins
ENV QML2_IMPORT_PATH=/usr/local/lib/python3.11/site-packages/PyQt6/Qt6/qml
ENV LD_LIBRARY_PATH=/usr/local/lib/python3.11/site-packages/PyQt6/Qt6/lib
ENV QT_XCB_GL_INTEGRATION=xcb-egl
ENV QT_DEBUG_PLUGINS=0

# ── Point d'entrée ────────────────────────────────────────────────────────────
CMD ["python", "-m", "taskmonitor.gui.app"]
```

---

**`.dockerignore`** :

```
MLproject_py311/
__pycache__/
*.pyc
*.pyo
.git/
.gitignore
*.egg-info/
dist/
build/
*.log
data/logs/
data/exports/
data/processed/
data/command_log/
data/file_log/
```

---

**`docker-compose.yml`** :

```yaml
version: "3.9"

services:
  taskmonitor:
    image: taskmonitor:latest
    build:
      context: .
      dockerfile: Dockerfile
    container_name: taskmonitor_app

    environment:
      - DISPLAY=${DISPLAY}
      - XAUTHORITY=/tmp/.docker.xauth
      - VIS_MODELS_DIR=/Vis_Models
      - MKL_THREADING_LAYER=GNU
      - MKL_SERVICE_FORCE_INTEL=0

    volumes:
      # Accès X11 pour l'interface graphique
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - /tmp/.docker.xauth:/tmp/.docker.xauth:rw
      # Modèles AI (montés en lecture seule)
      - ${VIS_MODELS_PATH}:/Vis_Models:ro
      # Base de données SQLite (persistance entre sessions)
      - ${HOME}/.taskmonitor:/root/.taskmonitor:rw
      # Logs de monitoring (wmctrl écrit ici)
      - ./data/logs:/app/data/logs:rw
      # Exports du processing
      - ./data/exports:/app/data/exports:rw
      - ./data/processed:/app/data/processed:rw
      - ./data/command_log:/app/data/command_log:rw
      - ./data/file_log:/app/data/file_log:rw

    network_mode: host

    privileged: false

    stdin_open: true
    tty: true

    restart: "no"
```

---

**`run_taskmonitor.sh`** — script de lancement pour l'utilisateur :

```bash
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

VIS_MODELS_PATH="$VIS_MODELS_PATH" docker-compose up

# ── Nettoyage ─────────────────────────────────────────────────────────────────
xhost -local:docker > /dev/null 2>&1
echo ""
echo "👋 TaskMonitor stopped."
```

---

**Modifier `config.py`** — rendre le chemin des modèles configurable :

```python
import os

# Remplacer cette ligne :
# MODELS_DIR = BASE_DIR.parent / "Vis_Models"

# Par :
MODELS_DIR = Path(os.environ.get(
    "VIS_MODELS_DIR",
    str(BASE_DIR.parent / "Vis_Models")
))
```

---

### Étape 2 — Builder l'image sur ta machine

```bash
# Dans le dossier taskMonitor/
cd ~/Documents/Projects/Visualization/taskMonitor

# Builder l'image (prend 10-20 min la première fois)
docker build -t taskmonitor:latest .

# Vérifier que l'image est créée
docker images | grep taskmonitor
```

---

### Étape 3 — Tester sur ta machine avant d'envoyer

```bash
chmod +x run_taskmonitor.sh

# Tester avec tes modèles
VIS_MODELS_PATH=~/Documents/Projects/Visualization/Vis_Models ./run_taskmonitor.sh
```

---

### Étape 4 — Exporter l'image pour l'autre machine

```bash
# Sauvegarder l'image en fichier compressé
# (va prendre du temps et de l'espace ~3-5 Go)
docker save taskmonitor:latest | gzip > taskmonitor_image.tar.gz

echo "Image size:"
du -sh taskmonitor_image.tar.gz
```

---

### Étape 5 — Transférer sur l'autre machine

```bash
# Option A — via réseau local (SSH)
rsync -avz --progress taskmonitor_image.tar.gz user@192.168.x.x:~/

# Option B — via clé USB
cp taskmonitor_image.tar.gz /media/usb/

# Transférer aussi les modèles si pas déjà présents
rsync -avz --progress \
    ~/Documents/Projects/Visualization/Vis_Models/ \
    user@192.168.x.x:~/Vis_Models/

# Transférer le script de lancement et docker-compose
scp run_taskmonitor.sh docker-compose.yml user@192.168.x.x:~/taskmonitor/
```

---

### Étape 6 — Installation sur la machine cible

Sur la **machine cible**, exécuter dans l'ordre :

```bash
# 1. Installer Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# 2. Ajouter l'utilisateur au groupe docker
# (évite de devoir mettre sudo à chaque fois)
sudo usermod -aG docker $USER
newgrp docker

# 3. Charger l'image TaskMonitor
docker load < taskmonitor_image.tar.gz

# Vérifier
docker images | grep taskmonitor

# 4. Créer la structure de dossiers
mkdir -p ~/taskmonitor
cd ~/taskmonitor

# 5. Copier les fichiers de lancement
# (copiés depuis l'étape 5)
chmod +x run_taskmonitor.sh

# 6. Vérifier que les modèles sont là
ls ~/Vis_Models/
# Doit afficher : Gen_Desc_Model  final_model  final_Model_V3

# 7. Lancer
VIS_MODELS_PATH=~/Vis_Models ./run_taskmonitor.sh
```

---

### Résumé de ce que tu distribues

```
📦 À transférer sur la machine cible :
├── taskmonitor_image.tar.gz    (~3-5 Go) ← l'image Docker
├── run_taskmonitor.sh          (< 1 Ko)  ← script de lancement
├── docker-compose.yml          (< 1 Ko)  ← configuration
└── Vis_Models/                 (~plusieurs Go) ← modèles AI
    ├── Gen_Desc_Model/
    ├── final_model/
    └── final_Model_V3/
```

L'utilisateur final n'a besoin que de **Docker installé** et de **lancer `run_taskmonitor.sh`**. Tout le reste (Python, PyQt6, torch, wmctrl...) est dans l'image.