# 🖥️ Linux Window Activity Tracker

A Bash and Python-based pipeline to monitor opened/closed application windows in Linux and extract usage timelines.

---

## 📚 Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Installation](#installation)
* [Usage](#usage)
* [Code Breakdown](#code-breakdown)

  * [1. Continuous Window Monitoring (Bash)](#1-continuous-window-monitoring-bash)
  * [2. Extract Opened/Closed Events from Logs (Bash)](#2-extract-openedclosed-events-from-logs-bash)
  * [3. Format File Names (Python)](#3-format-file-names-python)
  * [4. Match Opened/Closed Events (Python)](#4-match-openedclosed-events-python)
* [Output Example](#output-example)
* [Conclusion](#conclusion)
* [📎 Annexe: Détails Techniques](#annexe--détails-techniques)

---

## 📖 Overview

This project provides a lightweight, modular system for monitoring window activities on Linux. It detects and logs the opening and closing of graphical application windows in real-time, then processes this data to output a timeline of usage.

---

## ✨ Features

* Real-time window activity tracking
* Timestamped logging of opened and closed windows
* Data cleanup and formatting
* Pairing of open/close events for the same file/window
* Final output: a structured text file with precise usage history

---

## ⚙️ Installation

1. Ensure the following dependencies are installed:

```bash
sudo apt update && sudo apt install wmctrl python3
```

2. Clone this repository:

```bash
git clone https://github.com/votre-utilisateur/linux-window-tracker.git
cd linux-window-tracker
```

3. Make the Bash scripts executable:

```bash
chmod +x *.sh
```

---

## ▶️ Usage

1. Run the monitoring script:

```bash
./corrected_monitor_windows.sh
```

2. After collecting data in `window_changes.log`, extract opened/closed entries:

```bash
./extract_window_events.sh
```

3. Format extracted files:

```bash
python3 correct_opened-closed_file.py
```

4. Match open and close events:

```bash
python3 get_collect_file.py
```

The final output will be in `collected_file.txt`.

---

## 🧩 Code Breakdown

### 1. Continuous Window Monitoring (Bash)

**File:** `corrected_monitor_windows.sh`

```bash
#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=/home/aidan/.Xauthority

LOG_FILE="$HOME/window_changes.log"
PREV_WINDOWS_FILE="$HOME/prev_windows.txt"

if [ ! -f "$PREV_WINDOWS_FILE" ]; then
    wmctrl -l > "$PREV_WINDOWS_FILE"
fi

echo "Surveillance des fenêtres en cours..."

while true; do
    CURRENT_DATE=$(date +"%Y-%m-%d")

    if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
        LAST_LOG_DATE=$(grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}" "$LOG_FILE" | tail -n 1 | awk '{print $1}')
    else
        LAST_LOG_DATE=""
    fi

    if [ "$CURRENT_DATE" != "$LAST_LOG_DATE" ]; then
        echo "-----------------------------" > "$LOG_FILE"
        echo "$(date +"%Y-%m-%d %H:%M:%S") - Nouveau jour de surveillance" >> "$LOG_FILE"
    fi

    CURRENT_WINDOWS=$(wmctrl -l)

    NEW_WINDOWS=$(comm -13 <(sort "$PREV_WINDOWS_FILE") <(echo "$CURRENT_WINDOWS" | sort))
    CLOSED_WINDOWS=$(comm -23 <(sort "$PREV_WINDOWS_FILE") <(echo "$CURRENT_WINDOWS" | sort))

    if [ -n "$NEW_WINDOWS" ]; then
        echo "$(date +"%Y-%m-%d %H:%M:%S") - Nouvelles fenêtres ajoutées :" >> "$LOG_FILE"
        echo "$NEW_WINDOWS" >> "$LOG_FILE"
        echo "-----------------------------" >> "$LOG_FILE"
    fi

    if [ -n "$CLOSED_WINDOWS" ]; then
        echo "$(date +"%Y-%m-%d %H:%M:%S") - Fenêtres fermées :" >> "$LOG_FILE"
        echo "$CLOSED_WINDOWS" >> "$LOG_FILE"
        echo "-----------------------------" >> "$LOG_FILE"
    fi

    echo "$CURRENT_WINDOWS" > "$PREV_WINDOWS_FILE"
    sleep 2
done
```

### Function:

* Tracks the open/closed windows using `wmctrl`.
* Logs new and closed windows every 2 seconds.
* Output: `window_changes.log`

---

### 2. Extract Opened/Closed Events from Logs (Bash)

**File:** `extract_window_events.sh`

```bash
#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$HOME/window_changes.log"
OPENED_FILE="$SCRIPT_DIR/Opened_file.txt"
CLOSED_FILE="$SCRIPT_DIR/Closed_file.txt"

> "$OPENED_FILE"
> "$CLOSED_FILE"

paste -d ' ' \
  <(grep -A 0 "Nouvelles fenêtres ajoutées" "$LOG_FILE" | grep -v "^--$" | awk '{print $2}' | grep .) \
  <(grep -A 1 "Nouvelles fenêtres ajoutées" "$LOG_FILE" | grep -v "^--$" | awk -F ' aidan ' '{print $2}' | grep .) \
  > "$OPENED_FILE"

paste -d ' ' \
  <(grep -A 0 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk '{print $2}' | grep .) \
  <(grep -A 1 "Fenêtres fermées" "$LOG_FILE" | grep -v "^--$" | awk -F ' aidan ' '{print $2}' | grep .) \
  > "$CLOSED_FILE"

echo "Fichiers générés :"
echo "- $OPENED_FILE"
echo "- $CLOSED_FILE"
```

### Function:

* Parses log file.
* Extracts window titles with timestamps.
* Outputs: `Opened_file.txt`, `Closed_file.txt`

---

### 3. Format File Names (Python)

**File:** `correct_opened-closed_file.py`

```python
def treat_lines(infile, outfile):
    try:
        with open(infile, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        modified_lines = []

        for line in lines:
            line = line.strip()
            dot_index = line.rfind('.')

            if dot_index != -1:
                part1 = line[:dot_index]
                part2 = line[dot_index + 1:].split()[0]
                result = f'{part1}.{part2}'
            else:
                result = line

            modified_lines.append(result)

        with open(outfile, 'w', encoding='utf-8') as file:
            file.writelines(line + '\n' for line in modified_lines)

        print(f"[✓] Le fichier '{outfile}' a été généré avec succès.")

    except FileNotFoundError:
        print(f"[!] Fichier introuvable : {infile}")
    except Exception as e:
        print(f"[!] Erreur lors du traitement de {infile} : {e}")

treat_lines('Opened_file.txt', 'Opened_file_true.txt')
treat_lines('Closed_file.txt', 'Closed_file_true.txt')
```

### Function:

* Cleans file names.
* Keeps file extensions intact.
* Outputs: `Opened_file_true.txt`, `Closed_file_true.txt`

---

### 4. Match Opened/Closed Events (Python)

**File:** `get_collect_file.py`

```python
def parse_line(line):
    parts = line.strip().split(" ", 1)
    time = parts[0]
    filename = parts[1]
    return time, filename

with open("Opened_file_true.txt", "r", encoding="utf-8") as f_open:
    opened_lines = f_open.readlines()

with open("Closed_file_true.txt", "r", encoding="utf-8") as f_close:
    closed_lines = f_close.readlines()

true_file_lines = []
used_close_indices = set()

for i, open_line in enumerate(opened_lines):
    open_time, filename = parse_line(open_line)

    for j in range(i, len(closed_lines)):
        if j in used_close_indices:
            continue
        close_time, close_filename = parse_line(closed_lines[j])
        if close_filename == filename:
            used_close_indices.add(j)
            true_file_lines.append(f"{open_time} {close_time} {filename}\n")
            break

with open("collected_file.txt", "w", encoding="utf-8") as f_true:
    f_true.writelines(true_file_lines)

print("Fichier 'collected_file.txt' généré avec succès.")
```

### Function:

* Matches open and close events for each file.
* Generates final timeline: `collected_file.txt`

---

## 📝 Output Example

```text
12:34:56 12:45:12 Document1.txt
13:00:01 13:15:45 Notes.md
```

---

## ✅ Conclusion

This modular Bash + Python pipeline allows real-time and historical analysis of window activities on Linux systems. It is ideal for:

* Usage auditing
* Productivity tracking
* Monitoring system access

You can enhance it with GUI, notification support, or automated backups.

---

## 📎 Annexe : Détails Techniques

| Script/File                     | Purpose                                            |
| ------------------------------- | -------------------------------------------------- |
| `corrected_monitor_windows.sh`  | Monitor and log window activity continuously       |
| `extract_window_events.sh`      | Extract window open/close events from log          |
| `correct_opened-closed_file.py` | Clean and reformat extracted window names          |
| `get_collect_file.py`           | Combine open/close times into a final summary file |
| `Opened_file_true.txt`          | Cleaned list of opened windows                     |
| `Closed_file_true.txt`          | Cleaned list of closed windows                     |
| `collected_file.txt`            | Final result with timestamps and file/window names |
