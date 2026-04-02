"""
gui/dashboard.py
================
Vue principale du dashboard.
Affiche les graphiques, la liste des clusters/intentions,
et l'historique. Supporte la navigation entre les dates.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QComboBox, QSplitter,
    QTabWidget, QListWidget, QListWidgetItem,
    QSizePolicy, QPushButton, QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor

from taskmonitor.core import storage
from taskmonitor.core.models import DayReport, Cluster
from taskmonitor.gui.charts import (
    TimelineChart, TopAppsChart, TypeDistributionChart,
    ClusterBubbleChart, HistoryChart, HourlyHeatmap,
)


# ─────────────────────────────────────────────
# CARTE STATISTIQUE (KPI)
# ─────────────────────────────────────────────

class StatCard(QFrame):
    """Petite carte affichant une valeur statistique clé."""

    STYLE = """
        QFrame {
            background-color: #1A1D27;
            border: 1px solid #2A2D3E;
            border-radius: 10px;
        }
    """

    def __init__(self, title: str, value: str = "—", unit: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(self.STYLE)
        self.setMinimumHeight(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(QFont("Segoe UI", 9))
        self._title_lbl.setStyleSheet("color: #64748B; border: none;")

        self._value_lbl = QLabel(value)
        self._value_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self._value_lbl.setStyleSheet("color: #E2E8F0; border: none;")

        self._unit_lbl = QLabel(unit)
        self._unit_lbl.setFont(QFont("Segoe UI", 9))
        self._unit_lbl.setStyleSheet("color: #64748B; border: none;")

        layout.addWidget(self._title_lbl)
        layout.addWidget(self._value_lbl)
        layout.addWidget(self._unit_lbl)

    def set_value(self, value: str, unit: str = ""):
        self._value_lbl.setText(value)
        self._unit_lbl.setText(unit)


# ─────────────────────────────────────────────
# CARTE CLUSTER / INTENTION
# ─────────────────────────────────────────────

class ClusterCard(QFrame):
    """Carte affichant un cluster avec son intention globale et ses items."""

    STYLE = """
        QFrame {
            background-color: #1A1D27;
            border: 1px solid #2A2D3E;
            border-radius: 10px;
        }
        QLabel { border: none; }
        QListWidget {
            background-color: #12151F;
            border: none;
            border-radius: 6px;
            color: #64748B;
            font-size: 11px;
            padding: 4px;
        }
        QListWidget::item { padding: 3px 6px; }
        QListWidget::item:hover { background-color: #1E2130; }
    """

    ACCENT_COLORS = [
        "#6366F1", "#14B8A6", "#F59E0B", "#F87171",
        "#4ADE80", "#A78BFA", "#38BDF8", "#FB923C",
    ]

    def __init__(self, cluster: Cluster, idx: int, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self.STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        color = self.ACCENT_COLORS[idx % len(self.ACCENT_COLORS)]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # En-tête
        header = QHBoxLayout()
        badge = QLabel(f"  {cluster.num_tasks} tâches  ")
        badge.setStyleSheet(
            f"background-color: {color}22; color: {color}; "
            f"border: 1px solid {color}44; border-radius: 4px; "
            f"font-size: 10px; padding: 1px 4px;"
        )
        badge.setFixedHeight(20)

        coh_lbl = QLabel(f"cohésion {cluster.cohesion:.2f}")
        coh_lbl.setStyleSheet("color: #475569; font-size: 9px;")
        coh_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

        header.addWidget(badge)
        header.addStretch()
        header.addWidget(coh_lbl)
        layout.addLayout(header)

        # Intention globale
        intention_lbl = QLabel(cluster.intention or cluster.label)
        intention_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        intention_lbl.setStyleSheet(f"color: {color};")
        intention_lbl.setWordWrap(True)
        layout.addWidget(intention_lbl)

        # Items (liste dépliable, max 5 visibles)
        if cluster.items:
            items_list = QListWidget()
            items_list.setMaximumHeight(min(len(cluster.items), 5) * 26 + 8)
            for item in cluster.items[:10]:
                short = item[:80] + "…" if len(item) > 80 else item
                items_list.addItem(QListWidgetItem(f"  {short}"))
            if len(cluster.items) > 10:
                items_list.addItem(QListWidgetItem(f"  … et {len(cluster.items) - 10} autres"))
            layout.addWidget(items_list)


# ─────────────────────────────────────────────
# ONGLET OVERVIEW
# ─────────────────────────────────────────────

class OverviewTab(QWidget):
    """Onglet principal : KPIs + heatmap + top apps + donut."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(14)

        # KPI row
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)
        self._card_events   = StatCard("Événements")
        self._card_duration = StatCard("Durée totale")
        self._card_apps     = StatCard("Applications")
        self._card_clusters = StatCard("Clusters")
        for card in [self._card_events, self._card_duration,
                     self._card_apps, self._card_clusters]:
            kpi_layout.addWidget(card)
        layout.addLayout(kpi_layout)

        # Heatmap horaire
        self._heatmap = HourlyHeatmap()
        layout.addWidget(self._heatmap)

        # Row: top apps + donut
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)
        self._top_apps = TopAppsChart()
        self._donut    = TypeDistributionChart()
        charts_row.addWidget(self._top_apps, stretch=3)
        charts_row.addWidget(self._donut, stretch=2)
        layout.addLayout(charts_row)

    def update(self, report: DayReport):
        self._card_events.set_value(str(report.num_events), "événements")
        self._card_duration.set_value(
            f"{report.total_duration:.0f}", "minutes"
        )
        apps = len({e.app for e in report.events if e.app})
        self._card_apps.set_value(str(apps), "apps distinctes")
        self._card_clusters.set_value(str(report.num_clusters), "clusters")

        self._heatmap.update(report)
        self._top_apps.update(report)
        self._donut.update(report)


# ─────────────────────────────────────────────
# ONGLET TIMELINE
# ─────────────────────────────────────────────

class TimelineTab(QScrollArea):
    """Onglet timeline scrollable."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        layout    = QVBoxLayout(container)
        layout.setContentsMargins(0, 10, 0, 0)

        self._timeline = TimelineChart()
        self._timeline.setMinimumHeight(400)
        layout.addWidget(self._timeline)
        layout.addStretch()
        self.setWidget(container)

    def update(self, report: DayReport):
        self._timeline.update(report)


# ─────────────────────────────────────────────
# ONGLET CLUSTERS / INTENTIONS
# ─────────────────────────────────────────────

class ClustersTab(QScrollArea):
    """Onglet listant tous les clusters avec leurs intentions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet("background: transparent; border: none;")

        self._container = QWidget()
        self._layout    = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 10, 0, 10)
        self._layout.setSpacing(10)
        self.setWidget(self._container)

        # Graphique bulles en haut
        self._bubble = ClusterBubbleChart()
        self._layout.addWidget(self._bubble)
        self._layout.addStretch()

    def update(self, report: DayReport):
        # Nettoyer les anciennes cartes (pas la bulle)
        while self._layout.count() > 1:
            item = self._layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        self._bubble.update(report)

        for i, cluster in enumerate(report.clusters):
            if not cluster.is_singleton or cluster.intention:
                card = ClusterCard(cluster, i)
                self._layout.insertWidget(self._layout.count(), card)

        self._layout.addStretch()


# ─────────────────────────────────────────────
# ONGLET HISTORIQUE
# ─────────────────────────────────────────────

class HistoryTab(QWidget):
    """Onglet affichant l'historique des jours précédents."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)

        self._history_chart = HistoryChart()
        layout.addWidget(self._history_chart)
        layout.addStretch()

    def refresh(self):
        """Charge l'historique depuis le storage."""
        dates = storage.list_available_dates()[:14]   # 14 derniers jours
        dates.reverse()   # ordre chronologique
        durations = []
        for d in dates:
            report = storage.load_day_report(d)
            durations.append(report.total_duration)
        self._history_chart.update(dates, durations)


# ─────────────────────────────────────────────
# DASHBOARD PRINCIPAL
# ─────────────────────────────────────────────

class Dashboard(QWidget):
    """
    Widget principal du dashboard.
    Contient le sélecteur de date et les onglets de visualisation.
    """

    date_changed = pyqtSignal(str)   # émis quand l'utilisateur change de date

    STYLE = """
        QWidget {
            background-color: #0F1117;
            color: #E2E8F0;
        }
        QComboBox {
            background-color: #1A1D27;
            color: #E2E8F0;
            border: 1px solid #2A2D3E;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 11px;
            min-width: 160px;
        }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background-color: #1A1D27;
            color: #E2E8F0;
            border: 1px solid #2A2D3E;
            selection-background-color: #2A2D3E;
        }
        QTabWidget::pane {
            border: none;
            background-color: #0F1117;
        }
        QTabBar::tab {
            background-color: #0F1117;
            color: #64748B;
            padding: 8px 18px;
            font-size: 10px;
            border-bottom: 2px solid transparent;
        }
        QTabBar::tab:selected {
            color: #6366F1;
            border-bottom: 2px solid #6366F1;
        }
        QTabBar::tab:hover {
            color: #E2E8F0;
        }
        QLabel#date_label {
            color: #E2E8F0;
            font-size: 22px;
            font-weight: bold;
        }
        QLabel#subtitle {
            color: #64748B;
            font-size: 11px;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self.STYLE)
        self._current_report: DayReport | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── En-tête ──────────────────────────
        header = QHBoxLayout()

        title_col = QVBoxLayout()
        self._date_lbl = QLabel("—")
        self._date_lbl.setObjectName("date_label")
        self._subtitle  = QLabel("Aucune analyse disponible pour ce jour")
        self._subtitle.setObjectName("subtitle")
        title_col.addWidget(self._date_lbl)
        title_col.addWidget(self._subtitle)
        header.addLayout(title_col)
        header.addStretch()

        # Sélecteur de date
        date_col = QVBoxLayout()
        date_col.setAlignment(Qt.AlignmentFlag.AlignRight)
        date_hint = QLabel("Sélectionner une date :")
        date_hint.setStyleSheet("color: #475569; font-size: 9px;")
        self._date_combo = QComboBox()
        self._date_combo.currentTextChanged.connect(self._on_date_selected)
        date_col.addWidget(date_hint)
        date_col.addWidget(self._date_combo)
        header.addLayout(date_col)

        layout.addLayout(header)

        # ── Onglets ──────────────────────────
        self._tabs = QTabWidget()
        self._tab_overview  = OverviewTab()
        self._tab_timeline  = TimelineTab()
        self._tab_clusters  = ClustersTab()
        self._tab_history   = HistoryTab()

        self._tabs.addTab(self._tab_overview, "Vue d'ensemble")
        self._tabs.addTab(self._tab_timeline, "Timeline")
        self._tabs.addTab(self._tab_clusters, "Clusters & Intentions")
        self._tabs.addTab(self._tab_history,  "Historique")

        layout.addWidget(self._tabs)

    # ── API publique ─────────────────────────

    def refresh_dates(self):
        """Recharge la liste des dates disponibles dans le combo."""
        dates = storage.list_available_dates()
        self._date_combo.blockSignals(True)
        self._date_combo.clear()
        for d in dates:
            self._date_combo.addItem(d)
        self._date_combo.blockSignals(False)
        if dates:
            self.load_date(dates[0])

    def load_date(self, date_str: str):
        """Charge et affiche les données d'une date."""
        report = storage.load_day_report(date_str)
        self._current_report = report

        self._date_lbl.setText(date_str)
        if report.monitoring_on:
            self._subtitle.setText(
                f"{report.num_events} événements  ·  "
                f"{report.total_duration:.0f} min d'activité  ·  "
                f"{report.num_clusters} clusters"
            )
        else:
            self._subtitle.setText("Monitoring non actif ce jour — données insuffisantes")

        self._tab_overview.update(report)
        self._tab_timeline.update(report)
        self._tab_clusters.update(report)
        self._tab_history.refresh()

    # ── Slots ─────────────────────────────────

    def _on_date_selected(self, date_str: str):
        if date_str:
            self.load_date(date_str)
            self.date_changed.emit(date_str)