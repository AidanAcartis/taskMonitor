
# TaskMonitor

Desktop activity monitoring system with AI-based analysis and visualization.

The system automatically tracks open windows, edited files, and executed shell commands, then processes this data through a machine learning pipeline to produce task clusters and high-level user intentions.

---

## Architecture

```

taskmonitor/
├── taskmonitor/
│   ├── core/               ← shared modules (config, models, storage, logger)
│   ├── collectors/         ← raw data collection
│   ├── processing/         ← AI processing pipeline
│   ├── gui/                ← PyQt6 interface
│   ├── autostart/          ← startup integration
│   ├── orchestrator.py     ← pipeline orchestrator
│   └── main.py             ← entry point
├── data/                   ← local data (generated, not versioned)
├── models/                 ← AI models (not versioned, manual copy)
├── assets/                 ← icons and resources
├── requirements.txt
├── pyproject.toml
└── setup_env.sh

````

---

## Installation

### On Ubuntu (22.04 / 24.04)

```bash
git clone <repository-url> taskmonitor
cd taskmonitor
chmod +x setup_env.sh
./setup_env.sh
````

The setup script installs:

* `wmctrl` (window tracking)
* Conda environment `MLproject_py311`
* Python dependencies
* `cmddesc` (command description engine)
* Autostart configuration
* Desktop shortcut

---

## Models

The system relies on several machine learning models, each responsible for a specific stage of the pipeline.

### Description Model (T5-based)

* Path: `Vis_Models/Gen_Desc_Model/full_finetuned/`
* Used in: `processing/describer.py`
* Purpose:

  * Generate semantic descriptions of raw events
  * Normalize heterogeneous system data into structured text

---

### Clustering Model (Sentence Transformer)

* Path: `Vis_Models/final_model/`
* Used in: `processing/clusterer.py`
* Purpose:

  * Encode task descriptions into embeddings
  * Group semantically similar tasks into clusters

---

### Intention Prediction Model (Flan-T5 fine-tuned)

* Path: `Vis_Models/final_Model_V3/final_model/`
* Used in: `processing/intention_predictor.py`
* Purpose:

  * Generate a global task intention per cluster
  * Summarize multiple actions into a single high-level objective

---

## Pipeline Overview

| Step        | Module                   | Model Used          | Output             |
| ----------- | ------------------------ | ------------------- | ------------------ |
| Description | `describer.py`           | T5 (fine-tuned)     | Event descriptions |
| Clustering  | `clusterer.py`           | SentenceTransformer | Task clusters      |
| Intention   | `intention_predictor.py` | Flan-T5             | Global intentions  |

---

## Execution Model and Orchestration

### Fundamental Rule

All commands must be executed from the project root:

```
~/Documents/Projects/Visualization/taskMonitor
```

Always use module execution:

```bash
python -m taskmonitor.<module>
```

This ensures:

* Proper absolute imports
* Consistent path resolution
* Compatibility with packaging

---

## Environment Requirements

### Python Environment

```
MLproject_py311
```

### Required Packages

```bash
pip install pandas numpy scikit-learn transformers torch
```

### System Dependencies

* Access to `~/.bash_history`
* X11-compatible window manager
* `wmctrl` installed

### External Dependency

```bash
cd taskmonitor/external/command_desc
pip install .
```

---

## Module Execution

### Monitoring (Long-running)

Window monitor:

```python
from taskmonitor.collectors.window_monitor import WindowMonitor

wm = WindowMonitor()
wm.start()
```

Command collector:

```python
from taskmonitor.collectors.command_collector import CommandCollector

CommandCollector().run()
```

---

### Processing (Batch Pipeline)

1. Log extraction

```python
from taskmonitor.collectors.log_extractor import LogExtractor
LogExtractor().run()
```

2. File collection

```python
from taskmonitor.collectors.file_collector import FileCollector
FileCollector().run()
```

3. Data aggregation

```python
from taskmonitor.collectors.collect_data import DataCollector
DataCollector().run()
```

4. Parsing

```python
from taskmonitor.processing.parser import EventParser
EventParser().run()
```

5. Description

```bash
python -m taskmonitor.run_describer
```

6. Clustering

```bash
python -m taskmonitor.run_clusterer
```

7. Intention prediction

```bash
python -m taskmonitor.run_predict_intention
```

---

## Execution Modes

| Type         | Components               |
| ------------ | ------------------------ |
| Long-running | window_monitor           |
| Batch        | full processing pipeline |

---

## Orchestrator

The orchestrator (`taskmonitor/orchestrator.py`) provides three execution modes.

### Monitoring Mode

```bash
python -m taskmonitor.orchestrator monitor
```

Runs continuous monitoring and periodic command collection.

---

### Processing Mode

```bash
python -m taskmonitor.orchestrator process
```

Executes the full pipeline from raw logs to intentions.

---

### All-in-One Mode

```bash
python -m taskmonitor.orchestrator all
```

Runs monitoring in the background, executes processing, then stops monitoring.

---

## Critical Points

### Script Permissions

```bash
chmod +x taskmonitor/collectors/window_monitor.sh
```

### Configuration

All paths must be defined in `taskmonitor/core/config.py`.

Avoid hardcoded paths.

### Environment Activation

```bash
conda activate MLproject_py311
```

---

## Data Storage

Data is stored in:

```
~/.taskmonitor/data/
├── logs/YYYY-MM-DD/window_changes.log
├── processed/YYYY-MM-DD/
│   ├── Opened_file.txt
│   ├── Closed_file.txt
│   ├── data_collect.txt
│   ├── events_normalized.csv
│   ├── events_described.csv
│   └── clusters_output.txt
└── exports/YYYY-MM-DD/
    ├── clusters_with_intentions.jsonl
    └── clusters_with_intentions.txt
```

Each day is stored independently and can be accessed through the interface.

---

## Environment Variables

| Variable               | Default                                         | Description      |
| ---------------------- | ----------------------------------------------- | ---------------- |
| TASKMONITOR_DATA_DIR   | `~/.taskmonitor/data`                           | Data directory   |
| TASKMONITOR_MODELS_DIR | `~/Documents/Projects/Visualization/Vis_Models` | Models directory |

---

## System Outcome

The system evolves from independent scripts into a structured and reproducible pipeline:

* Centralized orchestration
* Consistent execution model
* AI-driven analysis pipeline
* Ready for GUI integration
* Suitable for deployment as a background service

---

## Future Improvements

* Systemd service integration for monitoring
* Centralized logging
* Incremental processing for performance
* State management (checkpoints, caching, embedding reuse)
* Full pipeline optimization for production use

