Parfait 👍 je vois exactement ce que tu veux : on doit **mettre à jour ton schéma d’input/output et ton preprocessing** pour inclure non seulement le filename, mais aussi **l’extension, le répertoire et l’application**, et modifier la consigne afin que la sortie soit une description complète (et pas seulement la fonction du fichier).

Voici la version corrigée et adaptée à ton nouvel objectif 👇

---

### 1️⃣ Dataset JSONL

Chaque exemple doit contenir toutes les infos nécessaires :

```jsonl
{"id": "0", "filename": "extract_window_events.sh", "extension": "sh", "directory": "Collect_file", "application": "Visual Studio Code", "description": "Script qui extrait les événements de la fenêtre de la machine. Il se trouve dans le dossier Collect_file et ouvert avec Visual Studio Code."}
{"id": "1", "filename": "analyse_logs.py", "extension": "py", "directory": "Analyse", "application": "PyCharm", "description": "Script Python qui analyse les journaux système. Il est situé dans le dossier Analyse et ouvert avec PyCharm."}
{"id": "2", "filename": "backup_database.sql", "extension": "sql", "directory": "DB_Backup", "application": "DBeaver", "description": "Fichier SQL qui sauvegarde la base de données. Il se trouve dans le dossier DB_Backup et ouvert avec DBeaver."}
{"id": "3", "filename": "rapport.html", "extension": "html", "directory": "Reports", "application": "Google Chrome", "description": "Page HTML qui affiche un rapport. Elle se trouve dans le dossier Reports et ouverte avec Google Chrome."}
```

---

### 2️⃣ Prompt d’entraînement

On corrige la consigne pour refléter ton objectif :

**Nouveau prompt (plus explicite) :**

```
Décrire le fichier suivant. Inclure :
- ce qu'il est selon l'extension ({extension})
- ce qu'il fait selon son nom ({filename})
- où il est situé ({directory})
- quelle application l'ouvre ({application})

Fichier : {filename}
Extension : {extension}
Répertoire : {directory}
Application : {application}
Description :
```

👉 Exemple :

```
Décrire le fichier suivant. Inclure :
- ce qu'il est selon l'extension (sh)
- ce qu'il fait selon son nom (extract_window_events.sh)
- où il est situé (Collect_file)
- quelle application l'ouvre (Visual Studio Code)

Fichier : extract_window_events.sh
Extension : sh
Répertoire : Collect_file
Application : Visual Studio Code
Description :
```

**Output attendu :**

```
Script qui extrait les événements de la fenêtre de la machine. Il se trouve dans le dossier Collect_file et ouvert avec Visual Studio Code.
```

---

### 3️⃣ Preprocessing corrigé (HuggingFace)

```python
def tokenize_function(example):
    start_prompt = (
        "Décrire le fichier suivant. Inclure :\n"
        "- ce qu'il est selon l'extension ({extension})\n"
        "- ce qu'il fait selon son nom ({filename})\n"
        "- où il est situé ({directory})\n"
        "- quelle application l'ouvre ({application})\n\n"
        "Fichier : {filename}\n"
        "Extension : {extension}\n"
        "Répertoire : {directory}\n"
        "Application : {application}\n"
        "Description : "
    )
    
    # Construire l'input prompt dynamique
    prompt = [
        start_prompt.format(
            filename=ex["filename"],
            extension=ex["extension"],
            directory=ex["directory"],
            application=ex["application"]
        )
        for ex in example
    ]
    
    # Tokenizer input + output
    example['input_ids'] = tokenizer(prompt, padding="max_length", truncation=True, return_tensors="pt").input_ids
    example['labels'] = tokenizer(example["description"], padding="max_length", truncation=True, return_tensors="pt").input_ids
    
    return example
```

---

### 4️⃣ Résultat final attendu

Ton dataset après preprocessing :

```python
DatasetDict({
    train: Dataset({
        features: ['input_ids', 'labels'],
        num_rows: XXXX
    })
    validation: Dataset({
        features: ['input_ids', 'labels'],
        num_rows: XXXX
    })
    test: Dataset({
        features: ['input_ids', 'labels'],
        num_rows: XXXX
    })
})
```

---

✅ Résumé :

* **Dataset enrichi** : `filename + extension + directory + application + description`.
* **Prompt explicite** : guide le modèle à produire une description complète et claire.
* **Labels** : la phrase descriptive attendue.
* **Preprocessing** : adapte l’input prompt pour chaque exemple.

---

Veux-tu que je te propose **2 variantes de prompt** (une très courte, une détaillée comme ci-dessus) pour que tu puisses tester lequel donne les meilleures descriptions lors du fine-tuning ?
