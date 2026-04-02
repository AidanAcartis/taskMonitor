from pathlib import Path

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
# FUTURE PIPELINE
# ─────────────────────────────────────────────
PROCESSED_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"