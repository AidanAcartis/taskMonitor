import subprocess
from pathlib import Path
from taskmonitor.core import config, logger

class LogExtractor:
    """Launches the bash script to extract open/closed windows from the log."""

    def __init__(self):
        self.base_dir: Path = config.BASE_DIR
        self.log_file: Path = config.WINDOW_LOG_FILE
        self.opened_file: Path = self.base_dir / "data/file_log/open-closed_log/Opened_file.txt"
        self.closed_file: Path = self.base_dir / "data/file_log/open-closed_log/Closed_file.txt"
        # Créer les dossiers si absents
        self.opened_file.parent.mkdir(parents=True, exist_ok=True)
        self.closed_file.parent.mkdir(parents=True, exist_ok=True)
        # Script bash correspondant
        self.script_path: Path = Path(__file__).parent / "log_extractor.sh"

    def run(self):
        "Executes the bash script and displays the generated files."
        try:
            logger.logger.info(f"Launch of {self.script_path}...")
            subprocess.run(["bash", str(self.script_path)], check=True)
            logger.logger.info(f"Files generated :\n- {self.opened_file}\n- {self.closed_file}")
        except subprocess.CalledProcessError as e:
            logger.logger.error(f"Error occurred while executing the script : {e}")