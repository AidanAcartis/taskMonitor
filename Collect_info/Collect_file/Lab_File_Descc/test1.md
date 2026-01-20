# Analyse d’erreur et diagnostic du pipeline

## 1. Erreur rencontrée

### Message d’erreur

```

IndexError: list index out of range

````

Cette erreur apparaît dans la fonction `parse_line`, à la ligne :

```python
filename = parts[1]
````

---

## 2. Code concerné

### Fonction de parsing

```python
def parse_line(line):
    parts = line.strip().split(" ", 1)
    time = parts[0]
    filename = parts[1]
    return time, filename
```

Cette fonction suppose **implicitement** que chaque ligne contient **au moins deux éléments séparés par un espace**.

---

## 3. Contenu réel des fichiers

### `Opened_file_true.txt`

```
10:18:16 fenêtres ajoutées :
10:18:18 collect_script.sh
10:18:26 fenêtres ajoutées :
10:18:34 extract_window_events.sh
10:19:13 fenêtres ajoutées :
10:19:15 collect_script.sh
```

### `Closed_file_true.txt`

```
10:18:16 fermées :
10:18:18 Preview READme.md
10:18:26 fermées :
10:18:34 collect_script.sh
10:19:13 fermées :
10:19:15 extract_window_events.sh
10:19:35 fermées :
10:20:18 collect_script.sh
```

---

## 4. Cause exacte du problème

Certaines lignes **ne contiennent pas de nom de fichier**, par exemple :

```
10:18:16 fenêtres ajoutées :
10:18:26 fenêtres ajoutées :
10:18:16 fermées :
```

Quand la ligne est traitée :

```python
parts = line.strip().split(" ", 1)
```

On obtient :

```python
parts = ["10:18:16"]
```

Il n’y a **pas de `parts[1]`**, d’où l’erreur :

```
IndexError: list index out of range
```

---

## 5. Pourquoi l’erreur apparaît dans la boucle principale

Dans cette ligne :

```python
close_time, close_filename = parse_line(closed_lines[j])
```

La boucle tombe parfois sur une ligne de type :

```
10:18:16 fermées :
```

qui **ne représente pas un événement de fichier**, mais un simple marqueur.

---

## 6. Correction minimale recommandée

### Version robuste de `parse_line`

```python
def parse_line(line):
    parts = line.strip().split(" ", 1)
    if len(parts) < 2:
        return None, None
    return parts[0], parts[1]
```

### Adaptation dans la boucle

```python
open_time, filename = parse_line(open_line)
if filename is None:
    continue
```

Et pareil pour la fermeture :

```python
close_time, close_filename = parse_line(closed_lines[j])
if close_filename is None:
    continue
```

---

## 7. Problème structurel plus profond

Le vrai problème n’est **pas seulement le parsing**, mais le format intermédiaire :

* Les fichiers mélangent :

  * des **événements réels** (timestamp + fichier),
  * des **lignes de contexte** (“fenêtres ajoutées :”, “fermées :”).

👉 Ces lignes auraient dû être **filtrées dès l’extraction Bash**, ou stockées dans une structure plus explicite (JSON).

---

## 8. Analyse des prédictions du modèle (zéro-shot)

### Exemple critique

#### FILENAME

```
audit_trail
```

#### Description de référence

```
likely containing records of system activities or user actions for auditing purposes.
```

#### Prédiction du modèle

```
Audit_trail is a telecommunications company that is headquartered in the city of san francisco, california.
```

### Diagnostic

Le modèle :

* **hallucine une entité réelle** (entreprise),
* interprète le nom comme un **nom propre**,
* ignore totalement le contexte technique.

Cela indique que :

* le modèle n’a **pas appris** à traiter `filename` comme un objet technique,
* il applique un biais “nom → entité du monde réel”.

---

## 9. Comparaison avec d’autres cas

| Filename         | Qualité                    |
| ---------------- | -------------------------- |
| migration_script | Acceptable                 |
| network_settings | Correct mais vague         |
| optimize_cache   | Faux (compression ≠ cache) |
| audit_trail      | Totalement faux            |

👉 Plus le nom est **ambigu et générique**, plus le modèle hallucine.

---

## 10. Conclusion globale

### Sur l’erreur Python

* C’est un **problème de format de données**, pas de logique algorithmique.
* Le parsing suppose des invariants qui ne sont pas respectés.

### Sur le modèle

* Le zéro-shot **ne suffit pas** pour interpréter correctement des noms techniques courts.
* Sans signal structurel (extension, dossier, application), le modèle invente.

---

## 11. Recommandations

1. Nettoyer les fichiers dès la phase Bash (pas de lignes “méta”).
2. Stocker les événements sous forme structurée (`jsonl`).
3. Fournir au modèle :

   * extension,
   * dossier,
   * application,
   * type (`file` / `command`).
4. Fine-tuner avec des exemples **anti-hallucination** (audit_trail ≠ entreprise).

---

