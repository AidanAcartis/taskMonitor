# Correction complète du pipeline d’entraînement avec fusion d’embeddings

Je corrige ici l’ensemble du pipeline :  
- le modèle,  
- le data collator,  
- les arguments d’entraînement,  
- ainsi que l’erreur rencontrée lors de l’appel à `trainer.train()`.

L’objectif est d’obtenir un entraînement stable et cohérent, où les `lexical_embeds` sont correctement intégrés au modèle.

---

## 1. Fusion correcte des `lexical_embeds` dans T5

Au lieu d’écraser un token existant, j’intègre les `lexical_embeds` comme un **token spécial ajouté au début de la séquence d’embeddings**.  
Cela permet au mécanisme d’attention de T5 de les exploiter naturellement.

```python
import torch
import torch.nn as nn
from transformers import T5ForConditionalGeneration, T5Config

class T5WithFusion(nn.Module):
    def __init__(self, model_name="google/flan-t5-small"):
        super().__init__()
        self.config = T5Config.from_pretrained(model_name)
        self.t5 = T5ForConditionalGeneration.from_pretrained(model_name)

        # Projection des embeddings lexicaux vers d_model
        self.proj = nn.Linear(self.config.d_model, self.config.d_model)

    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        labels=None,
        lexical_embeds=None,
        **kwargs
    ):
        # Génération des embeddings à partir des input_ids
        inputs_embeds = self.t5.encoder.embed_tokens(input_ids)

        if lexical_embeds is not None:
            # (B, D) -> (B, 1, D)
            lexical_embeds = self.proj(lexical_embeds).unsqueeze(1)

            # Concaténation comme token spécial
            inputs_embeds = torch.cat([lexical_embeds, inputs_embeds], dim=1)

            # Mise à jour du attention_mask
            new_mask = torch.ones(
                (attention_mask.size(0), attention_mask.size(1) + 1),
                device=attention_mask.device,
                dtype=attention_mask.dtype
            )
            new_mask[:, 1:] = attention_mask
            attention_mask = new_mask

        return self.t5(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            labels=labels,
            **kwargs
        )
````

---

## 2. DataCollator avec fusion

Je corrige deux points essentiels :

* les `labels` utilisent `-100` pour ignorer les tokens de padding,
* les `lexical_embeds` sont explicitement convertis en `float32`.

```python
class DataCollatorWithFusion:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, batch):
        input_ids = torch.stack([torch.tensor(x["input_ids"]) for x in batch])
        attention_mask = torch.stack([torch.tensor(x["attention_mask"]) for x in batch])
        labels = torch.stack([torch.tensor(x["labels"]) for x in batch])

        labels = labels.clone()
        labels[labels == self.tokenizer.pad_token_id] = -100

        lexical_embeds = torch.stack([
            torch.tensor(x["lexical_embeds"], dtype=torch.float32)
            for x in batch
        ])

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
            "lexical_embeds": lexical_embeds,
        }
```

---

## 3. Arguments d’entraînement

Je définis des paramètres plus stables pour T5, en m’assurant que HuggingFace ne supprime pas `lexical_embeds`.

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="/content/drive/MyDrive/Gen_Desc_Model/results_peft",
    learning_rate=5e-5,
    num_train_epochs=10,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    logging_steps=10,
    save_strategy="epoch",
    eval_strategy="epoch",
    report_to="none",
    fp16=True,
    remove_unused_columns=False
)
```

---

## 4. Vérification avant l’entraînement

Avant de lancer l’entraînement, je vérifie qu’une batch est correctement formée.

```python
collator = DataCollatorWithFusion(tokenizer)
sample_batch = [tokenized_datasets["train"][i] for i in range(2)]
batch = collator(sample_batch)

print(batch["input_ids"].shape)
print(batch["attention_mask"].shape)
print(batch["labels"].shape)
print(batch["lexical_embeds"].shape)
```

---

## 5. Problème rencontré lors de `trainer.train()`

L’erreur observée est :

```
TypeError: ... got multiple values for keyword argument 'inputs_embeds'
```

### Cause

Le `Trainer` transmet automatiquement `input_ids` au modèle.
Dans mon `forward`, je reconstruis manuellement `inputs_embeds` **et** HuggingFace essaie aussi d’en passer via `**kwargs`.

Cela provoque un conflit : `inputs_embeds` est fourni deux fois.

---

## 6. Correction du problème

La solution consiste à **supprimer explicitement `input_ids` des arguments transmis au modèle T5** lorsque j’utilise `inputs_embeds`.

Correction appliquée dans le `forward` :

```python
return self.t5(
    inputs_embeds=inputs_embeds,
    attention_mask=attention_mask,
    labels=labels,
)
```

Je m’assure également de **ne jamais passer `input_ids` en même temps que `inputs_embeds`**.

---

## 7. Initialisation du Trainer

```python
from transformers import Trainer

trainer = Trainer(
    model=peft_model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    data_collator=data_collator,
)
```

Puis je lance :

```python
trainer.train()
```

---

## 8. Résultat attendu

Après ces corrections :

* l’erreur sur `inputs_embeds` disparaît,
* la loss n’est plus bloquée à `0.0`,
* le modèle apprend réellement à exploiter les `lexical_embeds`,
* l’entraînement est stable en train et en validation.

---

