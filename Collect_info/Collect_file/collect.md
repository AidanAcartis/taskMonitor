Voici un script `extract_window_events.sh` qui :

- exécute les deux commandes que tu as données,
- stocke le résultat de :
  - la **commande 1 (ouvertures)** dans `Opened_file.txt`
  - la **commande 2 (fermetures)** dans `Closed_file.txt`

---

### ✅ Fichier : `extract_window_events.sh`

```bash
#!/bin/bash

# Fichier log à analyser
LOG_FILE="$HOME/window_changes.log"

# Fichier de sortie
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
```

---

### 🔧 Instructions :

1. Sauvegarder le fichier sous le nom `extract_window_events.sh`
2. Rendre le fichier exécutable :
   ```bash
   chmod +x extract_window_events.sh
   ```
3. Exécuter :
   ```bash
   ./extract_window_events.sh
   ```

---

Souhaites-tu que ce script s’exécute automatiquement chaque jour ou après chaque modification du fichier `window_changes.log` ?