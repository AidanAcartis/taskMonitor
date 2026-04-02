"""
gui/charts.py
=============
Widgets de graphiques matplotlib intégrés dans PyQt6.
Chaque classe est un QWidget autonome qu'on peut placer dans n'importe quelle vue.
"""

from __future__ import annotations
from collections import defaultdict

import matplotlib
matplotlib.use("QtAgg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt

from taskmonitor.core.models import DayReport, Event, Cluster


# ─────────────────────────────────────────────
# PALETTE COHÉRENTE ENTRE TOUS LES GRAPHIQUES
# ─────────────────────────────────────────────

PALETTE = {
    "bg":        "#0F1117",
    "surface":   "#1A1D27",
    "border":    "#2A2D3E",
    "text":      "#E2E8F0",
    "muted":     "#64748B",
    "accent":    "#6366F1",   # indigo
    "teal":      "#14B8A6",
    "amber":     "#F59E0B",
    "coral":     "#F87171",
    "green":     "#4ADE80",
    "purple":    "#A78BFA",
}

CATEGORY_COLORS = {
    "file":      PALETTE["accent"],
    "app":       PALETTE["teal"],
    "command":   PALETTE["amber"],
    "directory": PALETTE["purple"],
}

APP_COLORS = [
    PALETTE["accent"], PALETTE["teal"], PALETTE["amber"],
    PALETTE["coral"], PALETTE["green"], PALETTE["purple"],
    "#38BDF8", "#FB923C", "#34D399", "#E879F9",
]


def _apply_dark_style(fig: Figure, ax) -> None:
    """Applique le thème sombre à une figure matplotlib."""
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["surface"])
    ax.tick_params(colors=PALETTE["muted"], labelsize=9)
    ax.xaxis.label.set_color(PALETTE["muted"])
    ax.yaxis.label.set_color(PALETTE["muted"])
    for spine in ax.spines.values():
        spine.set_edgecolor(PALETTE["border"])
    ax.grid(color=PALETTE["border"], linewidth=0.5, alpha=0.6)


# ─────────────────────────────────────────────
# BASE WIDGET
# ─────────────────────────────────────────────

class ChartWidget(QWidget):
    """Widget de base pour tous les graphiques."""

    def __init__(self, parent=None, figsize=(6, 3.5)):
        super().__init__(parent)
        self.fig    = Figure(figsize=figsize, dpi=100, tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def clear(self):
        self.fig.clear()

    def refresh(self):
        self.canvas.draw()


# ─────────────────────────────────────────────
# 1. TIMELINE — activités dans la journée
# ─────────────────────────────────────────────

class TimelineChart(ChartWidget):
    """
    Graphique horizontal Gantt-like montrant les événements dans le temps.
    Axe X = heures de la journée, une barre par événement colorée par type.
    """

    def __init__(self, parent=None):
        super().__init__(parent, figsize=(8, 4))

    def update(self, report: DayReport) -> None:
        self.clear()
        ax = self.fig.add_subplot(111)
        _apply_dark_style(self.fig, ax)

        if not report.events:
            ax.text(0.5, 0.5, "Aucune donnée disponible",
                    ha="center", va="center", color=PALETTE["muted"],
                    transform=ax.transAxes, fontsize=12)
            self.refresh()
            return

        # Convertir HH:MM:SS → minutes depuis minuit
        def to_min(t: str) -> float:
            try:
                h, m, s = t.split(":")
                return int(h) * 60 + int(m) + int(s) / 60
            except Exception:
                return 0.0

        events_sorted = sorted(report.events, key=lambda e: e.start)
        y_labels = []
        y_pos    = []

        for i, event in enumerate(events_sorted):
            start_min = to_min(event.start)
            end_min   = to_min(event.end)
            width     = max(end_min - start_min, 0.5)   # min 0.5 min pour la visibilité
            color     = CATEGORY_COLORS.get(event.event_type, PALETTE["muted"])
            label     = (event.file or event.app or event.command or event.raw)[:30]

            ax.barh(i, width, left=start_min, height=0.6,
                    color=color, alpha=0.85, linewidth=0)
            y_labels.append(label)
            y_pos.append(i)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(y_labels, fontsize=8, color=PALETTE["text"])
        ax.set_xlabel("Heure (minutes depuis minuit)", color=PALETTE["muted"], fontsize=9)
        ax.set_title(f"Timeline — {report.date_str}", color=PALETTE["text"],
                     fontsize=11, pad=10)

        # Légende types
        legend_patches = [
            mpatches.Patch(color=c, label=t)
            for t, c in CATEGORY_COLORS.items()
        ]
        ax.legend(handles=legend_patches, loc="upper right",
                  facecolor=PALETTE["surface"], edgecolor=PALETTE["border"],
                  labelcolor=PALETTE["text"], fontsize=8)

        # Axe X en heures
        max_min = max(to_min(e.end) for e in report.events)
        ticks   = list(range(0, int(max_min) + 60, 60))
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{t//60:02d}h" for t in ticks],
                            color=PALETTE["muted"], fontsize=8)
        self.refresh()


# ─────────────────────────────────────────────
# 2. TOP APPS — durées par application
# ─────────────────────────────────────────────

class TopAppsChart(ChartWidget):
    """Barres horizontales des applications les plus utilisées."""

    def __init__(self, parent=None):
        super().__init__(parent, figsize=(6, 3.5))

    def update(self, report: DayReport, top_n: int = 8) -> None:
        self.clear()
        ax = self.fig.add_subplot(111)
        _apply_dark_style(self.fig, ax)

        top = report.top_apps[:top_n]
        if not top:
            ax.text(0.5, 0.5, "Aucune application détectée",
                    ha="center", va="center", color=PALETTE["muted"],
                    transform=ax.transAxes, fontsize=11)
            self.refresh()
            return

        apps, durations = zip(*top)
        y = range(len(apps))

        bars = ax.barh(list(y), list(durations),
                       color=APP_COLORS[:len(apps)],
                       height=0.6, alpha=0.9, linewidth=0)

        # Labels de valeur à droite des barres
        for bar, dur in zip(bars, durations):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f"{dur:.1f} min", va="center", ha="left",
                    color=PALETTE["muted"], fontsize=8)

        ax.set_yticks(list(y))
        ax.set_yticklabels(apps, color=PALETTE["text"], fontsize=9)
        ax.set_xlabel("Durée (minutes)", color=PALETTE["muted"], fontsize=9)
        ax.set_title("Applications les plus utilisées", color=PALETTE["text"],
                     fontsize=11, pad=10)
        ax.invert_yaxis()
        self.refresh()


# ─────────────────────────────────────────────
# 3. RÉPARTITION PAR TYPE — donut chart
# ─────────────────────────────────────────────

class TypeDistributionChart(ChartWidget):
    """Donut chart de la répartition file / app / command / directory."""

    def __init__(self, parent=None):
        super().__init__(parent, figsize=(5, 4))

    def update(self, report: DayReport) -> None:
        self.clear()
        ax = self.fig.add_subplot(111)
        _apply_dark_style(self.fig, ax)
        ax.set_aspect("equal")

        totals: dict[str, float] = defaultdict(float)
        for e in report.events:
            totals[e.event_type] += e.duration

        if not totals:
            ax.text(0.5, 0.5, "Aucune donnée",
                    ha="center", va="center", color=PALETTE["muted"],
                    transform=ax.transAxes, fontsize=11)
            self.refresh()
            return

        labels = list(totals.keys())
        sizes  = list(totals.values())
        colors = [CATEGORY_COLORS.get(l, PALETTE["muted"]) for l in labels]

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors,
            autopct="%1.1f%%", pctdistance=0.75,
            wedgeprops=dict(width=0.5, edgecolor=PALETTE["bg"], linewidth=2),
            startangle=90,
        )
        for t in texts:
            t.set_color(PALETTE["text"])
            t.set_fontsize(9)
        for at in autotexts:
            at.set_color(PALETTE["bg"])
            at.set_fontsize(8)
            at.set_fontweight("bold")

        ax.set_title("Répartition par type", color=PALETTE["text"],
                     fontsize=11, pad=10)
        self.refresh()


# ─────────────────────────────────────────────
# 4. CLUSTERS BUBBLES — taille = nb tâches
# ─────────────────────────────────────────────

class ClusterBubbleChart(ChartWidget):
    """
    Scatter chart où chaque cluster est une bulle.
    Taille = nombre de tâches, couleur = cohésion.
    """

    def __init__(self, parent=None):
        super().__init__(parent, figsize=(7, 4))

    def update(self, report: DayReport) -> None:
        self.clear()
        ax = self.fig.add_subplot(111)
        _apply_dark_style(self.fig, ax)

        clusters = [c for c in report.clusters if not c.is_singleton]
        if not clusters:
            ax.text(0.5, 0.5, "Aucun cluster disponible",
                    ha="center", va="center", color=PALETTE["muted"],
                    transform=ax.transAxes, fontsize=11)
            self.refresh()
            return

        x      = range(len(clusters))
        sizes  = [max(c.num_tasks * 200, 100) for c in clusters]
        cohs   = [c.cohesion for c in clusters]

        sc = ax.scatter(list(x), [0] * len(clusters),
                        s=sizes, c=cohs, cmap="RdYlGn_r",
                        vmin=0, vmax=1, alpha=0.85,
                        edgecolors=PALETTE["border"], linewidths=1)

        for i, c in enumerate(clusters):
            short = c.intention[:28] + "…" if len(c.intention) > 28 else c.intention
            ax.annotate(short, (i, 0),
                        xytext=(0, -(sizes[i] ** 0.5) / 2 - 12),
                        textcoords="offset points",
                        ha="center", va="top",
                        color=PALETTE["text"], fontsize=7.5,
                        wrap=True)

        cbar = self.fig.colorbar(sc, ax=ax, orientation="vertical", pad=0.01)
        cbar.set_label("Cohésion", color=PALETTE["muted"], fontsize=8)
        cbar.ax.yaxis.set_tick_params(color=PALETTE["muted"])
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color=PALETTE["muted"], fontsize=8)

        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("Clusters d'activités (taille = nb tâches)",
                     color=PALETTE["text"], fontsize=11, pad=10)
        for spine in ax.spines.values():
            spine.set_visible(False)

        self.refresh()


# ─────────────────────────────────────────────
# 5. HISTORIQUE — durées sur plusieurs jours
# ─────────────────────────────────────────────

class HistoryChart(ChartWidget):
    """Courbe de l'activité totale (minutes) sur les N derniers jours."""

    def __init__(self, parent=None):
        super().__init__(parent, figsize=(8, 3))

    def update(self, dates: list[str], durations: list[float]) -> None:
        self.clear()
        ax = self.fig.add_subplot(111)
        _apply_dark_style(self.fig, ax)

        if not dates:
            ax.text(0.5, 0.5, "Aucun historique disponible",
                    ha="center", va="center", color=PALETTE["muted"],
                    transform=ax.transAxes, fontsize=11)
            self.refresh()
            return

        x = range(len(dates))
        ax.fill_between(list(x), durations, alpha=0.25, color=PALETTE["accent"])
        ax.plot(list(x), durations, color=PALETTE["accent"],
                linewidth=2, marker="o", markersize=5,
                markerfacecolor=PALETTE["accent"], markeredgecolor=PALETTE["bg"])

        # Labels de valeur au-dessus des points
        for xi, (date, dur) in enumerate(zip(dates, durations)):
            ax.annotate(f"{dur:.0f}m", (xi, dur),
                        xytext=(0, 6), textcoords="offset points",
                        ha="center", color=PALETTE["text"], fontsize=7.5)

        ax.set_xticks(list(x))
        ax.set_xticklabels([d[5:] for d in dates],   # MM-DD
                            color=PALETTE["muted"], fontsize=8, rotation=30)
        ax.set_ylabel("Minutes d'activité", color=PALETTE["muted"], fontsize=9)
        ax.set_title("Activité sur les derniers jours",
                     color=PALETTE["text"], fontsize=11, pad=10)
        self.refresh()


# ─────────────────────────────────────────────
# 6. HEATMAP HORAIRE — activité par heure
# ─────────────────────────────────────────────

class HourlyHeatmap(ChartWidget):
    """Heatmap montrant l'intensité d'activité par tranche horaire."""

    def __init__(self, parent=None):
        super().__init__(parent, figsize=(8, 2.5))

    def update(self, report: DayReport) -> None:
        self.clear()
        ax = self.fig.add_subplot(111)
        _apply_dark_style(self.fig, ax)

        hourly = np.zeros(24)

        for e in report.events:
            try:
                h = int(e.start.split(":")[0])
                hourly[h] += e.duration
            except Exception:
                continue

        im = ax.imshow(
            hourly.reshape(1, 24),
            aspect="auto", cmap="YlOrRd",
            vmin=0, vmax=max(hourly.max(), 1),
        )
        ax.set_xticks(range(0, 24, 2))
        ax.set_xticklabels([f"{h:02d}h" for h in range(0, 24, 2)],
                            color=PALETTE["muted"], fontsize=8)
        ax.set_yticks([])
        ax.set_title("Intensité horaire (minutes d'activité)",
                     color=PALETTE["text"], fontsize=11, pad=8)

        cbar = self.fig.colorbar(im, ax=ax, orientation="vertical",
                                  pad=0.01, aspect=10)
        cbar.ax.yaxis.set_tick_params(color=PALETTE["muted"])
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color=PALETTE["muted"], fontsize=7)
        self.refresh()