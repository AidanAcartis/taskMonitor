from pathlib import Path
import torch
import torch.nn as nn
import numpy as np

# ─────────────────────────────────────────────
# BASE
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"

# ─────────────────────────────────────────────
# LOGS
# ─────────────────────────────────────────────
LOGS_DIR = DATA_DIR / "logs"
WINDOW_LOG_FILE = LOGS_DIR / "window_changes.log"
PREV_WINDOWS_FILE = LOGS_DIR / "prev_windows.txt"

# File collector outputs
FILE_LOG_DIR = DATA_DIR / "file_log"
OPEN_CLOSED_DIR = FILE_LOG_DIR / "open-closed_log"
DATA_FILE_DIR = FILE_LOG_DIR / "data_file"

COLLECTED_FILE = DATA_FILE_DIR / "collected_file.txt"
DATA_FILE_TXT = DATA_FILE_DIR / "data_file.txt"

# ─────────────────────────────────────────────
# COMMAND LOG
# ─────────────────────────────────────────────
COMMAND_LOG_DIR = DATA_DIR / "command_log"
DATA_COMMAND_FILE = COMMAND_LOG_DIR / "data_command.txt"

# ─────────────────────────────────────────────
# FUTURE PIPELINE
# ─────────────────────────────────────────────
PROCESSED_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"

DATA_COLLECT_FILE = PROCESSED_DIR / "data_collect.txt"
NORMALIZED_EVENTS_FILE = PROCESSED_DIR / "events_normalized.csv"

# ─────────────────────────────────────────────
# MODELS / AI
# ─────────────────────────────────────────────
MODELS_DIR = BASE_DIR.parent / "Vis_Models"
GEN_DESC_MODEL_DIR = MODELS_DIR / "Gen_Desc_Model" / "full_finetuned"

# ─────────────────────────────────────────────
# PROCESSING OUTPUTS
# ─────────────────────────────────────────────
DESCRIBED_EVENTS_FILE = PROCESSED_DIR / "events_described.csv"

# ───────────────── CONFIGURATION ─────────────────

LEXICAL_DIM = 512
BATCH_SIZE = 8
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

INFERENCE_CONFIG = {
    "num_beams": 5,
    "no_repeat_ngram_size": 3,
    "repetition_penalty": 1.5,
    "length_penalty": 1.0,
    "max_new_tokens": 50,
    "early_stopping": True
}

# ─────────────────────────────────────────────
# CLUSTERING
# ─────────────────────────────────────────────
CLUSTER_MODEL_DIR = MODELS_DIR / "final_model"

CLUSTER_OUTPUT_FILE = EXPORTS_DIR / "clusters_output.txt"

CLUSTER_CONFIG = {
    "random_seed": 42,
    "thresholds": np.arange(0.45, 0.85, 0.01),

    # Reclustering
    "cohesion_threshold": 0.34,
    "size_threshold": 10,

    # Final reclustering
    "cohesion_final": 0.55,
    "cohesion_split_max": 0.45,

    # Singleton
    "singleton_ratio": 0.10,

    # Post-processing
    "postproc_split_min": 0.40,
    "postproc_merge_sim": 0.55,
    "postproc_reassign_margin": 0.05,
    "singleton_merge_sim": 0.45
}