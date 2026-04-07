from pathlib import Path
from taskmonitor.core import config, logger


class DataCollector:
    """
    Merge file activity + command activity into one unified TSV dataset.
    """

    def __init__(self):
        self.file_data_path: Path = config.DATA_FILE_TXT
        self.command_data_path: Path = config.DATA_COMMAND_FILE
        self.output_path: Path = config.DATA_COLLECT_FILE

        # Assurer que le dossier existe
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        lines = []

        # ───────────────────────────────
        # FILE DATA
        # ───────────────────────────────
        if self.file_data_path.exists():
            with open(self.file_data_path, encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()

                    if len(parts) >= 6:
                        date = parts[0]
                        time_open = parts[1]
                        time_close = parts[2]
                        duration = parts[3]
                        type_ = parts[4]
                        name = " ".join(parts[5:])

                        lines.append(
                            f"{date}\t{time_open}\t{time_close}\t{duration}\t{type_}\t{name}"
                        )
        else:
            logger.logger.warning(f"File data introuvable: {self.file_data_path}")

        # ───────────────────────────────
        # COMMAND DATA
        # ───────────────────────────────
        if self.command_data_path.exists():
            with open(self.command_data_path, encoding="utf-8") as f:
                for line in f:
                    parts = [x.strip() for x in line.strip().split(",")]

                    if len(parts) >= 6:
                        date = parts[0]
                        time_open = parts[1]
                        time_close = parts[2]
                        duration = parts[3]
                        type_ = parts[4]
                        name = " ".join(parts[5:])

                        lines.append(
                            f"{date}\t{time_open}\t{time_close}\t{duration}\t{type_}\t{name}"
                        )
        else:
            logger.logger.warning(f"Command data introuvable: {self.command_data_path}")

        # ───────────────────────────────
        # WRITE FINAL FILE
        # ───────────────────────────────
        with open(self.output_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

        logger.logger.info(f"TSV generated: {self.output_path.resolve()}")