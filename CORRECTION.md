Tu as 3 problèmes distincts, tous liés à la nature du conteneur Docker. Voici l'analyse et les solutions :

---

## Problème 1 — Background blanc (PyQt6 / thème)

**Cause :** Dans le conteneur, il n'y a pas de gestionnaire de fenêtres ni de thème Qt installé. PyQt6 utilise alors le style par défaut "Fusion" en mode clair au lieu de ton thème sombre local.

**Solution :** Forcer le style sombre directement dans le code `app.py` :

```python
# Dans taskmonitor/gui/app.py, après QApplication(sys.argv)
app.setStyle("Fusion")

from PyQt6.QtGui import QPalette, QColor
palette = QPalette()
palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
palette.setColor(QPalette.ColorRole.WindowText, QColor(200, 200, 200))
palette.setColor(QPalette.ColorRole.Base, QColor(18, 18, 18))
palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
palette.setColor(QPalette.ColorRole.Text, QColor(200, 200, 200))
palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
palette.setColor(QPalette.ColorRole.ButtonText, QColor(200, 200, 200))
app.setPalette(palette)
```

---

## Problème 2 — Monitoring : `.bash_history` introuvable + heure fausse

**Cause A — bash_history :** Le conteneur tourne en `root` et démarre sans session bash interactive, donc `/root/.bash_history` n'existe pas.

**Solution :** Monter ton `.bash_history` depuis ta machine hôte dans le `docker-compose.yml` :

```yaml
volumes:
  - ${HOME}/.bash_history:/root/.bash_history:ro
```

**Cause B — heure fausse :** Le conteneur est en UTC par défaut. Si tu es à UTC+3 (Madagascar), l'écart de 3h explique exactement ce que tu vois.

**Solution :** Ajouter la timezone dans `docker-compose.yml` :

```yaml
environment:
  - TZ=Indian/Antananarivo
```

Et dans le `Dockerfile`, installer `tzdata` :

```dockerfile
RUN apt-get update && apt-get install -y \
    tzdata \
    ...
```

**Cause C — window_monitor.sh :** Le script contient `export XAUTHORITY=/home/aidan/.Xauthority` — chemin codé en dur vers ta machine. Dans le conteneur c'est `/tmp/.docker.xauth`.

**Solution :** Modifier `window_monitor.sh` pour utiliser une variable d'environnement :

```bash
# Remplacer :
export XAUTHORITY=/home/aidan/.Xauthority

# Par :
export XAUTHORITY="${XAUTHORITY:-/home/aidan/.Xauthority}"
```

Le `docker-compose.yml` passe déjà `XAUTHORITY=/tmp/.docker.xauth` donc ça sera pris automatiquement.

---

## Problème 3 — Graphes non mis à jour / base de données

**Cause :** Le conteneur écrit dans `/root/.taskmonitor/db/taskmonitor_2026_04.db` (volume monté sur `~/.taskmonitor`). Mais l'app GUI charge les données **au démarrage** une seule fois dans `main_window.py` :

```python
data = load_latest_session() or {"clusters": []}  # chargé UNE FOIS
```

Donc après un processing, les graphes ne se rafraîchissent pas automatiquement.

**Solution :** Ajouter un bouton "Refresh" ou un signal après le processing. Dans `processing.py`, émettre un signal à la fin :

```python
# Dans ProcessingPage
finished_processing = pyqtSignal()  # ajouter ce signal

def _on_ok(self):
    self._status.setText("✔ Completed")
    self._status.setStyleSheet("font-size: 12px; color: #26a641;")
    self._btn_run.setEnabled(True)
    self.finished_processing.emit()  # émettre le signal
```

Et dans `main_window.py`, connecter ce signal pour recharger les données :

```python
self.page_processing.finished_processing.connect(self._reload_data)

def _reload_data(self):
    data = load_latest_session() or {"clusters": []}
    self.page_graphstats.update_data(data)
    self.page_chart._on_session_changed(data)
    self.page_dashboard.__init__(data)  # ou une méthode refresh
```

---

## Résumé des fichiers à modifier

- `docker-compose.yml` → ajouter `TZ`, monter `.bash_history`
- `Dockerfile` → ajouter `tzdata`
- `taskmonitor/gui/app.py` → forcer palette sombre
- `taskmonitor/collectors/window_monitor.sh` → XAUTHORITY dynamique
- `taskmonitor/gui/pages/processing.py` → signal `finished_processing`
- `taskmonitor/gui/main_window.py` → connecter `_reload_data`

Après ces changements, rebuild :
```bash
docker rm taskmonitor_app
docker rmi taskmonitor:latest
docker build -t taskmonitor:latest .
```