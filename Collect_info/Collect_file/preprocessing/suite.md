# Intégration de `lexical_embeds` dans Hugging Face Trainer

## État actuel du préprocessing

À ce stade, mon préprocessing est correct : chaque exemple du dataset contient bien les quatre champs suivants :

- `input_ids`
- `attention_mask`
- `labels`
- `lexical_embeds`

Cela signifie que toutes les informations nécessaires sont présentes au niveau des données.  
Cependant, **Hugging Face `Trainer` ne sait pas exploiter automatiquement un champ supplémentaire comme `lexical_embeds`**.

Pour que cela fonctionne correctement, deux éléments sont indispensables :

1. Un **modèle custom** capable de recevoir `lexical_embeds` et de les injecter dans le calcul.
2. Un **data collator personnalisé** pour regrouper correctement `lexical_embeds` au niveau du batch.

---

## 1. Modèle custom : `T5WithFusion`

J’utilise un wrapper autour de `T5ForConditionalGeneration` afin d’injecter les embeddings lexicaux directement dans les embeddings d’entrée.

Le principe est simple :
- Je récupère les embeddings des tokens via l’encodeur T5.
- J’ajoute `lexical_embeds` au premier token (position 0).
- Le reste du modèle fonctionne normalement.

```python
import torch
import torch.nn as nn
from transformers import T5ForConditionalGeneration

class T5WithFusion(nn.Module):
    def __init__(self, model_name="google/flan-t5-small"):
        super().__init__()
        self.t5 = T5ForConditionalGeneration.from_pretrained(model_name)

    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        labels=None,
        lexical_embeds=None,
    ):
        # Récupération des embeddings des tokens
        inputs_embeds = self.t5.encoder.embed_tokens(input_ids)

        # Injection de lexical_embeds sur le premier token
        if lexical_embeds is not None:
            lexical_embeds = lexical_embeds.unsqueeze(1)  # (batch, 1, hidden_dim)
            inputs_embeds[:, 0:1, :] = inputs_embeds[:, 0:1, :] + lexical_embeds

        # Forward classique de T5
        return self.t5(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            labels=labels,
        )
````

Dans cette architecture, `lexical_embeds` agit comme un **biais sémantique global**, injecté dès l’entrée de l’encodeur.

---

## 2. Data collator personnalisé

Le rôle du data collator est de :

* empiler correctement les tenseurs (`input_ids`, `attention_mask`, `labels`),
* regrouper `lexical_embeds` sous forme d’un tenseur `(batch_size, hidden_dim)`.

```python
class DataCollatorWithFusion:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, batch):
        input_ids = torch.stack([torch.tensor(x["input_ids"]) for x in batch])
        attention_mask = torch.stack([torch.tensor(x["attention_mask"]) for x in batch])
        labels = torch.stack([torch.tensor(x["labels"]) for x in batch])
        lexical_embeds = torch.stack([torch.tensor(x["lexical_embeds"]) for x in batch])

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
            "lexical_embeds": lexical_embeds,
        }
```

Sans ce collator, `lexical_embeds` serait ignoré ou mal formé lors de l’entraînement.

---

## 3. Entraînement avec Hugging Face Trainer

Une fois le modèle et le collator définis, l’utilisation avec `Trainer` devient standard.

```python
from transformers import TrainingArguments, Trainer

model = T5WithFusion("google/flan-t5-small")
data_collator = DataCollatorWithFusion(tokenizer)

training_args = TrainingArguments(
    output_dir="./results",
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    learning_rate=5e-5,
    num_train_epochs=3,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    logging_dir="./logs",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    data_collator=data_collator,
)

trainer.train()
```

---

## Résultat attendu

Avec cette configuration :

* `lexical_embeds` est bien transmis du dataset jusqu’au modèle.
* Le modèle `T5WithFusion` exploite explicitement cette information au niveau des embeddings.
* L’entraînement fonctionne normalement avec `Trainer`, sans hack ni modification interne.

Cette approche me permet d’évaluer proprement l’impact d’un **vecteur sémantique global externe** sur la génération de descriptions.

---


