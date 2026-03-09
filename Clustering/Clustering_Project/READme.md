# Semantic Task Clustering – Training & Inference Pipeline

Ce projet implémente une **chaîne complète de préparation, entraînement et inférence** pour le clustering sémantique de tâches utilisateur, basée sur des embeddings Sentence Transformers et un raffinement hiérarchique contrôlé par des métriques de cohésion.

L’objectif est d’obtenir des **clusters interprétables**, représentant des **tâches globales cohérentes**, éventuellement composées de sous-tâches, tout en acceptant l’existence de tâches autonomes (singletons).

---

## 📌 Objectifs du projet

* Apprendre des représentations sémantiques de tâches orientées *objectif global*
* Structurer les données sous forme hiérarchique (sous-tâches → tâche globale)
* Entraîner un modèle sans négatifs explicites (contrastif implicite)
* Produire, à l’inférence, des clusters :

  * cohérents,
  * interprétables,
  * stables,
  * adaptés à une intégration logicielle

---

## 🧱 Structure globale du pipeline

1. **Feature engineering & structuration des données**
2. **Construction des exemples d’entraînement**
3. **Entraînement du modèle d’embeddings**
4. **Inférence multi-étapes avec reclustering adaptatif**

---

## 1️⃣ Feature Engineering & Structuration des données

### Normalisation des tâches

Un nettoyage minimal est appliqué afin de réduire le bruit textuel tout en conservant l’information sémantique.

```python
def normalize_task(text):
    """
    Nettoyage minimal d'un task_item ou global_task
    """
    text = text.replace('\\"', '').replace('"', '')
    text = text.lower().strip()
    return text
```

---

### Structuration hiérarchique des données

Chaque entrée du dataset est transformée en une structure à deux niveaux :

* **Niveau A** : sous-tâches unitaires (`small_tasks`)
* **Niveau B** : tâche globale (`global_block`) obtenue par concaténation

```python
structured_dataset = []

for entry in dataset:
    task_items = entry["task_items"]

    small_tasks = [normalize_task(t) for t in task_items]
    global_block = " ".join(small_tasks)

    structured_dataset.append({
        "id": entry["id"],
        "small_tasks": small_tasks,
        "global_block": global_block,
        "global_task_description": normalize_task(entry["global_task_description"])
    })
```

👉 Cette structuration permet d’apprendre explicitement la relation *sous-tâche → tâche globale*.

---

## 2️⃣ Construction des exemples d’entraînement

Les exemples sont construits sous forme de **paires positives uniquement**, compatibles avec `MultipleNegativesRankingLoss`.

Trois types de relations sont utilisés :

* sous-tâche ↔ tâche globale
* sous-tâche ↔ sous-tâche (cohésion intra-cluster)
* sous-ensemble partiel de sous-tâches ↔ tâche globale (data augmentation)

Les exemples sont ensuite sauvegardés pour réutilisation.

```python
with open(save_path, "wb") as f:
    pickle.dump(train_examples, f)
```

---

## 3️⃣ Entraînement du modèle d’embeddings

### Modèle de base

```python
model_name = "all-MiniLM-L6-v2"
model = SentenceTransformer(model_name)
```

### Dataloader & loss

```python
train_dataloader = DataLoader(
    train_examples,
    shuffle=True,
    batch_size=8
)

train_loss = losses.MultipleNegativesRankingLoss(model)
```

### Entraînement

```python
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=3,
    warmup_steps=warmup_steps,
    show_progress_bar=True,
    checkpoint_path=CHECKPOINT_DIR,
    checkpoint_save_steps=2000,
    checkpoint_save_total_limit=3
)
```

* Pas de négatifs explicites
* Négatifs implicites fournis par le batch
* Checkpoints automatiques
* Modèle final sauvegardé pour l’inférence

---

## 4️⃣ Inférence & Clustering sémantique (vue d’ensemble)

L’inférence repose sur un **pipeline en 4 étapes**, conçu pour maximiser la cohérence et l’interprétabilité des clusters.

### Step 1 — Clustering global initial

* Encodage des tâches
* Matrice de distances cosinus
* Clustering hiérarchique agglomératif
* Sélection du meilleur seuil via silhouette

### Step 2 — Reclustering itératif par cohésion

* Calcul de la cohésion intra-cluster
* Reclustering local des clusters trop hétérogènes
* Gestion explicite des petits clusters

### Step 3 — Traitement des singletons

* Extraction des tâches isolées
* Reclustering optionnel si leur proportion est significative
* Fusion contrôlée avec les clusters existants

### Step 4 — Reclustering adaptatif final

* Analyse fine des clusters encore hétérogènes
* Division récursive jusqu’à atteindre une cohésion acceptable
* Validation finale par silhouette et cohésion moyenne

👉 Le résultat final est un ensemble de clusters :

* centrés sur des tâches globales,
* acceptant les singletons pertinents,
* directement exploitables dans un logiciel.

---

## 📊 Métriques utilisées

* **Distance cosinus** (embeddings normalisés)
* **Silhouette score** (qualité globale)
* **Cohésion intra-cluster moyenne** (qualité locale)

Les singletons sont volontairement exclus des métriques de cohésion.

---

## 🧠 Philosophie de conception

* Pas de nombre de clusters imposé
* Pas de négatifs explicites
* Priorité à l’interprétabilité sémantique
* Clusters = tâches globales, pas simples similarités lexicales
* Singletons autorisés s’ils représentent une tâche autonome

---

## 🚀 Intégration logicielle

Ce pipeline est conçu pour être :

* embarqué dans un logiciel d’analyse d’activités utilisateur,
* utilisé en batch ou en quasi temps réel,
* étendu avec de nouveaux seuils ou heuristiques métier.

---

## 📁 Artefacts produits

* `train_examples.pkl` : exemples d’entraînement
* `checkpoints/` : modèles intermédiaires
* `final_model/` : modèle final prêt pour l’inférence

---

## ✅ Statut

✔ Feature engineering
✔ Entraînement
✔ Inférence multi-étapes
✔ Prêt pour intégration logicielle

