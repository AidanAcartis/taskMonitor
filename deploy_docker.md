## Docker Deployment — Complete Guide

---

### Step 1 — Files to create in the project

**Final structure:**
```
taskMonitor/
├── Dockerfile
├── docker-compose.yml
├── requirements_docker.txt
├── run_taskmonitor.sh          <- script for the end user
├── .dockerignore
└── taskmonitor/
    └── core/
        └── config.py           <- slightly modified
```

---

**`requirements_docker.txt`** — only what is needed:

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

**`Dockerfile`**:

```dockerfile
FROM python:3.11-slim

# -- Build variables ----------------------------------------------------------
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# -- System dependencies ------------------------------------------------------
RUN apt-get update && apt-get install -y \
    # X11 window monitoring
    wmctrl \
    xdotool \
    x11-utils \
    # Qt / OpenGL
    libgl1-mesa-glx \
    libglib2.0-0 \
    libdbus-1-3 \
    libdbus-1-dev \
    pkg-config \
    # XCB plugins for Qt
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-cursor0 \
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
    # Utilities
    bash \
    curl \
    git \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# -- Working directory ---------------------------------------------------------
WORKDIR /app

# -- Install Python dependencies -----------------------------------------------
COPY requirements_docker.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_docker.txt

# -- Copy project --------------------------------------------------------------
COPY taskmonitor/ ./taskmonitor/
COPY data/ ./data/

# -- Install cmddesc -----------------------------------------------------------
RUN pip install --no-cache-dir -e \
    taskmonitor/external/command_desc/command_describer_project/

# -- Qt environment variables --------------------------------------------------
ENV QT_PLUGIN_PATH=/usr/local/lib/python3.11/site-packages/PyQt6/Qt6/plugins
ENV QML2_IMPORT_PATH=/usr/local/lib/python3.11/site-packages/PyQt6/Qt6/qml
ENV LD_LIBRARY_PATH=/usr/local/lib/python3.11/site-packages/PyQt6/Qt6/lib
ENV QT_XCB_GL_INTEGRATION=xcb-egl
ENV QT_DEBUG_PLUGINS=0

# -- Entry point ---------------------------------------------------------------
CMD ["python", "-m", "taskmonitor.gui.app"]
```

---

**`.dockerignore`**:

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

**`docker-compose.yml`**:

```yaml
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
      - TZ=Indian/Antananarivo

    volumes:
      # X11 access for the graphical interface
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - /tmp/.docker.xauth:/tmp/.docker.xauth:rw
      # AI models (mounted read-only)
      - ${VIS_MODELS_PATH}:/Vis_Models:ro
      # SQLite database (persistent across sessions)
      - ${HOME}/.taskmonitor:/root/.taskmonitor:rw
      # Bash history (for command collection)
      - ${HOME}/.bash_history:/root/.bash_history:ro
      # Monitoring logs
      - ./data/logs:/app/data/logs:rw
      # Processing exports
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

**`run_taskmonitor.sh`** — launch script for the end user:

```bash
#!/bin/bash
set -e

# -- Preliminary checks -------------------------------------------------------
if [ -z "$DISPLAY" ]; then
    echo "No DISPLAY variable found. Make sure you are on Xorg."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Docker is not installed."
    echo "   Install it with: sudo apt install docker.io"
    exit 1
fi

if ! xset q &>/dev/null; then
    echo "Cannot connect to X server."
    exit 1
fi

# -- Model path ---------------------------------------------------------------
VIS_MODELS_PATH="${VIS_MODELS_PATH:-$HOME/Vis_Models}"

if [ ! -d "$VIS_MODELS_PATH/final_model" ]; then
    echo "AI models not found in: $VIS_MODELS_PATH"
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

# -- X11 authentication -------------------------------------------------------
echo "Setting up X11 authentication..."
touch /tmp/.docker.xauth
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | \
    xauth -f /tmp/.docker.xauth nmerge -

xhost +local:docker > /dev/null 2>&1

# -- Create required directories ----------------------------------------------
mkdir -p ~/.taskmonitor/db
mkdir -p data/logs data/exports data/processed data/command_log data/file_log

# -- Launch -------------------------------------------------------------------
echo "Starting TaskMonitor..."
echo "   Models: $VIS_MODELS_PATH"
echo "   Display: $DISPLAY"
echo ""

VIS_MODELS_PATH="$VIS_MODELS_PATH" docker compose up

# -- Cleanup ------------------------------------------------------------------
xhost -local:docker > /dev/null 2>&1
echo ""
echo "TaskMonitor stopped."
```

---

**Modify `config.py`** — make the model path configurable:

```python
import os

# Replace this line:
# MODELS_DIR = BASE_DIR.parent / "Vis_Models"

# With:
MODELS_DIR = Path(os.environ.get(
    "VIS_MODELS_DIR",
    str(BASE_DIR.parent / "Vis_Models")
))
```

---

### Step 2 — Build the image on your machine

```bash
# From the taskMonitor/ directory
cd ~/Documents/Projects/Visualization/taskMonitor

# Build the image (takes 10-20 minutes the first time)
docker build -t taskmonitor:latest .

# Verify the image was created
docker images | grep taskmonitor
```

---

### Step 3 — Test on your machine before transferring

```bash
chmod +x run_taskmonitor.sh

# Test with your models
VIS_MODELS_PATH=~/Documents/Projects/Visualization/Vis_Models ./run_taskmonitor.sh
```

---

### Step 4 — Export the image for the target machine

```bash
# Save the image as a compressed file
# (takes time and disk space, approximately 3-5 GB)
docker save taskmonitor:latest | gzip > taskmonitor_image.tar.gz

echo "Image size:"
du -sh taskmonitor_image.tar.gz
```

---

### Step 5 — Transfer to the target machine

```bash
# Option A — via local network (SSH)
rsync -avz --progress taskmonitor_image.tar.gz user@192.168.x.x:~/

# Option B — via USB drive
cp taskmonitor_image.tar.gz /media/usb/

# Transfer the AI models if not already present
rsync -avz --progress \
    ~/Documents/Projects/Visualization/Vis_Models/ \
    user@192.168.x.x:~/Vis_Models/

# Transfer the launch script and docker-compose
scp run_taskmonitor.sh docker-compose.yml user@192.168.x.x:~/taskmonitor/
```

---

### Step 6 — Installation on the target machine

Run the following commands in order on the **target machine**:

```bash
# 1. Install Docker
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 2. Add your user to the docker group
sudo usermod -aG docker $USER
newgrp docker

# 3. Load the TaskMonitor image
docker load < taskmonitor_image.tar.gz

# Verify
docker images | grep taskmonitor

# 4. Create the working directory
mkdir -p ~/taskmonitor
cd ~/taskmonitor

# 5. Copy the launch files (transferred in step 5)
chmod +x run_taskmonitor.sh

# 6. Verify the models are in place
ls ~/Vis_Models/
# Expected: Gen_Desc_Model  final_model  final_Model_V3

# 7. Launch
VIS_MODELS_PATH=~/Vis_Models ./run_taskmonitor.sh
```

---

### Summary of what to distribute

```
Files to transfer to the target machine:
├── taskmonitor_image.tar.gz    (~3-5 GB)  <- Docker image
├── run_taskmonitor.sh          (< 1 KB)   <- launch script
├── docker-compose.yml          (< 1 KB)   <- configuration
└── Vis_Models/                 (~several GB) <- AI models
    ├── Gen_Desc_Model/
    ├── final_model/
    └── final_Model_V3/
```

The end user only needs **Docker installed** and to run `run_taskmonitor.sh`. Everything else (Python, PyQt6, torch, wmctrl...) is packaged inside the image.