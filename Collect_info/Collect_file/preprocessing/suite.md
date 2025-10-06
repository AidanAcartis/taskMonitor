Parfait ✅ ton **préprocessing est nickel** : tu as bien maintenant les 4 colonnes :

* `input_ids`
* `attention_mask`
* `labels`
* `lexical_embeds`

👉 Mais attention : HuggingFace `Trainer` **n’accepte pas directement** `lexical_embeds`.
Il faut :

1. **Un modèle custom** (`T5WithFusion`) qui sait lire `lexical_embeds` et les injecter.
2. **Un collator** qui regroupe `lexical_embeds` en batch correctement.

---

### 1️⃣ Le modèle custom (fusion au premier token)

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
        lexical_embeds=None,  # <- ton vecteur externe
    ):
        # embeddings initiaux (batch, seq_len, hidden_dim)
        inputs_embeds = self.t5.encoder.embed_tokens(input_ids)

        # injecter lexical_embeds sur le 1er token
        if lexical_embeds is not None:
            lexical_embeds = lexical_embeds.unsqueeze(1)  # (batch, 1, hidden_dim)
            inputs_embeds[:, 0:1, :] = inputs_embeds[:, 0:1, :] + lexical_embeds

        # forward classique
        return self.t5(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            labels=labels,
        )
```

---

### 2️⃣ DataCollator pour gérer lexical\_embeds

```python
from torch.utils.data import DataLoader

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
            "lexical_embeds": lexical_embeds,  # envoyé au modèle
        }
```

---

### 3️⃣ Utilisation avec HuggingFace Trainer

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

🚀 Avec ça :

* Ton dataset **alimente lexical\_embeds au modèle**.
* Le modèle `T5WithFusion` **injecte lexical\_embeds dans le premier token**.
* HuggingFace `Trainer` entraîne normalement avec cette nouvelle architecture enrichie.

---

Veux-tu que je t’ajoute aussi **la version inference** (génération avec `generate()`) adaptée à ce `T5WithFusion` ?
