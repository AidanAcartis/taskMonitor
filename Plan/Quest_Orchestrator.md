Alors on va construire orchestrator.py, mais pour cela il faut qu'on sache bien comment lancer chaque programme. Dans collector, comment lancer chaque programme et depuis quel directory(+ quels sont les requierements au niveau de l'emplacement, les packages, dans quel env ?) : window_monitor.py:"import subprocess
import signal
import os
from pathlib import Path


class WindowMonitor:

    def __init__(self):
        self.process = None
        self.script_path = Path(__file__).parent / "window_monitor.sh"

    def start(self):
        if self.process and self.is_running():
            print("Monitoring already in progress")
            return

        print("Starting monitoring (bash)...")

        self.process = subprocess.Popen(
            ["bash", str(self.script_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )

    def stop(self):
        if self.process and self.is_running():
            print("Monitoring stopped...")
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process = None

    def is_running(self):
        return self.process is not None and self.process.poll() is None", log_extractor.py:"import subprocess
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
        """Exécute le script bash et affiche les fichiers générés."""
        try:
            logger.logger.info(f"Lancement de {self.script_path}...")
            subprocess.run(["bash", str(self.script_path)], check=True)
            logger.logger.info(f"Fichiers générés :\n- {self.opened_file}\n- {self.closed_file}")
        except subprocess.CalledProcessError as e:
            logger.logger.error(f"Erreur lors de l'exécution du script : {e}")", file_extractor.py:"import subprocess
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
            logger.logger.info(f"Lancement de {self.script_path}...")
            
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

            logger.logger.info("File collection terminée avec succès.")

        except subprocess.CalledProcessError as e:
            logger.logger.error(
                f"Erreur lors de l'exécution du script : {e}\n"
                f"stdout:\n{e.output}\nstderr:\n{e.stderr}"
            )
            raise", 'command_collector.py':"import os
from datetime import datetime, timedelta
from pathlib import Path
from taskmonitor.core import config, logger

class CommandCollector:
    """
    Collects user commands from ~/.bash_history and saves them to data_command.txt in DATA_FILE_DIR.
    """

    def __init__(self):
        self.history_file = os.path.expanduser("~/.bash_history")
        self.output_file = config.DATA_COMMAND_FILE

        # Créer dossier si absent
        config.COMMAND_LOG_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        commandes = []
        current_timestamp = None
        date_aujourdhui = datetime.now().strftime("%Y-%m-%d")

        # Lecture du fichier historique
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            logger.logger.error(f"Fichier historique introuvable: {self.history_file}")
            return

        for line in lines:
            line = line.strip()

            # Ligne timestamp dans bash_history
            if line.startswith("#"):
                try:
                    current_timestamp = int(line[1:])
                except ValueError:
                    current_timestamp = None

            # Ligne commande
            elif current_timestamp is not None:
                date_du_jour = datetime.fromtimestamp(current_timestamp).strftime("%Y-%m-%d")

                if date_du_jour == date_aujourdhui:
                    start_dt = datetime.fromtimestamp(current_timestamp)
                    end_dt = start_dt + timedelta(seconds=2)
                    heure_ouverture = start_dt.strftime("%H:%M:%S")
                    heure_fermeture = end_dt.strftime("%H:%M:%S")
                    duree_minutes = round((end_dt - start_dt).total_seconds() / 60, 3)

                    commandes.append((
                        current_timestamp,
                        "Commande",
                        line,
                        heure_ouverture,
                        heure_fermeture,
                        date_du_jour,
                        duree_minutes
                    ))

        commandes.sort(key=lambda x: x[0])

        # Écriture du fichier final
        with open(self.output_file, "w", encoding="utf-8") as f:
            for cmd in commandes:
                ligne = f"{cmd[5]}, {cmd[3]}, {cmd[4]}, {cmd[6]:.3f}, {cmd[1]}, {cmd[2]}\n"
                f.write(ligne)

        logger.logger.info(f"{len(commandes)} commandes enregistrées dans {self.output_file}")", collect_data.py:"from pathlib import Path
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

        logger.logger.info(f"TSV généré: {self.output_path.resolve()}")", 'processing/assembler.py':""""
processing/assembler.py
=======================
Assemble data_file.txt et data_command.txt en un seul fichier TSV data_collect.txt.
Refactorisation de collect_data.py.
"""

from taskmonitor.core import config, storage
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


def assemble(date_str: str) -> list[str]:
    """
    Fusionne les données fichiers et commandes en un TSV unifié.

    Format de sortie (TSV):
        date  start  end  duration  type  name

    Args:
        date_str: date au format "YYYY-MM-DD"

    Returns:
        Lignes TSV de data_collect.txt
    """
    lines: list[str] = []

    # ── Fichiers (data_file.txt) ──────────────────────
    file_lines = storage.read_data_file(date_str)
    for line in file_lines:
        parts = line.strip().split()
        if len(parts) >= 6:
            date      = parts[0]
            time_open = parts[1]
            time_close= parts[2]
            duration  = parts[3]
            type_     = parts[4]
            name      = " ".join(parts[5:])
            lines.append(f"{date}\t{time_open}\t{time_close}\t{duration}\t{type_}\t{name}")

    # ── Commandes (data_command.txt) ─────────────────
    cmd_lines = storage.read_data_command(date_str)
    for line in cmd_lines:
        parts = [x.strip() for x in line.strip().split(",")]
        if len(parts) >= 6:
            date      = parts[0]
            time_open = parts[1]
            time_close= parts[2]
            duration  = parts[3]
            type_     = parts[4]
            name      = ", ".join(parts[5:])
            lines.append(f"{date}\t{time_open}\t{time_close}\t{duration}\t{type_}\t{name}")

    storage.write_data_collect(date_str, lines)
    log.info(f"data_collect.txt : {len(lines)} lignes pour {date_str}")
    return lines",  processing/parser.py:"import re
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

    def parse_event(self, raw: str):
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
            logger.logger.error(f"Fichier introuvable: {self.input_path}")
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
                # FILE / APP
                # ───────────────────────────────
                else:
                    event_type, file, app, command = self.parse_event(raw_event)

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

        logger.logger.info(f"Standardized saved events: {self.output_path}")", describer.py a besoin de ces autres fichiers :"(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/taskMonitor$ ls taskmonitor/
autostart   external     models           resources                 services
collectors  gui          orchestrator.py  run_clusterer.py
core        __init__.py  processing       run_describer.py
dicts       main.py      __pycache__      run_predict_intention.py
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/taskMonitor$ ls taskmonitor/processing/
assembler.py  cluster_output_parser.py  intention_predictor.py  __pycache__
clusterer     describer.py              io_utils.py
clusterer.py  __init__.py               parser.py
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/taskMonitor$ ls taskmonitor/models/
__init__.py  __pycache__  t5_fusion.py
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/taskMonitor$ ls taskmonitor/external/
command_desc
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/taskMonitor$ ls taskmonitor/dicts/
COMMAND_ACTION.json  KEY_CONCEPTS.json  THEMES.json  VERB_MAP_EXTENDED.json
FILE_EXTENSION.json  mime_map.json      TOOLS.json   VERB_MAP.json
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/taskMonitor$ ls taskmonitor/resources/
linux_special_files.py  __pycache__
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/taskMonitor$ ls taskmonitor/services/
command_description_service.py  description_builder.py       __init__.py
context_extractor.py            file_description_service.py  __pycache__
", et se lance en lancant run_describer.py:"import shutil
import subprocess
import sys

# ───────────────── CHECK cmddesc ─────────────────

def check_cmddesc():
    """Vérifie que cmddesc est installé et accessible."""
    if shutil.which("cmddesc") is None:
        print("❌ cmddesc n'est pas installé ou pas dans le PATH.")
        print("👉 Va dans : taskmonitor/external/command_desc/")
        print("👉 Puis installe avec : pip install .")
        sys.exit(1)

    try:
        result = subprocess.run(
            ["cmddesc"],
            input="ls",
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            raise Exception("cmddesc ne répond pas correctement")
    except Exception as e:
        print(f"❌ Erreur cmddesc : {e}")
        sys.exit(1)

    print("✅ cmddesc OK")


# ───────────────── RUN PIPELINE ─────────────────

def run_pipeline():
    print("🚀 Lancement du pipeline describer...\n")

    from processing.describer import main  # on va créer main()

    main()


# ───────────────── MAIN ─────────────────

if __name__ == "__main__":
    check_cmddesc()
    run_pipeline()", clusterer.py a besoin de clusterer:"(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/taskMonitor$ ls taskmonitor/processing/clusterer/
clustering_engine.py  __init__.py       reclustering_engine.py
cluster_pipeline.py   metrics.py        singleton_handler.py
distance_builder.py   postprocessor.py  utils.py
embedding_service.py  __pycache__
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/taskMonitor$ ls taskmonitor/processing/
assembler.py  cluster_output_parser.py  intention_predictor.py  __pycache__
clusterer     describer.py              io_utils.py
clusterer.py  __init__.py               parser.py
(base) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/taskMonitor$ 
" et en lancant run_clusterer.py'"""
run_clusterer.py
----------------
Point d'entrée pour exécuter le pipeline de clustering.
"""

from pathlib import Path

from taskmonitor.processing.clusterer.cluster_pipeline import ClusterPipeline
from taskmonitor.core.config import DESCRIBED_EVENTS_FILE

def main():
    # ─────────────────────────────────────────────
    # INPUT / OUTPUT
    # ─────────────────────────────────────────────
    input_file = DESCRIBED_EVENTS_FILE  # fichier réel existant

    # ─────────────────────────────────────────────
    # RUN PIPELINE
    # ─────────────────────────────────────────────
    pipeline = ClusterPipeline(input_file)
    result = pipeline.run()

    # ─────────────────────────────────────────────
    # DEBUG RAPIDE
    # ─────────────────────────────────────────────
    print("\n📊 Résumé final :")
    print(f"    Clusters   : {result['metrics_after']['n_clusters']}")
    print(f"    Silhouette : {result['metrics_after']['silhouette']:.3f}")
    print(f"    Cohésion   : {result['metrics_after']['cohesion']:.3f}")


if __name__ == "__main__":
    main()', finalement, 'intention_predictor.py' depend de 'cluster_output_parser.py', 'io_utils.py' et se lance en lancant run_predict_intention.py'#!/usr/bin/env python3
"""
Point d'entrée pour générer les intentions globales des clusters.
"""

import sys
from pathlib import Path
import argparse

from core.config import INTENTION_OUTPUT_TXT, INTENTION_OUTPUT_JSONL, INTENTION_MODEL_DIR
from processing.io_utils import write_txt, write_jsonl
from processing.intention_predictor import load_model, predict, generate_simple_intention
from processing.cluster_output_parser import parse_clusters

def parse_args():
    parser = argparse.ArgumentParser(description="Genere une global task intention pour chaque cluster.")
    parser.add_argument("--input", default=Path("data/exports/clusters_output.txt"), help="Fichier de clusters en entree")
    parser.add_argument("--model", default=INTENTION_MODEL_DIR, help="Chemin vers le modele Flan-T5 fine-tune")
    parser.add_argument("--out-txt", default=INTENTION_OUTPUT_TXT, help="Fichier texte de sortie")
    parser.add_argument("--out-jsonl", default=INTENTION_OUTPUT_JSONL, help="Fichier JSONL de sortie")
    return parser.parse_args()

def main():
    args = parse_args()

    print(f"\n{'='*65}")
    print("  CLUSTER GLOBAL TASK INTENTION PREDICTOR")
    print(f"{'='*65}\n")

    clusters = parse_clusters(args.input)
    print(f"{len(clusters)} clusters trouves")

    model, tokenizer, device = load_model(args.model)

    results = []
    for cluster in clusters:
        if cluster.get("is_singleton"):
            intention = generate_simple_intention(cluster["items"][0])
        else:
            intention = predict(model, tokenizer, device, cluster["items"])
        cluster["intention"] = intention
        results.append(cluster)
        print(f"{cluster['cluster_id']} -> {intention}")

    write_txt(results, args.out_txt)
    write_jsonl(results, args.out_jsonl)

    print(f"\nSorties generees : {args.out_txt}, {args.out_jsonl}")

if __name__ == "__main__":
    main()'. Voila, ils sont tous la, comment va-t-on construire construire pour les 3 modes maintenant : 'Mode MONITORING', 'Mode PROCESSING', 'Mode ALL-IN-ONE' ??