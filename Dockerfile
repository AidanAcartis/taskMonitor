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
    libgl1 \
    libgl1-mesa-dri \
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
    # Utilitaires
    bash \
    curl \
    git \
    tzdata \
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