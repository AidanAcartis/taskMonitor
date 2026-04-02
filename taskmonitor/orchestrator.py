"""
orchestrator.py
===============
Chef d'orchestre du pipeline complet.
Lance les étapes dans l'ordre, émet des signaux PyQt6 vers l'UI,
gère les erreurs et permet l'annulation.

Utilisation:
    orch = Orchestrator(date_str="2026-03-28")
    orch.step_started.connect(ui.on_step_started)
    orch.step_done.connect(ui.on_step_done)
    orch.finished.connect(ui.on_finished)
    orch.start()   # tourne dans un QThread
"""

from datetime import datetime

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from taskmonitor.core import config, storage
from taskmonitor.core.models import PipelineState, PipelineStep
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────
# WORKER — tourne dans un QThread séparé
# ─────────────────────────────────────────────

class PipelineWorker(QObject):
    """
    Exécute le pipeline dans un thread séparé pour ne pas bloquer l'UI.
    Émet des signaux à chaque changement d'état.
    """

    # Signaux émis vers l'UI
    step_started  = pyqtSignal(str, str)      # (step_name, label)
    step_progress = pyqtSignal(str, int)      # (step_name, percent 0-100)
    step_done     = pyqtSignal(str)           # (step_name)
    step_error    = pyqtSignal(str, str)      # (step_name, error_message)
    log_message   = pyqtSignal(str)           # message texte libre
    finished      = pyqtSignal(bool)          # True = succès, False = erreur

    def __init__(self, date_str: str, parent=None):
        super().__init__(parent)
        self.date_str  = date_str
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        """Point d'entrée principal — appelé par QThread.start()."""
        config.ensure_dirs()
        success = True

        steps = self._build_steps()

        for step_fn, name, label in steps:
            if self._cancelled:
                self.log_message.emit("Pipeline annulé.")
                self.finished.emit(False)
                return

            self.step_started.emit(name, label)
            self.log_message.emit(f"▶ {label}...")

            try:
                step_fn()
                self.step_done.emit(name)
                self.log_message.emit(f"✓ {label}")
            except Exception as e:
                err = str(e)
                log.exception(f"Erreur étape {name}: {err}")
                self.step_error.emit(name, err)
                self.log_message.emit(f"✗ {label} — {err}")
                success = False
                break

        self.finished.emit(success)

    # ─────────────────────────────────────────
    # DÉFINITION DES ÉTAPES
    # ─────────────────────────────────────────

    def _build_steps(self) -> list[tuple]:
        """
        Retourne la liste ordonnée des étapes :
        (fonction, nom_interne, label_affiché)
        """
        date_str = self.date_str

        # Import ici pour éviter les imports circulaires au niveau module
        from taskmonitor.collectors.file_collector   import extract_opened_closed, collect_file_data
        from taskmonitor.collectors.command_collector import collect_commands
        from taskmonitor.processing.assembler         import assemble
        from taskmonitor.processing.parser            import parse
        from taskmonitor.processing.describer         import Describer
        from taskmonitor.processing.clusterer         import Clusterer
        from taskmonitor.processing.intention_predictor import IntentionPredictor

        # Instances réutilisables (modèles chargés une seule fois)
        describer  = Describer()
        clusterer  = Clusterer()
        predictor  = IntentionPredictor()

        def _archive_log():
            storage.archive_window_log(date_str)

        def _extract():
            extract_opened_closed(date_str)

        def _collect_files():
            collect_file_data(date_str)

        def _collect_commands():
            collect_commands(date_str)

        def _assemble():
            lines = assemble(date_str)
            if not lines:
                raise RuntimeError("Aucune donnée à assembler")

        def _parse():
            df = parse(date_str)
            if df.empty:
                raise RuntimeError("Parsing a produit un DataFrame vide")

        def _describe():
            df = describer.describe(date_str)
            if df.empty:
                raise RuntimeError("Description a produit un DataFrame vide")

        def _cluster():
            groups = clusterer.cluster(date_str)
            if not groups:
                raise RuntimeError("Clustering n'a produit aucun cluster")

        def _predict():
            clusters = predictor.predict(date_str)
            if not clusters:
                raise RuntimeError("Aucune intention générée")

        return [
            (_archive_log,       "archive_log",      "Archivage du log fenêtres"),
            (_extract,           "extract",          "Extraction ouvertures / fermetures"),
            (_collect_files,     "collect_files",    "Calcul des durées fichiers"),
            (_collect_commands,  "collect_commands", "Collecte des commandes bash"),
            (_assemble,          "assemble",         "Assemblage des données"),
            (_parse,             "parse",            "Normalisation en CSV"),
            (_describe,          "describe",         "Description IA des événements"),
            (_cluster,           "cluster",          "Clustering des activités"),
            (_predict,           "predict",          "Génération des intentions globales"),
        ]


# ─────────────────────────────────────────────
# ORCHESTRATOR — gère le thread
# ─────────────────────────────────────────────

class Orchestrator(QObject):
    """
    Interface publique pour lancer/arrêter le pipeline.
    Gère le QThread et le PipelineWorker.

    Usage depuis l'UI:
        orch = Orchestrator()
        orch.step_started.connect(my_slot)
        orch.finished.connect(my_slot)
        orch.start(date_str)
    """

    step_started  = pyqtSignal(str, str)
    step_progress = pyqtSignal(str, int)
    step_done     = pyqtSignal(str)
    step_error    = pyqtSignal(str, str)
    log_message   = pyqtSignal(str)
    finished      = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: PipelineWorker | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def start(self, date_str: str | None = None) -> None:
        """Lance le pipeline pour la date donnée (défaut: aujourd'hui)."""
        if self.is_running:
            log.warning("Pipeline déjà en cours")
            return

        date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        log.info(f"Démarrage du pipeline pour {date_str}")

        self._thread = QThread()
        self._worker = PipelineWorker(date_str)
        self._worker.moveToThread(self._thread)

        # Connecter les signaux du worker → signaux de l'orchestrateur
        self._worker.step_started.connect(self.step_started)
        self._worker.step_progress.connect(self.step_progress)
        self._worker.step_done.connect(self.step_done)
        self._worker.step_error.connect(self.step_error)
        self._worker.log_message.connect(self.log_message)
        self._worker.finished.connect(self._on_worker_finished)

        # Démarrer le worker quand le thread démarre
        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def cancel(self) -> None:
        """Annule le pipeline en cours."""
        if self._worker:
            self._worker.cancel()

    def _on_worker_finished(self, success: bool) -> None:
        """Nettoyage après fin du worker."""
        self.finished.emit(success)
        if self._thread:
            self._thread.quit()
            self._thread.wait()
        self._thread = None
        self._worker = None
        log.info(f"Pipeline terminé (succès={success})")


# ─────────────────────────────────────────────
# LISTE DES ÉTAPES (pour l'UI — ordre et labels)
# ─────────────────────────────────────────────

PIPELINE_STEPS = [
    PipelineStep("archive_log",      "Archivage du log fenêtres"),
    PipelineStep("extract",          "Extraction ouvertures / fermetures"),
    PipelineStep("collect_files",    "Calcul des durées fichiers"),
    PipelineStep("collect_commands", "Collecte des commandes bash"),
    PipelineStep("assemble",         "Assemblage des données"),
    PipelineStep("parse",            "Normalisation en CSV"),
    PipelineStep("describe",         "Description IA des événements"),
    PipelineStep("cluster",          "Clustering des activités"),
    PipelineStep("predict",          "Génération des intentions globales"),
]