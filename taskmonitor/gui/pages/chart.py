from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QTextEdit, QPushButton, QDialogButtonBox
)

from PyQt6.QtCore import Qt
import pyqtgraph as pg
from taskmonitor.gui.widgets.session_selector import SessionSelector


CLUSTER  = "#378ADD"
SINGLE   = "#7F77DD"
BG_PANEL = "#252525"
FG       = "#e0e0e0"
FG_MUTED = "#888888"


def _bar_color(cid: str) -> str:
    return SINGLE if "singleton" in cid.lower() else CLUSTER


def _make_plot() -> pg.PlotWidget:
    pw = pg.PlotWidget()
    pw.setBackground(BG_PANEL)
    pw.getAxis("bottom").setPen(pg.mkPen(FG_MUTED))
    pw.getAxis("left").setPen(pg.mkPen(FG_MUTED))
    pw.getAxis("bottom").setTextPen(pg.mkPen(FG_MUTED))
    pw.getAxis("left").setTextPen(pg.mkPen(FG_MUTED))
    pw.showGrid(x=False, y=True, alpha=0.15)
    pw.setMenuEnabled(False)
    return pw


def _titled(title: str, widget: QWidget) -> QWidget:
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    lbl = QLabel(title)
    lbl.setStyleSheet(f"color: {FG}; font-size: 13px; font-weight: 500;")
    layout.addWidget(lbl)
    layout.addWidget(widget)
    return container


class Chart(QWidget):
    def __init__(self, data: dict):
        super().__init__()
        self.data = data
        self.clusters = data.get("clusters", [])
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)          # <-- 'layout', pas 'root'
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        ctrl = QHBoxLayout()
        lbl = QLabel("Visualisation :")
        lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 13px;")

        self._selector = SessionSelector()
        self._selector.session_changed.connect(self._on_session_changed)
        ctrl.addWidget(self._selector)

        self.combo = QComboBox()
        self.combo.addItems([               # <-- un seul addItems
            "Active duration per cluster",
            "Cohesion per cluster",
            "Gantt Timeline",
            "Summary table",
        ])
        self.combo.setFixedWidth(240)
        self.combo.setStyleSheet(f"""
            QComboBox {{
                background: {BG_PANEL}; color: {FG};
                border: 1px solid #3a3a3a; border-radius: 4px;
                padding: 3px 8px; font-size: 13px;
            }}
            QComboBox QAbstractItemView {{
                background: {BG_PANEL}; color: {FG};
                selection-background-color: #333;
            }}
        """)
        self.combo.currentIndexChanged.connect(self._switch)
        ctrl.addWidget(lbl)
        ctrl.addWidget(self.combo)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.chart_duration = _titled(
            "Active duration per cluster (hours)", self._build_duration()
        )
        self.chart_cohesion = _titled(
            "Cohesion score per cluster", self._build_cohesion()
        )
        self.chart_gantt = _titled(
            "Gantt Timeline — active segments", self._build_gantt()
        )
        self.chart_table = _titled(
            "Cluster summary table", self._build_table()
        )

        for w in (self.chart_duration, self.chart_cohesion,
                  self.chart_gantt, self.chart_table):
            layout.addWidget(w)

        self._switch(0)

    def _build_duration(self) -> pg.PlotWidget:
        clusters = self.clusters
        labels   = [c["cluster_id"] for c in clusters]
        values   = [c["stats"]["active_duration"] for c in clusters]
        colors   = [_bar_color(c["cluster_id"]) for c in clusters]

        pw = _make_plot()
        pw.setLabel("left", "Hours", color=FG_MUTED)
        pw.getAxis("bottom").setTicks(
            [[(i, self._short_id(lbl)) for i, lbl in enumerate(labels)]]
        )
        for i, (v, col) in enumerate(zip(values, colors)):
            pw.addItem(pg.BarGraphItem(
                x=[i], height=[v], width=0.6,
                brush=pg.mkBrush(col), pen=pg.mkPen(None)
            ))
        pw.setXRange(-0.6, len(labels) - 0.4)
        pw.setYRange(0, max(values) * 1.15)
        return pw

    def _build_cohesion(self) -> pg.PlotWidget:
        clusters = self.clusters
        labels   = [c["cluster_id"] for c in clusters]
        values   = [c["cohesion"] for c in clusters]
        colors   = [_bar_color(c["cluster_id"]) for c in clusters]

        pw = _make_plot()
        pw.setLabel("left", "Cohesion [0–1]", color=FG_MUTED)
        pw.getAxis("bottom").setTicks(
            [[(i, self._short_id(lbl)) for i, lbl in enumerate(labels)]]
        )
        for i, (v, col) in enumerate(zip(values, colors)):
            pw.addItem(pg.BarGraphItem(
                x=[i], height=[v], width=0.6,
                brush=pg.mkBrush(col), pen=pg.mkPen(None)
            ))
        pw.addItem(pg.InfiniteLine(
            pos=0.5, angle=0,
            pen=pg.mkPen(color="#ffffff", style=Qt.PenStyle.DashLine, width=1)
        ))
        pw.setXRange(-0.6, len(labels) - 0.4)
        pw.setYRange(0, 1.05)
        return pw

    def _build_gantt(self) -> QScrollArea:
        clusters  = self.clusters
        all_times = []
        for c in clusters:
            for seg in c.get("segments", []):
                all_times.append(self._to_minutes(seg["start"]))
                all_times.append(self._to_minutes(seg["end"]))

        t_min = min(all_times)
        t_max = max(all_times)
        span  = t_max - t_min

        pw = _make_plot()
        pw.setLabel("bottom", "Hour (HH:MM)", color=FG_MUTED)
        pw.setLabel("left",   "Cluster",        color=FG_MUTED)

        y_labels = []
        for row, c in enumerate(clusters):
            cid = c["cluster_id"]
            col = _bar_color(cid)
            y_labels.append((row, self._short_id(cid)))
            for seg in c.get("segments", []):
                x0  = self._to_minutes(seg["start"]) - t_min
                dur = self._to_minutes(seg["end"]) - self._to_minutes(seg["start"])
                pw.addItem(pg.BarGraphItem(
                    x0=[x0], x1=[x0 + max(dur, 0.5)],
                    y0=[row - 0.35], y1=[row + 0.35],
                    brush=pg.mkBrush(col), pen=pg.mkPen(None)
                ))

        step = max(1, round(span / 8))
        x_ticks = []
        for m in range(0, int(span) + step, step):
            abs_m = t_min + m
            h, mn = divmod(int(abs_m), 60)
            x_ticks.append((m, f"{h:02d}:{mn:02d}"))
        pw.getAxis("bottom").setTicks([x_ticks])
        pw.getAxis("left").setTicks([y_labels])
        pw.setXRange(-1, span + 1)
        pw.setYRange(-0.8, len(clusters) - 0.2)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(pw)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        return scroll

    def _build_table(self) -> QTableWidget:
        columns = ["ID", "Intention", "Start", "End",
                "Active duration (h)", "Events", "Cohesion", "Apps", "Items"]
        clusters = self.clusters
        table = QTableWidget(len(clusters), len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_PANEL};
                color: {FG};
                gridline-color: #3a3a3a;
                border: none;
                font-size: 12px;
            }}
            QTableWidget::item {{ padding: 4px 8px; }}
            QTableWidget::item:selected {{ background-color: #2a3a4a; color: {FG}; }}
            QTableWidget::item:alternate {{ background-color: #1e1e1e; }}
            QHeaderView::section {{
                background-color: #1a1a1a;
                color: {FG_MUTED};
                font-size: 11px;
                font-weight: 500;
                padding: 4px 8px;
                border: none;
                border-bottom: 1px solid #3a3a3a;
            }}
        """)

        for row, c in enumerate(clusters):
            stats   = c["stats"]
            apps    = sorted({e["app"] for e in c.get("events", []) if e.get("app")})
            start_t = stats["start"].split(" ")[-1][:5]
            end_t   = stats["end"].split(" ")[-1][:5]

            cells = [
                c["cluster_id"],
                c.get("global_task_intention", "—"),
                start_t,
                end_t,
                f"{stats['active_duration']:.3f}",
                str(stats["num_events"]),
                f"{c['cohesion']:.3f}",
                ", ".join(apps),
            ]

            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                )
                if col == 6:
                    val = c["cohesion"]
                    color = "#5DCAA5" if val >= 0.7 else "#EF9F27" if val >= 0.35 else "#F09595"
                    item.setForeground(pg.mkColor(color))
                if col == 0:
                    item.setForeground(pg.mkColor(
                        SINGLE if "singleton" in text.lower() else CLUSTER
                    ))
                table.setItem(row, col, item)

            # ── bouton Items ──────────────────────────────────────────────────────
            task_items = c.get("task_items", [])
            btn = QPushButton(f"View ({len(task_items)})")
            btn.setFixedHeight(22)
            btn.setStyleSheet("""
                QPushButton {
                    color: #aaa; background: #2a2a2a;
                    border: 1px solid #444; border-radius: 3px;
                    padding: 0 6px; font-size: 11px;
                }
                QPushButton:hover { background: #333; color: #fff; }
            """)
            btn.clicked.connect(lambda _, cl=c: self._show_items_popup(cl))
            table.setCellWidget(row, 8, btn)

        table.resizeColumnsToContents()
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(8, 90)
        return table

    def _show_items_popup(self, cluster: dict):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{cluster['cluster_id']} — Items")
        dialog.setMinimumSize(600, 400)
        dialog.setStyleSheet("background-color: #1a1a1a; color: #ccc;")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ── titre ──────────────────────────────────────────────────────────────
        title = QLabel(cluster.get("global_task_intention", "—"))
        title.setStyleSheet("font-size: 13px; font-weight: 500; color: #ddd;")
        title.setWordWrap(True)
        layout.addWidget(title)

        # ── contenu ────────────────────────────────────────────────────────────
        viewer = QTextEdit()
        viewer.setReadOnly(True)
        viewer.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
                font-family: Monospace;
                font-size: 11px;
            }
        """)

        task_items = cluster.get("task_items", [])
        if task_items:
            lines = []
            for i, item in enumerate(task_items, 1):
                desc = item.get("description", str(item))
                dur  = item.get("total_duration", 0)
                dur_str = f"{dur:.1f} min" if dur else ""
                lines.append(f"{i:>2}. {desc}  {dur_str}")
            viewer.setPlainText("\n".join(lines))
        else:
            # fallback sur events si task_items vide
            events = cluster.get("events", [])
            lines = [f"{i:>2}. {e.get('raw', str(e))}" for i, e in enumerate(events, 1)]
            viewer.setPlainText("\n".join(lines) if lines else "No items.")

        layout.addWidget(viewer)

        # ── bouton fermer ───────────────────────────────────────────────────────
        btn_close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_close.setStyleSheet("color: #aaa;")
        btn_close.rejected.connect(dialog.reject)
        layout.addWidget(btn_close)

        dialog.exec()

    @staticmethod
    def _short_id(cid: str) -> str:
        if "singleton" in cid.lower():
            parts = cid.split()
            return "Sing. " + parts[-1] if parts else cid
        return cid.replace("Cluster ", "C")

    @staticmethod
    def _to_minutes(ts: str) -> float:
        parts = ts.split()
        time_part = parts[-1] if len(parts) > 1 else parts[0]
        h, m, s = time_part.split(":")
        return int(h) * 60 + int(m) + int(s) / 60

    def _switch(self, idx: int):
        self.chart_duration.setVisible(idx == 0)
        self.chart_cohesion.setVisible(idx == 1)
        self.chart_gantt.setVisible(idx == 2)
        self.chart_table.setVisible(idx == 3)

    def _on_session_changed(self, data: dict):
        self.data     = data
        self.clusters = data.get("clusters", [])
        # rebuild all sub-charts
        layout = self.layout()
        for w in (self.chart_duration, self.chart_cohesion,
                self.chart_gantt, self.chart_table):
            layout.removeWidget(w)
            w.deleteLater()
        self.chart_duration = _titled("Active duration per cluster (hours)", self._build_duration())
        self.chart_cohesion = _titled("Cohesion score per cluster",     self._build_cohesion())
        self.chart_gantt    = _titled("Gantt Timeline — active segments",  self._build_gantt())
        self.chart_table    = _titled("Cluster summary table", self._build_table())
        for w in (self.chart_duration, self.chart_cohesion,
                self.chart_gantt, self.chart_table):
            layout.addWidget(w)
        self._switch(self.combo.currentIndex())