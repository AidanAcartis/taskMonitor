import subprocess
from pathlib import Path
from taskmonitor.core import config, logger

class FileCollector:
    """
    Launch all the steps to collect open/closed files and generate data_file.txt.
    """

    def __init__(self):
        # Chemin du script bash
        self.script_path: Path = Path(__file__).parent / "file_collector.sh"

    def run(self):
        try:
            logger.logger.info(f"Launch of {self.script_path}...")
            
            # On s'assure que le script bash est exécutable
            self.script_path.chmod(0o755)

            # Exécution du script bash
            result = subprocess.run(
                ["bash", str(self.script_path)],
                capture_output=True, text=True
            )

            # Afficher la sortie standard
            if result.stdout:
                logger.logger.info(result.stdout)
            if result.stderr:
                logger.logger.error(result.stderr)

            # Vérifier le code de retour
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, result.args, output=result.stdout, stderr=result.stderr
                )

            logger.logger.info("File collection successfully completed.")

        except subprocess.CalledProcessError as e:
            logger.logger.error(
                f"Error occurred while executing the script : {e}\n"
                f"stdout:\n{e.output}\nstderr:\n{e.stderr}"
            )
            raise