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

# ─────────────────────────────────────────────
# FUTURE PIPELINE
# ─────────────────────────────────────────────
PROCESSED_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"