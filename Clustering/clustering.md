---
## Étape 0 : Monter Google Drive

Je commence par monter Google Drive afin d’accéder directement à mon dataset stocké dans Drive et d’y sauvegarder les résultats.

```python
from google.colab import drive
drive.mount('/content/drive')
````

Je définis ensuite les chemins vers le fichier d’entrée au format JSONL et vers le fichier de sortie qui contiendra les clusters générés.

```python
input_path = '/content/drive/MyDrive/data.jsonl'  # à adapter
output_path = '/content/drive/MyDrive/clusters_descriptions.jsonl'
```

---

## Étape 1 : Installation des bibliothèques nécessaires

J’installe toutes les bibliothèques requises directement dans le notebook afin d’assurer la reproductibilité de l’expérience.

```python
!pip install -q sentence-transformers==2.2.2
!pip install -q hdbscan==0.8.32
!pip install -q scikit-learn==1.3.2
!pip install -q pandas==2.2.2
!pip install -q torch>=2.1.0
```

---

## Étape 2 : Chargement du dataset JSONL

Je charge le dataset JSONL contenant les descriptions d’activités et je le convertis en DataFrame pour faciliter la manipulation des données.

```python
import json
import pandas as pd

data = []
with open(input_path, "r", encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))

df = pd.DataFrame(data)
print("Aperçu du dataset :")
print(df.head())
```

---

## Étape 3 : Préparation des descriptions textuelles

J’extrais la colonne contenant les descriptions. Selon le besoin, je peux enrichir le texte en concaténant d’autres champs (type, nom de fichier, répertoire) afin de fournir plus de contexte au modèle.

```python
descriptions = df['description'].tolist()

# Optionnel : ajouter plus de contexte
# descriptions = (df['type'] + ' ' + df['name'] + ' ' + df['description']).tolist()
```

---

## Étape 4 : Génération des embeddings

J’utilise un modèle Sentence Transformer pour convertir les descriptions textuelles en embeddings vectoriels exploitables pour le clustering.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(descriptions, show_progress_bar=True)
```

---

## Étape 5 : Normalisation des embeddings

Je normalise les embeddings afin d’améliorer la qualité du clustering, en particulier lorsque des distances cosinus ou euclidiennes sont utilisées.

```python
from sklearn.preprocessing import normalize

embeddings_norm = normalize(embeddings)
```

---

## Étape 6 : Clustering avec HDBSCAN

J’applique l’algorithme HDBSCAN pour identifier automatiquement des groupes cohérents de descriptions sans fixer le nombre de clusters à l’avance.

```python
import hdbscan
from collections import Counter

clusterer = hdbscan.HDBSCAN(
    min_cluster_size=3,
    metric='euclidean',
    cluster_selection_method='eom'
)

labels = clusterer.fit_predict(embeddings_norm)
df['cluster'] = labels

print("Répartition des clusters :")
print(Counter(labels))
```

---

## Étape 7 : Regroupement et export des clusters

Je regroupe les descriptions appartenant à chaque cluster (en excluant le bruit) et je génère un fichier JSONL de sortie contenant les clusters et leurs descriptions associées.

```python
clusters = df[df['cluster'] != -1].groupby('cluster')['description'].apply(list)

with open(output_path, 'w', encoding='utf-8') as f_out:
    for c, descs in clusters.items():
        json.dump({
            "cluster": int(c),
            "descriptions": descs
        }, f_out, ensure_ascii=False)
        f_out.write("\n")

print(f"Fichier JSONL de clusters généré : {output_path}")
```

---

## Résumé

Ce notebook permet de :

* Charger un dataset JSONL depuis Google Drive.
* Générer des embeddings sémantiques à partir de descriptions textuelles.
* Appliquer un clustering non supervisé avec HDBSCAN.
* Produire un fichier JSONL contenant des groupes cohérents de descriptions.

Ce pipeline constitue une base solide pour des tâches de structuration automatique d’activités, de construction de datasets ou d’entraînement de modèles génératifs comme Flan-T5.

