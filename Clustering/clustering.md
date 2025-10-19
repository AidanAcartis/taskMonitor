Parfait ! Voici ton notebook **Google Colab complet**, avec les installations nécessaires intégrées **en début de cellule**, prêt à être copié/collé et exécuté.

```python
# Étape 0 : Monter Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Définir le chemin vers ton dataset JSONL
input_path = '/content/drive/MyDrive/data.jsonl'  # à adapter
output_path = '/content/drive/MyDrive/clusters_descriptions.jsonl'

# Étape 1 : Installer les bibliothèques nécessaires
!pip install -q sentence-transformers==2.2.2
!pip install -q hdbscan==0.8.32
!pip install -q scikit-learn==1.3.2
!pip install -q pandas==2.2.2
!pip install -q torch>=2.1.0

# Étape 2 : Charger le dataset JSONL
import json
import pandas as pd

data = []
with open(input_path, "r", encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))

df = pd.DataFrame(data)
print("Aperçu du dataset :")
print(df.head())

# Étape 3 : Préparer les descriptions
descriptions = df['description'].tolist()

# Optionnel : concaténer type, name ou directory pour plus de contexte
# descriptions = (df['type'] + ' ' + df['name'] + ' ' + df['description']).tolist()

# Étape 4 : Générer les embeddings avec Sentence Transformer
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # rapide et efficace
embeddings = model.encode(descriptions, show_progress_bar=True)

# Étape 5 : Normalisation (recommandée)
from sklearn.preprocessing import normalize

embeddings_norm = normalize(embeddings)

# Étape 6 : Clustering avec HDBSCAN
import hdbscan
from collections import Counter

clusterer = hdbscan.HDBSCAN(
    min_cluster_size=3,  # à ajuster selon ton dataset
    metric='euclidean',  # ou 'cosine' si tu préfères
    cluster_selection_method='eom'
)

labels = clusterer.fit_predict(embeddings_norm)
df['cluster'] = labels
print("Répartition des clusters :")
print(Counter(labels))

# Étape 7 : Regrouper les descriptions par cluster
clusters = df[df['cluster'] != -1].groupby('cluster')['description'].apply(list)

# Préparer le fichier JSONL de sortie
with open(output_path, 'w', encoding='utf-8') as f_out:
    for c, descs in clusters.items():
        json.dump({
            "cluster": int(c),
            "descriptions": descs
        }, f_out, ensure_ascii=False)
        f_out.write("\n")

print(f"Fichier JSONL de clusters généré : {output_path}")
```

✅ Ce notebook fait maintenant tout :

1. Monte Google Drive.
2. Installe toutes les bibliothèques (`sentence-transformers`, `hdbscan`, `scikit-learn`, `pandas`, `torch`).
3. Charge ton JSONL depuis Drive.
4. Crée les embeddings et normalise.
5. Fait le clustering HDBSCAN.
6. Génère un fichier **JSONL** de sortie avec chaque cluster et ses descriptions.

Si tu veux, je peux te fournir **une version qui ajoute automatiquement un résumé par cluster** pour que ton JSONL contienne `"cluster"`, `"descriptions"` et `"summary"` directement.

Veux‑tu que je fasse ça ?
