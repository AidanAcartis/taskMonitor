# Script d’extraction des événements de fenêtres

## Objectif du script

J’ai mis en place un script Bash nommé `extract_window_events.sh` dont le rôle est de :

- exécuter deux commandes d’extraction à partir d’un fichier de log,
- séparer les événements d’ouverture et de fermeture de fenêtres,
- stocker les résultats dans deux fichiers distincts :
  - `Opened_file.txt` pour les fenêtres ouvertes,
  - `Closed_file.txt` pour les fenêtres fermées.

Ce script s’appuie sur l’analyse du fichier `window_changes.log`.

---

## Script : `extract_window_events.sh`

```bash
#!/bin/bash

# Fichier log à analyser
LOG_FILE="$HOME/window_changes.log"

# Fichiers de sortie
OPENED_FILE="$HOME/Opened_file.txt"
CLOSED_FILE="$HOME/Closed_file.txt"

# Extraction des fenêtres ouvertes avec horodatage
paste -d ' ' \
  <(grep -A 0 "Nouvelles fenêtres ajoutées" "$LOG_FILE" | grep -v "^--$" | awk '{print $2}' | grep .) \
  <(grep -A 1 "Nouvelles fenêtres ajoutées" "$LOG_FILE" | grep -v "^--$" | awk -F ' aidan ' '{print $2}' | grep .) \
  > "$OPENED_FILE"

# Extraction des fenêtres fermées avec horodatage
paste -d ' ' \
  <(grep -A 0 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk '{print $2}' | grep .) \
  <(grep -A 1 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk -F ' aidan ' '{print $2}' | grep .) \
  > "$CLOSED_FILE"

echo "Fichiers générés :"
echo "- $OPENED_FILE"
echo "- $CLOSED_FILE"
````

---

## Fonctionnement général

Le script procède en deux étapes principales :

1. **Fenêtres ouvertes**

   * Il repère les lignes contenant `Nouvelles fenêtres ajoutées`.
   * Il extrait l’horodatage ainsi que l’identifiant ou le nom de la fenêtre.
   * Il combine ces informations sur une seule ligne grâce à `paste`.

2. **Fenêtres fermées**

   * Il applique la même logique aux lignes contenant `Fenêtres fermées`.
   * Les résultats sont stockés dans un fichier séparé.

Cette séparation permet de reconstruire plus facilement les durées d’ouverture des fenêtres ou d’analyser les usages par application.

---

## Instructions d’utilisation

1. Sauvegarder le script sous le nom :

   ```bash
   extract_window_events.sh
   ```

2. Rendre le fichier exécutable :

   ```bash
   chmod +x extract_window_events.sh
   ```

3. Lancer le script :

   ```bash
   ./extract_window_events.sh
   ```

Après exécution, les deux fichiers de sortie sont générés dans le répertoire personnel.

---

## Évolutions possibles

Ce script peut ensuite être intégré dans un pipeline plus large, par exemple pour :

* une exécution automatique quotidienne (cron),
* un déclenchement après modification de `window_changes.log`,
* un préprocessing en vue d’un dataset temporel d’activités utilisateur.

```