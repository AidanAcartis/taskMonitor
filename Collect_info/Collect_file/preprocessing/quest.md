# Vérification du rôle sémantique de `lexical_embeds`

## Contexte initial du dataset

Au départ, mon dataset est stocké sous forme JSONL et chargé avec `datasets` de Hugging Face :

```python
my_dataset = "/content/drive/MyDrive/file_desc_data/file_description.jsonl"

dataset = load_dataset(
    "json",
    data_files=my_dataset,
    split={
        "train": "train[:85%]",
        "validation": "train[85%:95%]",
        "test": "train[95%:]"
    }
)
````

Après chargement, j’obtiens la structure suivante :

* **Train** : 1707 exemples
* **Validation** : 201 exemples
* **Test** : 100 exemples

Chaque entrée contient initialement :

* `id`
* `filename`
* `file_desc`

---

## Préprocessing et intégration de `lexical_embeds`

L’objectif du préprocessing est d’enrichir chaque exemple avec un **embedding externe du nom de fichier**, supposé capturer une information sémantique globale.

### Projection dans l’espace de Flan-T5

Comme les embeddings produits par mon modèle lexical (dimension 384) ne sont pas dans le même espace que Flan-T5 (dimension 512), j’utilise une couche linéaire de projection :

```python
hidden_size = config.d_model  # dimension interne de flan-t5-small
proj_layer = nn.Linear(embedding_dim, hidden_size)
proj_layer = proj_layer.eval()
```

Cette couche permet d’aligner l’espace sémantique externe avec l’espace interne du modèle génératif.

---

### Fonction de tokenisation

Pour chaque exemple :

1. Je récupère le `filename` et la description cible `file_desc`.
2. Je calcule un embedding sémantique global du nom de fichier.
3. Je projette cet embedding dans l’espace de Flan-T5.
4. Je construis un prompt textuel standard.
5. Je stocke l’embedding projeté comme `lexical_embeds`.

```python
def tokenize_function(example):
    filename = example["filename"]
    file_desc = example["file_desc"]

    # Embedding externe du filename
    filename_embedding = torch.tensor(lex_model.encode(filename))  # (384,)
    filename_proj = proj_layer(filename_embedding.float())  # (512,)

    # Prompt
    prompt = f"""
    Given the following filename, generate a short description of what the file is likely about.

    Filename: {filename}

    Description:
    """

    # Tokenisation
    tokenized_inputs = tokenizer(prompt, padding="max_length", truncation=True)
    tokenized_labels = tokenizer(file_desc, padding="max_length", truncation=True)

    tokenized_inputs["labels"] = tokenized_labels["input_ids"]
    tokenized_inputs["lexical_embeds"] = filename_proj.detach().numpy()

    return tokenized_inputs
```

Après application de cette fonction et suppression des colonnes inutiles, le dataset devient :

* `input_ids`
* `attention_mask`
* `labels`
* `lexical_embeds`

Chaque split conserve le même nombre d’exemples qu’au départ.

---

## Problématique scientifique

La question centrale que je cherche à traiter est la suivante :

> **Est-ce que `lexical_embeds` représente réellement un vecteur de sémantique globale du nom de fichier, capturant le sens combiné de la séquence entière, ou s’agit-il simplement d’un signal faible ou redondant ?**

Autrement dit, je veux déterminer si :

* `lexical_embeds` apporte une information **complémentaire** aux tokens textuels,
* ou si le modèle pourrait atteindre les mêmes performances sans cette composante.

---

## Hypothèse de travail

Mon hypothèse est que :

* Le nom de fichier contient une **sémantique compacte et globale** (ex. type de document, domaine, usage),
* Cette information est difficile à reconstruire uniquement à partir d’un prompt textuel standard,
* En l’injectant sous forme de vecteur dense unique, le modèle peut exploiter cette information dès les premières couches d’attention.

Dans cette configuration, `lexical_embeds` agit comme un **résumé sémantique global**, analogue à un token spécial porteur de contexte.

---

## Comment démontrer empiriquement son utilité

Pour prouver que `lexical_embeds` capture effectivement une sémantique globale pertinente, je peux procéder de plusieurs manières :

### 1. Étude d’ablation

* Entraîner un modèle **avec** `lexical_embeds`.
* Entraîner un modèle **sans** `lexical_embeds`.
* Comparer :

  * la loss,
  * la qualité des descriptions générées,
  * la vitesse de convergence.

Une amélioration systématique indique que l’embedding apporte une information utile.

---

### 2. Perturbation contrôlée

* Remplacer `lexical_embeds` par :

  * du bruit,
  * un vecteur constant,
  * un embedding d’un autre filename.
* Observer la dégradation des performances.

Si les performances chutent, cela indique que le modèle utilisait activement l’information sémantique contenue dans `lexical_embeds`.

---

### 3. Analyse géométrique de l’espace des embeddings

* Projeter les `lexical_embeds` (PCA / t-SNE / UMAP).
* Vérifier si des noms de fichiers sémantiquement proches se regroupent.

Un regroupement cohérent renforce l’hypothèse d’une représentation globale du sens.

---

### 4. Analyse de l’attention

* Examiner les poids d’attention associés au token issu de `lexical_embeds`.
* Vérifier s’il est utilisé de manière non triviale par le modèle, notamment dans les premières couches.

---

## Conclusion intermédiaire

Dans cette architecture, `lexical_embeds` n’est pas un simple ajout technique.
Il constitue une **hypothèse de représentation sémantique globale**, injectée explicitement dans le modèle pour guider la génération.

La validation de cette hypothèse repose sur :

* des comparaisons expérimentales rigoureuses,
* des analyses d’ablation,
* et une étude du comportement interne du modèle.

C’est précisément ce que je cherche à démontrer à travers ce pipeline.

