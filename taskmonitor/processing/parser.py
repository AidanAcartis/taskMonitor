import re
import pandas as pd
from pathlib import Path
from taskmonitor.core import config, logger

class EventParser:
    """
    Transform raw data_collect.txt into structured events (CSV).
    """

    def __init__(self):
        self.input_path: Path = config.DATA_COLLECT_FILE
        self.output_path: Path = config.NORMALIZED_EVENTS_FILE

        self.file_regex = re.compile(r"\.[a-zA-Z0-9]+$")

        # Créer dossier si absent
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    def detect_file(self, name: str) -> bool:
        return bool(self.file_regex.search(name))

    def parse_event(self, raw: str, type_raw: str = None):
        """
        Returns: event_type, file, app, command
        """

        # Nettoyer raw
        raw = raw.strip()

        # Cas type directory/App avec répertoire connu
        if type_raw and "directory/App" in type_raw:
            if raw in config.KNOWN_DIRS:
                return "directory", "", raw, ""
            else:
                return "app", "", raw, ""

        # Cas général : split " - " pour détecter fichier et app
        parts = raw.split(" - ")

        if len(parts) >= 2:
            filename = parts[0].strip()
            app = parts[-1].strip()

            if self.detect_file(filename):
                return "file", filename, app, ""
            else:
                return "app", "", app, ""
        else:
            if self.detect_file(raw):
                return "file", raw, "", ""
            return "app", "", raw, ""

    def run(self):
        if not self.input_path.exists():
            logger.logger.error(f"File not founded: {self.input_path}")
            return

        rows = []

        with open(self.input_path, encoding="utf-8") as f:
            for line in f:
                cols = line.strip().split("\t")

                if len(cols) < 6:
                    continue

                date, start, end, duration, type_raw, raw_event = cols

                try:
                    duration = float(duration)
                except ValueError:
                    continue

                # ───────────────────────────────
                # COMMAND
                # ───────────────────────────────
                if type_raw == "Commande":
                    rows.append({
                        "date": date,
                        "start": start,
                        "end": end,
                        "duration": duration,
                        "event_type": "command",
                        "file": "",
                        "app": "Terminal",
                        "command": raw_event,
                        "raw": raw_event
                    })

                # ───────────────────────────────
                # FILE / APP / DIRECTORY
                # ───────────────────────────────
                else:
                    event_type, file, app, command = self.parse_event(raw_event, type_raw)

                    rows.append({
                        "date": date,
                        "start": start,
                        "end": end,
                        "duration": duration,
                        "event_type": event_type,
                        "file": file,
                        "app": app,
                        "command": command,
                        "raw": raw_event
                    })

        df = pd.DataFrame(rows)
        df.to_csv(self.output_path, index=False)

        logger.logger.info(f"Standardized saved events: {self.output_path}")