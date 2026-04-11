"""
Help page — overview of all TaskMonitor features.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


SECTION_STYLE = """
    QLabel {
        font-size: 13px;
        font-weight: 500;
        color: #00bcd4;
        margin-top: 8px;
    }
"""

TITLE_STYLE = """
    QLabel {
        font-size: 22px;
        font-weight: 500;
        color: #e0e0e0;
    }
"""

SUBTITLE_STYLE = """
    QLabel {
        font-size: 13px;
        color: #666;
        margin-bottom: 16px;
    }
"""

ITEM_TITLE_STYLE = "font-size: 12px; font-weight: 500; color: #c9d1d9;"
ITEM_DESC_STYLE  = "font-size: 12px; color: #666; margin-bottom: 6px;"

DIVIDER_STYLE = """
    QFrame {
        color: #2a2a2a;
        background: #2a2a2a;
        border: none;
        max-height: 1px;
        margin: 12px 0px;
    }
"""


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(DIVIDER_STYLE)
    return line


def _section(title: str) -> QLabel:
    lbl = QLabel(title)
    lbl.setStyleSheet(SECTION_STYLE)
    return lbl


def _item(title: str, description: str) -> QWidget:
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(12, 4, 0, 0)
    layout.setSpacing(2)
    t = QLabel(title)
    t.setStyleSheet(ITEM_TITLE_STYLE)
    d = QLabel(description)
    d.setStyleSheet(ITEM_DESC_STYLE)
    d.setWordWrap(True)
    layout.addWidget(t)
    layout.addWidget(d)
    return w


class HelpPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ── outer layout ──────────────────────────────────────────────────────
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── scroll area ───────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #141414; }")

        content = QWidget()
        content.setStyleSheet("background: #141414;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 32, 40, 40)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── header ────────────────────────────────────────────────────────────
        title = QLabel("TaskMonitor — Help")
        title.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title)

        subtitle = QLabel(
            "TaskMonitor records your window activity and terminal commands, "
            "clusters them into meaningful tasks using AI, and visualizes your "
            "daily productivity."
        )
        subtitle.setStyleSheet(SUBTITLE_STYLE)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addWidget(_divider())

        # ── TOOLBAR ───────────────────────────────────────────────────────────
        layout.addWidget(_section("Toolbar"))
        layout.addWidget(_item(
            "● Monitoring button",
            "Opens a dropdown with three options: Start Monitoring (launches the "
            "window tracker and command collector), Stop Monitoring (terminates "
            "all monitoring processes including the bash script), and Show "
            "Monitoring (navigates to the Monitoring page)."
        ))
        layout.addWidget(_item(
            "⚙ Processing button",
            "Opens a dropdown with two options: Start Processing (runs the full "
            "AI pipeline — file collection, event parsing, description generation, "
            "clustering, intention prediction, and SQLite storage) and Show "
            "Processing (navigates to the Processing page)."
        ))
        layout.addWidget(_item(
            "‹ › Navigation arrows",
            "Browser-style back and forward buttons that move through your "
            "page history. The arrows are enabled only when history exists in "
            "that direction."
        ))
        layout.addWidget(_item(
            "? Help",
            "Opens this help page."
        ))
        layout.addWidget(_item(
            "⚙ Settings",
            "Opens the settings panel (coming soon)."
        ))
        layout.addWidget(_item(
            "⏻ Quit",
            "Closes the application."
        ))

        layout.addWidget(_divider())

        # ── MONITORING ────────────────────────────────────────────────────────
        layout.addWidget(_section("Monitoring"))
        layout.addWidget(_item(
            "What is monitored?",
            "Two data sources are collected in parallel: (1) window_changes.log — "
            "every window open/close event is recorded every 2 seconds by a bash "
            "script using wmctrl; (2) data_command.txt — your terminal commands "
            "are collected every 30 seconds via the command history."
        ))
        layout.addWidget(_item(
            "Process output (left panel)",
            "Shows the stdout of the orchestrator monitor process in real time — "
            "you will see '📥 Collecting command logs...' every 30 seconds."
        ))
        layout.addWidget(_item(
            "window_changes.log (right panel)",
            "Live tail of the log file. New window events appear here as they "
            "are detected. The file is reset each new day."
        ))
        layout.addWidget(_item(
            "Start / Stop",
            "Start launches both the bash window monitor and the Python command "
            "collector. Stop sends SIGINT to the entire process group, which "
            "triggers a clean shutdown of the bash script via SIGTERM."
        ))

        layout.addWidget(_divider())

        # ── PROCESSING ────────────────────────────────────────────────────────
        layout.addWidget(_section("Processing Pipeline"))
        layout.addWidget(_item(
            "Step 1 — File collection",
            "Extracts opened and closed file names from window_changes.log and "
            "computes duration spent on each file."
        ))
        layout.addWidget(_item(
            "Step 2 — Data merge",
            "Merges file events and command events into a single normalized "
            "CSV (events_normalized.csv)."
        ))
        layout.addWidget(_item(
            "Step 3 — Event parsing",
            "Standardizes all events into a unified format with timestamps, "
            "app names, file names, and raw text."
        ))
        layout.addWidget(_item(
            "Step 4 — AI Description (Gen_Desc_Model)",
            "A fine-tuned T5 model generates a natural language description "
            "for each unique file or application event. This enriches raw "
            "window titles into meaningful descriptions."
        ))
        layout.addWidget(_item(
            "Step 5 — Clustering (final_model)",
            "A sentence-transformer embedding model (MiniLM-L6-v2) computes "
            "semantic similarity between event descriptions. Agglomerative "
            "clustering groups related events into task clusters. The pipeline "
            "includes iterative reclustering, singleton merging, and "
            "post-processing to optimize cohesion and silhouette scores."
        ))
        layout.addWidget(_item(
            "Step 6 — Intention prediction (final_Model_V3)",
            "A fine-tuned Flan-T5 model predicts a short global task intention "
            "label for each cluster (e.g. 'Review directory contents', "
            "'Browse the internet')."
        ))
        layout.addWidget(_item(
            "Step 7 — Storage",
            "The final JSON output is hashed (MD5 on sorted cluster contents) "
            "and stored in a monthly SQLite database (~/.taskmonitor/db/). "
            "Duplicate sessions are automatically detected and skipped."
        ))

        layout.addWidget(_divider())

        # ── DASHBOARD ─────────────────────────────────────────────────────────
        layout.addWidget(_section("Dashboard"))
        layout.addWidget(_item(
            "Activity Heatmap",
            "A GitHub-style calendar showing daily activity intensity over the "
            "last 52 weeks. Color intensity reflects the number of clusters "
            "recorded that day. Click any cell to filter the timeline to that date."
        ))
        layout.addWidget(_item(
            "Timeline",
            "A vertical stem timeline showing all clusters for the selected "
            "session or date, grouped by day and sorted by start time. Each "
            "entry shows the task intention, time range, and duration."
        ))
        layout.addWidget(_item(
            "Session selector",
            "Choose a specific processing session (by date and time) to display "
            "in the timeline."
        ))
        layout.addWidget(_item(
            "Date selector",
            "Aggregate all clusters across all sessions for a specific calendar "
            "date, regardless of which session they were recorded in."
        ))

        layout.addWidget(_divider())

        # ── GRAPHS & STATS ────────────────────────────────────────────────────
        layout.addWidget(_section("Graphs & Stats"))
        layout.addWidget(_item(
            "Activity Duration",
            "Bar chart showing total active duration per cluster. Hover for "
            "details. Zoom in/out with the ＋/－ buttons. Export as PNG. "
            "Switch sessions or filter by date with the selectors."
        ))
        layout.addWidget(_item(
            "Gantt / Timeline",
            "Horizontal Gantt chart showing active segments per cluster across "
            "the day. Hover a segment to see its exact time range and duration. "
            "The time axis adapts automatically to the data span."
        ))
        layout.addWidget(_item(
            "Task Proportion (donut)",
            "Donut chart showing the proportion of time spent on each cluster "
            "intention. Hover a slice to see the percentage and duration."
        ))
        layout.addWidget(_item(
            "App Proportion (donut)",
            "Donut chart breaking down time by application (VS Code, Terminal, "
            "Chrome, Burp Suite, etc.)."
        ))
        layout.addWidget(_item(
            "Domain Proportion (donut)",
            "Donut chart categorizing time into domains: work, leisure, security, "
            "configuration, study, and other — based on keyword matching in "
            "event descriptions."
        ))
        layout.addWidget(_item(
            "Activity Heatmap (embed)",
            "The same GitHub-style heatmap as on the Dashboard, shown here "
            "alongside active day count and total session count statistics."
        ))
        layout.addWidget(_item(
            "Line Charts",
            "Two line chart modes available via the dropdown: (1) Activity by "
            "hour of day — aggregates all sessions and shows at which hours you "
            "are most active; (2) Domain over time — multi-line chart showing "
            "how time spent per domain evolves across sessions, dates, weeks, "
            "months, or years."
        ))

        layout.addWidget(_divider())

        # ── CHART PAGE ────────────────────────────────────────────────────────
        layout.addWidget(_section("Chart Page"))
        layout.addWidget(_item(
            "Duration per cluster (bar)",
            "Active duration in hours for each cluster, rendered with pyqtgraph."
        ))
        layout.addWidget(_item(
            "Cohesion per cluster (bar)",
            "Cohesion score (0–1) for each cluster. A dashed line marks 0.5. "
            "Green = high cohesion, orange = medium, red = low."
        ))
        layout.addWidget(_item(
            "Gantt timeline (pyqtgraph)",
            "Scrollable Gantt chart built with pyqtgraph BarGraphItems, "
            "with minute-resolution x-axis."
        ))
        layout.addWidget(_item(
            "Summary table",
            "Full tabular view of all clusters: ID, intention, start/end times, "
            "active duration, event count, cohesion score, and apps used."
        ))

        layout.addWidget(_divider())

        # ── DATA & STORAGE ────────────────────────────────────────────────────
        layout.addWidget(_section("Data & Storage"))
        layout.addWidget(_item(
            "SQLite database",
            "Sessions are stored monthly in ~/.taskmonitor/db/taskmonitor_YYYY_MM.db. "
            "Each row contains the session timestamp, a content hash for "
            "deduplication, and the full JSON data."
        ))
        layout.addWidget(_item(
            "Deduplication",
            "Before saving, the pipeline computes an MD5 hash of all cluster "
            "intentions (sorted) to detect identical outputs. If the same "
            "session is processed twice, it is not stored again."
        ))
        layout.addWidget(_item(
            "Raw exports",
            "Intermediate files are saved in data/exports/: clusters_output.txt, "
            "clusters_with_intentions.jsonl, and final_output.json. These are "
            "overwritten on each processing run."
        ))

        scroll.setWidget(content)
        outer.addWidget(scroll)