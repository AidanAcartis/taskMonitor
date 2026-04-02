"""
gui/pipeline_dialog.py
======================
Fenêtre de progression du pipeline.
Affiche l'état de chaque étape en temps réel + log textuel.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QWidget, QTextEdit,
    QProgressBar, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QColor

from taskmonitor.orchestrator import PIPELINE_STEPS
from taskmonitor.core.models import PipelineStep


# ─────────────────────────────────────────────
# WIDGET D'UNE ÉTAPE
# ─────────────────────────────────────────────

class StepRow(QWidget):
    """Ligne représentant une étape du pipeline : icône + label + statut."""

    ICONS = {
        PipelineStep.PENDING: "○",
        PipelineStep.RUNNING: "◉",
        PipelineStep.DONE:    "✓",
        PipelineStep.ERROR:   "✗",
    }
    COLORS = {
        PipelineStep.PENDING: "#475569",
        PipelineStep.RUNNING: "#6366F1",
        PipelineStep.DONE:    "#4ADE80",
        PipelineStep.ERROR:   "#F87171",
    }

    def __init__(self, name: str, label: str, parent=None):
        super().__init__(parent)
        self.name  = name
        self.label = label

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        self._icon_lbl = QLabel(self.ICONS[PipelineStep.PENDING])
        self._icon_lbl.setFixedWidth(20)
        self._icon_lbl.setFont(QFont("monospace", 13))
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._text_lbl = QLabel(label)
        self._text_lbl.setFont(QFont("Segoe UI", 10))

        self._status_lbl = QLabel("En attente")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._status_lbl.setFont(QFont("Segoe UI", 9))

        layout.addWidget(self._icon_lbl)
        layout.addWidget(self._text_lbl, stretch=1)
        layout.addWidget(self._status_lbl)

        self._set_status(PipelineStep.PENDING)

    def set_running(self):
        self._set_status(PipelineStep.RUNNING)
        self._status_lbl.setText("En cours…")

    def set_done(self):
        self._set_status(PipelineStep.DONE)
        self._status_lbl.setText("Terminé")

    def set_error(self, msg: str):
        self._set_status(PipelineStep.ERROR)
        self._status_lbl.setText("Erreur")
        self._text_lbl.setToolTip(msg)

    def _set_status(self, status: str):
        color = self.COLORS[status]
        icon  = self.ICONS[status]
        self._icon_lbl.setText(icon)
        self._icon_lbl.setStyleSheet(f"color: {color};")
        self._text_lbl.setStyleSheet(
            f"color: {'#E2E8F0' if status != PipelineStep.PENDING else '#64748B'};"
        )
        self._status_lbl.setStyleSheet(f"color: {color};")


# ─────────────────────────────────────────────
# DIALOGUE PRINCIPAL
# ─────────────────────────────────────────────

class PipelineDialog(QDialog):
    """
    Fenêtre modale de progression du pipeline.
    Se connecte aux signaux de l'Orchestrator.
    """

    STYLE = """
        QDialog {
            background-color: #0F1117;
            color: #E2E8F0;
        }
        QLabel {
            color: #E2E8F0;
        }
        QTextEdit {
            background-color: #1A1D27;
            color: #94A3B8;
            border: 1px solid #2A2D3E;
            border-radius: 6px;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 11px;
            padding: 6px;
        }
        QProgressBar {
            background-color: #1A1D27;
            border: 1px solid #2A2D3E;
            border-radius: 4px;
            height: 8px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #6366F1;
            border-radius: 4px;
        }
        QPushButton {
            background-color: #1A1D27;
            color: #E2E8F0;
            border: 1px solid #2A2D3E;
            border-radius: 6px;
            padding: 8px 20px;
            font-size: 10px;
        }
        QPushButton:hover {
            background-color: #2A2D3E;
            border-color: #6366F1;
        }
        QPushButton#btn_cancel {
            border-color: #F87171;
            color: #F87171;
        }
        QPushButton#btn_cancel:hover {
            background-color: #2A1A1A;
        }
        QPushButton#btn_close {
            background-color: #6366F1;
            border-color: #6366F1;
            color: white;
        }
        QPushButton#btn_close:hover {
            background-color: #4F46E5;
        }
        QFrame#step_container {
            background-color: #1A1D27;
            border: 1px solid #2A2D3E;
            border-radius: 8px;
        }
    """

    def __init__(self, orchestrator, date_str: str, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.date_str     = date_str
        self._done        = False

        self.setWindowTitle(f"Analyse en cours — {date_str}")
        self.setMinimumSize(620, 580)
        self.setStyleSheet(self.STYLE)
        self.setModal(True)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Titre
        title = QLabel(f"Pipeline d'analyse  ·  {self.date_str}")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #E2E8F0;")
        layout.addWidget(title)

        # Barre de progression globale
        self._progress = QProgressBar()
        self._progress.setRange(0, len(PIPELINE_STEPS))
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        layout.addWidget(self._progress)

        # Container des étapes
        step_frame = QFrame()
        step_frame.setObjectName("step_container")
        step_layout = QVBoxLayout(step_frame)
        step_layout.setContentsMargins(0, 4, 0, 4)
        step_layout.setSpacing(0)

        self._step_rows: dict[str, StepRow] = {}
        for i, step in enumerate(PIPELINE_STEPS):
            row = StepRow(step.name, step.label)
            step_layout.addWidget(row)
            self._step_rows[step.name] = row

            if i < len(PIPELINE_STEPS) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("color: #2A2D3E;")
                step_layout.addWidget(sep)

        layout.addWidget(step_frame)

        # Log textuel
        log_label = QLabel("Journal d'exécution")
        log_label.setFont(QFont("Segoe UI", 10))
        log_label.setStyleSheet("color: #64748B;")
        layout.addWidget(log_label)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFixedHeight(130)
        layout.addWidget(self._log_text)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._btn_cancel = QPushButton("Annuler")
        self._btn_cancel.setObjectName("btn_cancel")
        self._btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self._btn_cancel)

        self._btn_close = QPushButton("Fermer")
        self._btn_close.setObjectName("btn_close")
        self._btn_close.setEnabled(False)
        self._btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self._btn_close)

        layout.addLayout(btn_layout)

    def _connect_signals(self):
        self.orchestrator.step_started.connect(self._on_step_started)
        self.orchestrator.step_done.connect(self._on_step_done)
        self.orchestrator.step_error.connect(self._on_step_error)
        self.orchestrator.log_message.connect(self._on_log)
        self.orchestrator.finished.connect(self._on_finished)

    # ── Slots ────────────────────────────────

    @pyqtSlot(str, str)
    def _on_step_started(self, name: str, label: str):
        if name in self._step_rows:
            self._step_rows[name].set_running()

    @pyqtSlot(str)
    def _on_step_done(self, name: str):
        if name in self._step_rows:
            self._step_rows[name].set_done()
        done = sum(1 for r in self._step_rows.values()
                   if r._status_lbl.text() == "Terminé")
        self._progress.setValue(done)

    @pyqtSlot(str, str)
    def _on_step_error(self, name: str, msg: str):
        if name in self._step_rows:
            self._step_rows[name].set_error(msg)

    @pyqtSlot(str)
    def _on_log(self, msg: str):
        self._log_text.append(msg)
        self._log_text.verticalScrollBar().setValue(
            self._log_text.verticalScrollBar().maximum()
        )

    @pyqtSlot(bool)
    def _on_finished(self, success: bool):
        self._done = True
        self._btn_cancel.setEnabled(False)
        self._btn_close.setEnabled(True)
        if success:
            self._progress.setValue(len(PIPELINE_STEPS))
            self._log_text.append("\n✅ Analyse terminée avec succès !")
        else:
            self._log_text.append("\n❌ Analyse interrompue par une erreur.")

    def _on_cancel(self):
        self.orchestrator.cancel()
        self._btn_cancel.setEnabled(False)
        self._log_text.append("⚠ Annulation demandée…")