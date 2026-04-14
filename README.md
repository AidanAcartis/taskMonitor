# TaskMonitor

TaskMonitor is a desktop productivity analysis tool for Linux. It runs silently in the background, recording which windows you open and close and which terminal commands you execute. At the end of a session, it runs an AI pipeline that groups your activity into meaningful tasks, predicts what each task was about, and visualizes the results through an interactive PyQt6 interface.

---

## How It Works

### Data Collection

TaskMonitor collects two sources of data in parallel while you work.

The first source is window activity. A bash script runs every two seconds and uses `wmctrl` to detect which windows have been opened or closed since the last check. Every change is appended to a log file at `data/logs/window_changes.log` with a timestamp.

The second source is terminal commands. Every thirty seconds, a Python process reads your shell history and appends any new commands to `data/command_log/data_command.txt`.

### Processing Pipeline

When you trigger processing, the following steps run in sequence.

**Step 1 - File collection.** The pipeline reads `window_changes.log` and extracts opened and closed file names, computing how long each file was active.

**Step 2 - Data merge.** File events and command events are merged into a single normalized CSV at `data/processed/events_normalized.csv`.

**Step 3 - Event parsing.** Each event is classified as a file, an application, a directory, or a command, and enriched with timestamps, durations, and application names.

**Step 4 - AI description (Gen_Desc_Model).** A fine-tuned T5 model generates a natural language description for each unique event. Raw window titles like `dashboard.py - taskMonitor - Visual Studio Code` become descriptions like `opened dashboard.py with Visual Studio Code, contains data related to a Python script serving as a dashboard`.

**Step 5 - Clustering (final_model).** A sentence-transformer model (MiniLM-L6-v2) encodes all descriptions into semantic embeddings. An agglomerative clustering algorithm groups events that belong to the same task. The pipeline includes iterative reclustering, singleton merging, and post-processing to optimize cohesion and silhouette scores.

**Step 6 - Intention prediction (final_Model_V3).** A fine-tuned Flan-T5 model reads each cluster and predicts a short global task intention label, such as "Deploy and manage Docker for a system" or "Watch figure skating videos on YouTube".

**Step 7 - Storage.** The final JSON output is hashed using MD5 on the sorted cluster intentions. If the same session is processed twice, it is detected and skipped. Otherwise, it is stored in a monthly SQLite database at `~/.taskmonitor/db/taskmonitor_YYYY_MM.db`.

### Interface

The PyQt6 interface presents the results across several pages.

The **Dashboard** shows a GitHub-style activity heatmap over the past year and a vertical timeline of clusters for the selected session or date. You can filter by session or by calendar date.

The **Graphs and Stats** page shows bar charts of active duration per cluster, Gantt timelines, donut charts for task proportion, app proportion, and domain proportion, and line charts showing activity by hour of day or domain evolution over time.

The **Chart** page provides an alternative view with pyqtgraph-rendered bar charts for duration and cohesion, a scrollable Gantt chart, and a full summary table of all clusters.

The **Monitoring** page shows the live output of the monitoring process and a live tail of `window_changes.log`, side by side.

The **Processing** page shows the real-time output of the full AI pipeline as it runs.

---

## Requirements

To run TaskMonitor, the target machine needs the following.

- Linux with an Xorg display server (Wayland is not supported)
- Docker installed and running
- The AI model files placed in a directory accessible from the machine

The models required are:

```
Vis_Models/
├── Gen_Desc_Model/full_finetuned/
├── final_model/
└── final_Model_V3/final_model/
```

---

## Installation

### Step 1 - Install Docker

```bash
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
```

### Step 2 - Add your user to the Docker group

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Step 3 - Load the TaskMonitor image

Transfer the image file `taskmonitor_image.tar.gz` to your machine, then load it:

```bash
docker load < taskmonitor_image.tar.gz
docker images | grep taskmonitor
```

### Step 4 - Place the AI models

Copy the `Vis_Models` directory to your home folder or to any path you prefer:

```bash
ls ~/Vis_Models/
# Expected: Gen_Desc_Model  final_model  final_Model_V3
```

### Step 5 - Get the launch files

Copy `run_taskmonitor.sh` and `docker-compose.yml` into a working directory:

```bash
mkdir -p ~/taskmonitor
cd ~/taskmonitor
chmod +x run_taskmonitor.sh
```

---

## Usage

### Launching the application

From the directory containing `run_taskmonitor.sh`:

```bash
VIS_MODELS_PATH=~/Vis_Models ./run_taskmonitor.sh
```

If your models are stored at a different path, adjust the variable accordingly:

```bash
VIS_MODELS_PATH=/your/custom/path/Vis_Models ./run_taskmonitor.sh
```

The script will verify that Docker is running, that the X server is accessible, and that the model files are present before starting the container.

### Starting monitoring

Click the monitoring button in the toolbar and select "Start Monitoring". This launches the window tracker and the command collector. You can navigate to the Monitoring page to see the live output.

When you are done working, click "Stop Monitoring" to terminate the processes cleanly.

### Running the processing pipeline

Click the processing button in the toolbar and select "Start Processing". The full AI pipeline will run and stream its output to the Processing page. When it completes, the Dashboard, Graphs, and Chart pages are automatically refreshed with the new session data.

### Stopping the application

Click the quit button in the toolbar or close the window. The Docker container will stop automatically.

---

## Project Structure

```
taskMonitor/
├── Dockerfile
├── docker-compose.yml
├── run_taskmonitor.sh
├── requirements_docker.txt
├── taskmonitor/
│   ├── collectors/         # Window monitor, command collector, file collector
│   ├── core/               # Config, storage, database reader
│   ├── dicts/              # TOOLS.json, VERB_MAP_EXTENDED.json
│   ├── external/           # cmddesc command describer project
│   ├── gui/                # PyQt6 interface (pages, widgets, header, navbar)
│   ├── models/             # Model loading utilities
│   ├── processing/         # Parser, clusterer, intention predictor, assembler
│   ├── orchestrator.py     # Entry point for monitor and process modes
│   ├── run_describer.py
│   ├── run_clusterer.py
│   └── run_predict_intention.py
└── data/
    ├── logs/               # window_changes.log
    ├── command_log/        # data_command.txt
    ├── file_log/           # Collected file events
    ├── processed/          # Normalized CSV, described events
    └── exports/            # Cluster outputs and final JSON
```

---

## Data Persistence

The SQLite database is stored on the host machine at `~/.taskmonitor/db/` and mounted into the container as a volume. This means your session history is preserved across container restarts and image rebuilds.

The monitoring logs and export files in `data/` are also mounted as volumes and persist on the host.

---

## Notes

- TaskMonitor requires an Xorg session. It will not work on a Wayland session or on a machine without a display.
- The bash history file (`~/.bash_history`) must exist on the host machine for command collection to work. It is mounted read-only into the container.
- The timezone inside the container is set to match the host. If timestamps appear incorrect, verify that the `TZ` environment variable in `docker-compose.yml` matches your local timezone.
- Processing can take several minutes depending on the number of events and the hardware available. All models run on CPU inside the container.

## License

Copyright (c) 2026 AidanAcartis. All rights reserved.

This software and its source code are the exclusive property of the author.
No part of this software may be reproduced, distributed, modified, or used
in any form or by any means without the prior written permission of the author.