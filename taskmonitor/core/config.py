from pathlib import Path
import torch
import torch.nn as nn

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
