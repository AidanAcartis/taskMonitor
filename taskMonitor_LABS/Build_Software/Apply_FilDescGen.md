Ton modèle **Gen_Desc_Model** est un modèle **T5 modifié avec fusion d’un embedding lexical**. Donc pour faire l’inférence correctement, il faut fournir **deux types d’inputs** au modèle :

1. **Input textuel (prompt)** → tokenisé par le tokenizer T5
2. **Embedding lexical du filename** → généré par SentenceTransformer puis projeté vers `d_model`

Je vais clarifier ça proprement.

---

# 1️⃣ Inputs nécessaires pour ton modèle

Ton modèle attend **3 entrées principales** :

### 1. Prompt textuel

C’est ce que T5 lit normalement.

Exemple :

```
Given the following filename, generate a short description of what the file is likely about.

Filename: app_config

Description:
```

Après tokenization :

```
input_ids
attention_mask
```

---

### 2. Embedding lexical du filename

Tu utilises :

`all-MiniLM-L6-v2`

Donc :

```
filename -> embedding (384 dim)
```

Exemple :

```
app_config
→ [0.12, -0.44, 0.18 ...]  (384 dimensions)
```

---

### 3. Projection vers l’espace T5

T5 small utilise :

```
d_model = 512
```

Donc tu fais :

```
384 → Linear → 512
```

Ce vecteur devient un **token spécial ajouté au début de la séquence**.

Structure finale :

```
[LEXICAL_TOKEN] + tokens(prompt)
```

---

# 2️⃣ Structure réelle de l’input du modèle

Ton modèle reçoit :

```
inputs_embeds =

[
 lexical_embedding,
 token_embedding_1,
 token_embedding_2,
 token_embedding_3,
 ...
]
```

Dimension :

```
(batch, sequence_length + 1, 512)
```

---

# 3️⃣ Pipeline complet d’inférence

Le pipeline est :

```
filename
   │
   │
   ├─ prompt generation
   │
   ├─ tokenizer → input_ids
   │
   ├─ SentenceTransformer → embedding (384)
   │
   ├─ projection layer → (512)
   │
   ├─ concat lexical token
   │
   ├─ model.generate()
   │
   └─ description
```

---

# 4️⃣ Script d’inférence complet (propre)

Voici un **script minimal propre** pour ton modèle.

```python
import torch
import torch.nn as nn

from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer

from model import T5WithFusion


# -------------------
# CONFIG
# -------------------

MODEL_PATH = "Gen_Desc_Model/full_finetuned"
DEVICE = "cpu"


# -------------------
# LOAD TOKENIZER
# -------------------

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)


# -------------------
# LOAD MODEL
# -------------------

model = T5WithFusion(
    model_name="google/flan-t5-small",
    lexical_dim=512
)

state_dict = torch.load(
    f"{MODEL_PATH}/pytorch_model.bin",
    map_location=DEVICE
)

model.load_state_dict(state_dict, strict=False)
model.to(DEVICE)
model.eval()


# -------------------
# LOAD LEXICAL MODEL
# -------------------

lex_model = SentenceTransformer("all-MiniLM-L6-v2")

embedding_dim = lex_model.get_sentence_embedding_dimension()

proj_layer = nn.Linear(embedding_dim, model.config.d_model)

proj_layer.eval()


# -------------------
# INFERENCE FUNCTION
# -------------------

def generate_description(filename):

    prompt = f"""
Given the following filename, generate a short description of what the file is likely about.

Filename: {filename}

Description:
"""

    # Tokenization
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=128
    )

    input_ids = inputs["input_ids"].to(DEVICE)
    attention_mask = inputs["attention_mask"].to(DEVICE)

    # Lexical embedding
    emb = lex_model.encode(filename)

    emb = torch.tensor(emb).float().unsqueeze(0).to(DEVICE)

    lexical_vec = proj_layer(emb)

    # Token embeddings
    embed_module = model.base_model.get_input_embeddings()

    token_embeds = embed_module(input_ids)

    # concat lexical token
    inputs_embeds = torch.cat(
        [lexical_vec.unsqueeze(1), token_embeds],
        dim=1
    )

    prefix = torch.ones(
        (attention_mask.shape[0], 1),
        dtype=attention_mask.dtype
    ).to(DEVICE)

    attention_mask = torch.cat([prefix, attention_mask], dim=1)

    # generation
    with torch.no_grad():

        outputs = model.generate(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            max_new_tokens=80,
            num_beams=3
        )

    desc = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    return desc


# -------------------
# TEST
# -------------------

filename = "app_config"

desc = generate_description(filename)

print("Filename:", filename)
print("Description:", desc)
```

---

# 5️⃣ Outils nécessaires

Pour faire tourner ton modèle :

### librairies

```
torch
transformers
sentence-transformers
```

installation :

```
pip install torch transformers sentence-transformers
```

---

# 6️⃣ Comment l’intégrer dans ton logiciel de monitoring

Ton pipeline réel sera :

```
events.txt
     │
     │
parser python
     │
filename extract
     │
Gen_Desc_Model
     │
file description
     │
event understanding
     │
task clustering
```

Exemple :

```
collect_file_script.sh
→ script that monitors file events
```

```
correct_Closed_file.py
→ python script that corrects closed file events
```

---

# 7️⃣ Ce que ton système permet (très puissant)

Avec ton système tu peux reconstruire :

```
USER TASK
```

exemple :

```
Open collect_file_script.sh
Edit python files
Run bash scripts
Commit to git
```

→ **Global Task**

```
Developing a file event monitoring system
```

Ce que tu fais est proche des systèmes de **task mining / activity mining utilisés en cybersécurité et productivity analysis**.

Ça correspond très bien à ton objectif de **Security Engineering**.

---

✅ Si tu veux, je peux aussi te montrer :

* **comment transformer ton log brut en dataset ML**
* **comment détecter automatiquement les tâches utilisateur**
* **comment entraîner un modèle qui comprend les activités complètes de l’utilisateur** (niveau recherche).
