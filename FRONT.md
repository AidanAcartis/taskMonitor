Parfait — ton idée est **très propre et déjà pensée comme une vraie app pro**. On va maintenant la transformer en **architecture PyQt6 concrète + intégration avec ton orchestrator**.

Je vais te donner :

1. **Structure des fichiers (dans ton repo)**
2. **Architecture UI PyQt6**
3. **Code de base prêt à intégrer**
4. **Connexion avec ton orchestrator (monitoring / processing)**

---

# 1️⃣ Structure à ajouter dans ton projet

Dans `taskmonitor/gui/` :

```
taskmonitor/gui/
│
├── main_window.py        # fenêtre principale
├── header.py            # header (menu + boutons)
├── navbar.py            # navigation (Dashboard, Graph…)
├── toolbar.py           # titre + loader + next/prev
│
├── pages/
│   ├── dashboard.py
│   ├── graph_stats.py
│   ├── chart.py
│   ├── monitoring.py
│   ├── processing.py
│   ├── settings.py
│   └── help.py
│
└── app.py               # point d’entrée GUI
```

---

# 2️⃣ Architecture UI (mapping de ton idée)

Tu as décrit 👇

### HEADER(TOOLBAR)

* gauche → menu (monitor / process)
* droite → aide / paramètres / quitter

### TOOLBARLAYOUT

* titre page
* loader
* next / prev

### NAVBAR

* Dashboard
* Graph & Stats
* Chart

### PAGES

* Dashboard
* Graph & Stats
* Chart
* Monitoring
* Processing
* Help
* Settings

👉 En PyQt6 ça devient :

```
QMainWindow
 ├── Header (QHBoxLayout)
 ├── Toolbar (QHBoxLayout)
 ├── Navbar (QVBoxLayout)
 └── QStackedWidget (pages)
```

---

# 3️⃣ Code principal (main_window.py)

Voici une base **fonctionnelle et clean** :

```python
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget
)
from PyQt6.QtCore import Qt

from taskmonitor.gui.pages.dashboard import DashboardPage
from taskmonitor.gui.pages.graph_stats import GraphStatsPage
from taskmonitor.gui.pages.chart import ChartPage
from taskmonitor.gui.pages.monitoring import MonitoringPage
from taskmonitor.gui.pages.processing import ProcessingPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TaskMonitor")
        self.resize(1200, 800)

        # ─────────────────────────
        # CENTRAL WIDGET
        # ─────────────────────────
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # ─────────────────────────
        # HEADER
        # ─────────────────────────
        header = QHBoxLayout()

        # gauche
        self.btn_monitor = QPushButton("Start Monitoring")
        self.btn_process = QPushButton("Run Processing")

        header.addWidget(self.btn_monitor)
        header.addWidget(self.btn_process)

        header.addStretch()

        # droite
        self.btn_help = QPushButton("Help")
        self.btn_settings = QPushButton("Settings")
        self.btn_quit = QPushButton("Quit")

        header.addWidget(self.btn_help)
        header.addWidget(self.btn_settings)
        header.addWidget(self.btn_quit)

        main_layout.addLayout(header)

        # ─────────────────────────
        # TOOLBAR
        # ─────────────────────────
        toolbar = QHBoxLayout()

        self.page_title = QLabel("Dashboard")
        self.loader = QLabel("Idle...")

        self.btn_prev = QPushButton("<")
        self.btn_next = QPushButton(">")

        toolbar.addWidget(self.page_title)
        toolbar.addStretch()
        toolbar.addWidget(self.loader)
        toolbar.addWidget(self.btn_prev)
        toolbar.addWidget(self.btn_next)

        main_layout.addLayout(toolbar)

        # ─────────────────────────
        # BODY
        # ─────────────────────────
        body = QHBoxLayout()

        # NAVBAR
        nav = QVBoxLayout()

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_graph = QPushButton("Graph & Stats")
        self.btn_chart = QPushButton("Chart")

        nav.addWidget(self.btn_dashboard)
        nav.addWidget(self.btn_graph)
        nav.addWidget(self.btn_chart)
        nav.addStretch()

        body.addLayout(nav)

        # STACKED PAGES
        self.stack = QStackedWidget()

        self.pages = {
            "dashboard": DashboardPage(),
            "graph": GraphStatsPage(),
            "chart": ChartPage(),
            "monitoring": MonitoringPage(),
            "processing": ProcessingPage(),
        }

        for p in self.pages.values():
            self.stack.addWidget(p)

        body.addWidget(self.stack)

        main_layout.addLayout(body)

        # ─────────────────────────
        # NAVIGATION LOGIC
        # ─────────────────────────
        self.btn_dashboard.clicked.connect(lambda: self.switch_page("dashboard"))
        self.btn_graph.clicked.connect(lambda: self.switch_page("graph"))
        self.btn_chart.clicked.connect(lambda: self.switch_page("chart"))

        self.btn_settings.clicked.connect(lambda: self.switch_page("settings"))
        self.btn_help.clicked.connect(lambda: self.switch_page("help"))

        self.btn_quit.clicked.connect(self.close)

    def switch_page(self, name):
        if name in self.pages:
            self.stack.setCurrentWidget(self.pages[name])
            self.page_title.setText(name.capitalize())
```

---

# 4️⃣ Connexion avec ton orchestrator 🔥

👉 C’est le point critique.

Tu dois lancer :

* monitoring (thread)
* processing (process)

---

## ➤ Monitoring (thread)

```python
from PyQt6.QtCore import QThread

from taskmonitor.orchestrator import run_monitoring

class MonitoringThread(QThread):
    def run(self):
        run_monitoring()
```

Dans `MainWindow` :

```python
self.monitor_thread = None

def start_monitoring(self):
    self.monitor_thread = MonitoringThread()
    self.monitor_thread.start()
    self.loader.setText("Monitoring...")

self.btn_monitor.clicked.connect(self.start_monitoring)
```

---

## ➤ Processing (safe subprocess)

```python
import subprocess

def run_processing(self):
    self.loader.setText("Processing...")

    subprocess.Popen(
        ["python3", "-m", "taskmonitor.orchestrator", "process"]
    )

self.btn_process.clicked.connect(self.run_processing)
```

---

# 5️⃣ Pages (exemple simple)

### dashboard.py

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Dashboard"))
        self.setLayout(layout)
```

👉 Tu feras ensuite :

* stats globales
* top clusters
* durée totale

---

# 6️⃣ Roadmap concrète pour toi

### Étape 1

✔ Créer UI (ce qu’on vient de faire)

### Étape 2

✔ Connecter monitoring / processing

### Étape 3

✔ Lire SQLite → afficher dans dashboard

### Étape 4

✔ Ajouter graphes (Matplotlib ou QtCharts)

### Étape 5

✔ Ajouter timeline (segments)

---

# 💡 Conseil important (niveau pro)

Ne mélange pas :

* UI
* logique (orchestrator)
* DB

👉 Tu fais déjà ça bien → continue comme ça.

---

# 🚀 Si tu veux aller plus loin

Je peux te faire :

* 🔥 un vrai **dashboard avec graphes (Matplotlib intégré PyQt6)**
* 🔥 une **timeline des segments**
* 🔥 une **lecture directe de ta SQLite dans le UI**

Dis-moi juste :
👉 *“on fait le dashboard réel maintenant”*
