# TaskMonitor

Moniteur d'activité bureau avec analyse IA et visualisation.

Surveille automatiquement les fenêtres ouvertes, les fichiers édités et les commandes bash, puis génère une analyse complète avec clustering et intentions globales de tâches.

---

## Architecture

```
taskmonitor/
├── taskmonitor/
│   ├── core/               ← modules partagés (config, models, storage, logger)
│   ├── collectors/         ← collecte des données brutes
│   ├── processing/         ← pipeline de traitement IA
│   ├── gui/                ← interface PyQt6
│   ├── autostart/          ← installation raccourcis
│   ├── orchestrator.py     ← chef d'orchestre du pipeline
│   └── main.py             ← point d'entrée
├── data/                   ← données locales (générées, non versionnées)
├── models/                 ← modèles IA (non versionnés, copier manuellement)
├── assets/                 ← icône et ressources
├── requirements.txt
├── pyproject.toml
└── setup_env.sh
```

---

## Installation rapide

### Sur votre machine (Ubuntu 22.04 / 24.04)

```bash
git clone <url-du-repo> taskmonitor
cd taskmonitor
chmod +x setup_env.sh
./setup_env.sh
```

Le script installe automatiquement :
- `wmctrl` (surveillance des fenêtres)
- L'environnement conda `MLproject_py311`
- Toutes les dépendances Python
- `cmddesc` (description des commandes)
- L'autostart au démarrage de session
- Un raccourci bureau

### Sur une nouvelle machine

1. Copier le dossier du projet
2. Copier les modèles IA dans `~/Documents/Projects/Visualization/Vis_Models/`
   (ou définir `TASKMONITOR_MODELS_DIR=/chemin/vers/models`)
3. Lancer `./setup_env.sh`

---

## Lancement

```bash
taskmonitor
```

L'application se lance en arrière-plan avec une icône dans le system tray.

---

## Pipeline de traitement

| Étape | Module | Description |
|-------|--------|-------------|
| 1 | `collectors/window_monitor.py` | Surveillance wmctrl → log |
| 2 | `collectors/file_collector.py` | Extraction ouvertures/fermetures |
| 3 | `collectors/file_collector.py` | Calcul des durées |
| 4 | `collectors/command_collector.py` | Collecte bash_history |
| 5 | `processing/assembler.py` | Assemblage TSV unifié |
| 6 | `processing/parser.py` | Normalisation CSV |
| 7 | `processing/describer.py` | Description IA (T5 + cmddesc) |
| 8 | `processing/clusterer.py` | Clustering sémantique |
| 9 | `processing/intention_predictor.py` | Intentions globales |

---

## Modèles requis

| Modèle | Chemin par défaut | Usage |
|--------|-------------------|-------|
| Gen_Desc_Model | `Vis_Models/Gen_Desc_Model/full_finetuned/` | Description des fichiers |
| final_model | `Vis_Models/final_model/` | Clustering (SentenceTransformer) |
| final_Model_V3 | `Vis_Models/final_Model_V3/final_model/` | Génération d'intentions |

Chemin personnalisable :
```bash
export TASKMONITOR_MODELS_DIR=/chemin/vers/models
```

---

## Données

Les données sont stockées dans `~/.taskmonitor/data/` :

```
~/.taskmonitor/data/
├── logs/YYYY-MM-DD/window_changes.log
├── processed/YYYY-MM-DD/
│   ├── Opened_file.txt
│   ├── Closed_file.txt
│   ├── data_collect.txt
│   ├── events_normalized.csv
│   ├── events_described.csv
│   └── clusters_output.txt
└── exports/YYYY-MM-DD/
    ├── clusters_with_intentions.jsonl
    └── clusters_with_intentions.txt
```

Chaque journée est conservée indéfiniment et consultable depuis l'interface.

---

## Variables d'environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `TASKMONITOR_DATA_DIR` | `~/.taskmonitor/data` | Dossier de données |
| `TASKMONITOR_MODELS_DIR` | `~/Documents/Projects/Visualization/Vis_Models` | Dossier modèles IA |