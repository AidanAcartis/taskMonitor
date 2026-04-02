"""
core/storage.py
===============
Couche d'accès aux données.
Tous les modules passent par ici pour lire/écrire les fichiers.
Aucun autre module ne doit faire open() directement sur des fichiers de données.
"""

import csv
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from taskmonitor.core import config
from taskmonitor.core.models import Event, Cluster, DayReport
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────
# HELPERS DATES
# ─────────────────────────────────────────────

def today_str() -> str:
    """Retourne la date du jour au format YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def list_available_dates() -> list[str]:
    """
    Retourne la liste des dates pour lesquelles des données existent,
    triées du plus récent au plus ancien.
    """
    dates = []
    if config.EXPORTS_DIR.exists():
        for d in config.EXPORTS_DIR.iterdir():
            if d.is_dir() and _is_valid_date(d.name):
                dates.append(d.name)
    dates.sort(reverse=True)
    return dates


def _is_valid_date(s: str) -> bool:
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ─────────────────────────────────────────────
# WINDOW LOG
# ─────────────────────────────────────────────

def archive_window_log(date_str: str) -> Path:
    """
    Copie le window_changes.log actif dans l'archive de la date.
    Appelé en fin de journée ou avant traitement.
    """
    src = config.WINDOW_LOG_FILE
    dst = config.get_log_file(date_str)
    if src.exists():
        shutil.copy2(src, dst)
        log.info(f"Log archivé : {dst}")
    return dst


def read_window_log(date_str: Optional[str] = None) -> str:
    """
    Lit le contenu du window_changes.log.
    Si date_str fourni, lit l'archive ; sinon lit le log actif.
    """
    path = config.get_log_file(date_str) if date_str else config.WINDOW_LOG_FILE
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_opened_closed(date_str: str, opened_lines: list[str], closed_lines: list[str]) -> None:
    """Écrit les fichiers Opened_file.txt et Closed_file.txt."""
    files = config.get_processed_files(date_str)
    files["opened"].write_text("\n".join(opened_lines), encoding="utf-8")
    files["closed"].write_text("\n".join(closed_lines), encoding="utf-8")


# ─────────────────────────────────────────────
# FICHIERS DE DONNÉES BRUTES
# ─────────────────────────────────────────────

def read_data_file(date_str: str) -> list[str]:
    """Lit data_file.txt (durées fichiers)."""
    path = config.get_processed_files(date_str)["data_file"]
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def write_data_file(date_str: str, lines: list[str]) -> None:
    """Écrit data_file.txt."""
    path = config.get_processed_files(date_str)["data_file"]
    path.write_text("\n".join(lines), encoding="utf-8")


def read_data_command(date_str: str) -> list[str]:
    """Lit data_command.txt (commandes bash)."""
    path = config.get_processed_files(date_str)["data_command"]
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def write_data_command(date_str: str, lines: list[str]) -> None:
    """Écrit data_command.txt."""
    path = config.get_processed_files(date_str)["data_command"]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_data_collect(date_str: str, lines: list[str]) -> None:
    """Écrit data_collect.txt (assemblage final brut)."""
    path = config.get_processed_files(date_str)["data_collect"]
    path.write_text("\n".join(lines), encoding="utf-8")


# ─────────────────────────────────────────────
# CSV NORMALISÉS
# ─────────────────────────────────────────────

def write_events_normalized(date_str: str, df: pd.DataFrame) -> None:
    """Écrit events_normalized.csv."""
    path = config.get_processed_files(date_str)["events_normalized"]
    df.to_csv(path, index=False)
    log.info(f"events_normalized écrit : {path} ({len(df)} lignes)")


def read_events_normalized(date_str: str) -> pd.DataFrame:
    """Lit events_normalized.csv. Retourne DataFrame vide si absent."""
    path = config.get_processed_files(date_str)["events_normalized"]
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path).fillna("")


def write_events_described(date_str: str, df: pd.DataFrame) -> None:
    """Écrit events_described.csv."""
    path = config.get_processed_files(date_str)["events_described"]
    df.to_csv(path, index=False)
    log.info(f"events_described écrit : {path} ({len(df)} lignes)")


def read_events_described(date_str: str) -> pd.DataFrame:
    """Lit events_described.csv. Retourne DataFrame vide si absent."""
    path = config.get_processed_files(date_str)["events_described"]
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path).fillna("")


# ─────────────────────────────────────────────
# CLUSTERS ET INTENTIONS
# ─────────────────────────────────────────────

def write_clusters_output(date_str: str, content: str) -> None:
    """Écrit clusters_output.txt."""
    path = config.get_processed_files(date_str)["clusters_output"]
    path.write_text(content, encoding="utf-8")


def read_clusters_output(date_str: str) -> str:
    """Lit clusters_output.txt."""
    path = config.get_processed_files(date_str)["clusters_output"]
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_intentions(date_str: str, clusters: list[Cluster]) -> None:
    """Écrit clusters_with_intentions.jsonl et .txt."""
    files = config.get_export_files(date_str)

    # JSONL
    with files["intentions_jsonl"].open("w", encoding="utf-8") as f:
        for i, c in enumerate(clusters):
            record = {
                "id":                    str(i),
                "cluster_id":            c.label,
                "num_tasks":             c.num_tasks,
                "cohesion":              c.cohesion,
                "task_items":            c.items,
                "global_task_intention": c.intention,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # TXT lisible
    sep  = "=" * 65
    dash = "─" * 65
    lines = [sep, "  CLUSTERS — GLOBAL TASK INTENTIONS", sep, ""]
    for c in clusters:
        lines.append(dash)
        if c.is_singleton:
            lines.append(f"{c.label}  |  singleton")
        else:
            lines.append(f"{c.label}  |  {c.num_tasks} tache(s)  |  cohesion = {c.cohesion:.3f}")
        lines.append(dash)
        lines.append(f"  Global Task Intention : {c.intention}")
        lines.append("")
        lines.append("  Items :")
        for item in c.items:
            lines.append(f"    - {item}")
        lines.append("")
    lines += [sep, "  FIN DU RAPPORT", sep]
    files["intentions_txt"].write_text("\n".join(lines), encoding="utf-8")

    log.info(f"Intentions écrites : {files['intentions_jsonl']}")


def read_intentions(date_str: str) -> list[Cluster]:
    """Lit clusters_with_intentions.jsonl et retourne une liste de Cluster."""
    path = config.get_export_files(date_str)["intentions_jsonl"]
    if not path.exists():
        return []
    clusters = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            clusters.append(Cluster(
                cluster_id=i,
                label=data.get("cluster_id", f"Cluster {i}"),
                num_tasks=data.get("num_tasks", 0),
                cohesion=data.get("cohesion", 0.0),
                items=data.get("task_items", []),
                intention=data.get("global_task_intention", ""),
                is_singleton=data.get("num_tasks", 0) == 1,
            ))
    return clusters


# ─────────────────────────────────────────────
# RAPPORT JOURNALIER COMPLET
# ─────────────────────────────────────────────

def load_day_report(date_str: str) -> DayReport:
    """
    Charge le rapport complet d'une journée depuis les fichiers exportés.
    Utilisé par l'interface graphique.
    """
    report = DayReport(date_str=date_str)

    # Charger les événements décrits
    df = read_events_described(date_str)
    if not df.empty:
        for _, row in df.iterrows():
            report.events.append(Event(
                date=str(row.get("date", "")),
                start=str(row.get("start", "")),
                end=str(row.get("end", "")),
                duration=float(row.get("duration", 0.0)),
                event_type=str(row.get("event_type", "")),
                file=str(row.get("file", "")),
                app=str(row.get("app", "")),
                command=str(row.get("command", "")),
                raw=str(row.get("raw", "")),
                description=str(row.get("description", "")),
            ))
        report.total_duration = sum(e.duration for e in report.events)

    # Charger les clusters avec intentions
    report.clusters = read_intentions(date_str)

    # Vérifier si le monitoring a tourné ce jour
    log_path = config.get_log_file(date_str)
    report.monitoring_on = log_path.exists() and log_path.stat().st_size > 0

    return report