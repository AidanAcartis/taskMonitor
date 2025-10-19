Parfait 🚀 je vais corriger **tous les points** que j’ai listés :
👉 modèle, data collator, training arguments.
Comme ça tu as un pipeline propre et stable pour ton entraînement.

---

# ✅ Corrections complètes

## 1. Fusion de `lexical_embeds`

Au lieu d’**écraser le premier token**, on crée un **token spécial** en concaténant `lexical_embeds` à la séquence d’embeddings.
Ainsi, l’attention T5 peut apprendre à l’utiliser naturellement.

```python
import torch
import torch.nn as nn
from transformers import T5ForConditionalGeneration, T5Config

class T5WithFusion(nn.Module):
    def __init__(self, model_name="google/flan-t5-small", hidden_size=512):
        super().__init__()
        self.config = T5Config.from_pretrained(model_name)
        self.t5 = T5ForConditionalGeneration.from_pretrained(model_name)
        self.hidden_size = hidden_size

        # Projeter lexical_embeds si nécessaire
        self.proj = nn.Linear(hidden_size, self.config.d_model)

    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        labels=None,
        lexical_embeds=None,
        **kwargs
    ):
        # Embeddings initiaux des tokens
        inputs_embeds = self.t5.encoder.embed_tokens(input_ids)  # (B, L, D)

        if lexical_embeds is not None:
            # lexical_embeds : (B, D) → (B, 1, D)
            lexical_embeds = self.proj(lexical_embeds).unsqueeze(1)

            # Concaténer comme "token spécial"
            inputs_embeds = torch.cat([lexical_embeds, inputs_embeds], dim=1)

            # Adapter attention_mask
            new_mask = torch.ones(
                (attention_mask.shape[0], attention_mask.shape[1] + 1),
                dtype=attention_mask.dtype,
                device=attention_mask.device,
            )
            new_mask[:, 1:] = attention_mask
            attention_mask = new_mask

        # Forward classique T5
        return self.t5(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            labels=labels,
            **kwargs
        )
```

---

## 2. DataCollatorWithFusion

Corrige :

* `labels` → remplacer `pad_token_id` par `-100`.
* `lexical_embeds` → cast explicite en `float32`.

```python
class DataCollatorWithFusion:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, batch):
        input_ids = torch.stack([torch.tensor(x["input_ids"]) for x in batch])
        attention_mask = torch.stack([torch.tensor(x["attention_mask"]) for x in batch])
        labels = torch.stack([torch.tensor(x["labels"]) for x in batch])

        # Corriger labels : ignorer pad tokens
        labels = labels.clone()
        labels[labels == self.tokenizer.pad_token_id] = -100

        # Embeddings lexicaux
        lexical_embeds = torch.stack([
            torch.tensor(x["lexical_embeds"], dtype=torch.float32) for x in batch
        ])

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
            "lexical_embeds": lexical_embeds,
        }
```

---

## 3. TrainingArguments

Corrige :

* `learning_rate` → plus petit (`5e-5` ou `1e-4`).
* `remove_unused_columns=False` (sinon HuggingFace jette `lexical_embeds`).
* Plus d’epochs (`5-10` mini).

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="/content/drive/MyDrive/Gen_Desc_Model/results_peft",
    learning_rate=5e-5,   # plus stable pour T5
    num_train_epochs=10,  # plus long, dataset petit
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    logging_steps=10,
    save_strategy="epoch",
    eval_strategy="epoch",
    report_to="none",
    fp16=True,
    remove_unused_columns=False,  # ⚠️ essentiel pour garder lexical_embeds
)
```

---

## 4. Vérifications avant training

Avant de lancer `Trainer`, fais :

```python
# Vérifier une batch
collator = DataCollatorWithFusion(tokenizer)
sample_batch = [tokenized_datasets["train"][i] for i in range(2)]
batch = collator(sample_batch)

print(batch["input_ids"].shape)       # (B, L)
print(batch["attention_mask"].shape)  # (B, L)
print(batch["labels"].shape)          # (B, L)
print(batch["lexical_embeds"].shape)  # (B, D)
print(batch["labels"])                # voir si -100 apparaît bien
```

---

# 🚀 Résultat attendu après corrections

* Plus de `train_loss=0.0`.
* Plus de `NaN` en validation.
* Le modèle peut **apprendre à utiliser lexical_embeds** car il est intégré comme **vrai token spécial**.

---

Veux-tu que je t’écrive aussi un **script complet et minimal** (du preprocessing → collator → modèle → Trainer) que tu peux lancer directement sans recoller les morceaux ?




Nouveau probleme '---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
/tmp/ipython-input-4032920361.py in <cell line: 0>()
----> 1 trainer.train()

13 frames
/tmp/ipython-input-3294434893.py in forward(self, input_ids, attention_mask, labels, lexical_embeds, **kwargs)
     31                 ], dim=1)
     32 
---> 33         return self.t5(
     34             input_ids=None,
     35             attention_mask=attention_mask,

TypeError: T5ForConditionalGeneration(
  (shared): Embedding(32128, 512)
  (encoder): T5Stack(
    (embed_tokens): Embedding(32128, 512)
    (block): ModuleList(
      (0): T5Block(
        (layer): ModuleList(
          (0): T5LayerSelfAttention(
            (SelfAttention): T5Attention(
              (q): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (k): Linear(in_features=512, out_features=384, bias=False)
              (v): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (o): Linear(in_features=384, out_features=512, bias=False)
              (relative_attention_bias): Embedding(32, 6)
            )
            (layer_norm): T5LayerNorm()
            (dropout): Dropout(p=0.1, inplace=False)
          )
          (1): T5LayerFF(
            (DenseReluDense): T5DenseGatedActDense(
              (wi_0): Linear(in_features=512, out_features=1024, bias=False)
              (wi_1): Linear(in_features=512, out_features=1024, bias=False)
              (wo): Linear(in_features=1024, out_features=512, bias=False)
              (dropout): Dropout(p=0.1, inplace=False)
              (act): NewGELUActivation()
            )
            (layer_norm): T5LayerNorm()
            (dropout): Dropout(p=0.1, inplace=False)
          )
        )
      )
      (1-7): 7 x T5Block(
        (layer): ModuleList(
          (0): T5LayerSelfAttention(
            (SelfAttention): T5Attention(
              (q): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (k): Linear(in_features=512, out_features=384, bias=False)
              (v): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (o): Linear(in_features=384, out_features=512, bias=False)
            )
            (layer_norm): T5LayerNorm()
            (dropout): Dropout(p=0.1, inplace=False)
          )
          (1): T5LayerFF(
            (DenseReluDense): T5DenseGatedActDense(
              (wi_0): Linear(in_features=512, out_features=1024, bias=False)
              (wi_1): Linear(in_features=512, out_features=1024, bias=False)
              (wo): Linear(in_features=1024, out_features=512, bias=False)
              (dropout): Dropout(p=0.1, inplace=False)
              (act): NewGELUActivation()
            )
            (layer_norm): T5LayerNorm()
            (dropout): Dropout(p=0.1, inplace=False)
          )
        )
      )
    )
    (final_layer_norm): T5LayerNorm()
    (dropout): Dropout(p=0.1, inplace=False)
  )
  (decoder): T5Stack(
    (embed_tokens): Embedding(32128, 512)
    (block): ModuleList(
      (0): T5Block(
        (layer): ModuleList(
          (0): T5LayerSelfAttention(
            (SelfAttention): T5Attention(
              (q): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (k): Linear(in_features=512, out_features=384, bias=False)
              (v): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (o): Linear(in_features=384, out_features=512, bias=False)
              (relative_attention_bias): Embedding(32, 6)
            )
            (layer_norm): T5LayerNorm()
            (dropout): Dropout(p=0.1, inplace=False)
          )
          (1): T5LayerCrossAttention(
            (EncDecAttention): T5Attention(
              (q): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (k): Linear(in_features=512, out_features=384, bias=False)
              (v): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (o): Linear(in_features=384, out_features=512, bias=False)
            )
            (layer_norm): T5LayerNorm()
            (dropout): Dropout(p=0.1, inplace=False)
          )
          (2): T5LayerFF(
            (DenseReluDense): T5DenseGatedActDense(
              (wi_0): Linear(in_features=512, out_features=1024, bias=False)
              (wi_1): Linear(in_features=512, out_features=1024, bias=False)
              (wo): Linear(in_features=1024, out_features=512, bias=False)
              (dropout): Dropout(p=0.1, inplace=False)
              (act): NewGELUActivation()
            )
            (layer_norm): T5LayerNorm()
            (dropout): Dropout(p=0.1, inplace=False)
          )
        )
      )
      (1-7): 7 x T5Block(
        (layer): ModuleList(
          (0): T5LayerSelfAttention(
            (SelfAttention): T5Attention(
              (q): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (k): Linear(in_features=512, out_features=384, bias=False)
              (v): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (o): Linear(in_features=384, out_features=512, bias=False)
            )
            (layer_norm): T5LayerNorm()
            (dropout): Dropout(p=0.1, inplace=False)
          )
          (1): T5LayerCrossAttention(
            (EncDecAttention): T5Attention(
              (q): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (k): Linear(in_features=512, out_features=384, bias=False)
              (v): lora.Linear(
                (base_layer): Linear(in_features=512, out_features=384, bias=False)
                (lora_dropout): ModuleDict(
                  (default): Dropout(p=0.05, inplace=False)
                )
                (lora_A): ModuleDict(
                  (default): Linear(in_features=512, out_features=32, bias=False)
                )
                (lora_B): ModuleDict(
                  (default): Linear(in_features=32, out_features=384, bias=False)
                )
                (lora_embedding_A): ParameterDict()
                (lora_embedding_B): ParameterDict()
                (lora_magnitude_vector): ModuleDict()
              )
              (o): Linear(in_features=384, out_features=512, bias=False)
            )
            (layer_norm): T5LayerNorm()
            (dropout): Dropout(p=0.1, inplace=False)
          )
          (2): T5LayerFF(
            (DenseReluDense): T5DenseGatedActDense(
              (wi_0): Linear(in_features=512, out_features=1024, bias=False)
              (wi_1): Linear(in_features=512, out_features=1024, bias=False)
              (wo): Linear(in_features=1024, out_features=512, bias=False)
              (dropout): Dropout(p=0.1, inplace=False)
              (act): NewGELUActivation()
            )
            (layer_norm): T5LayerNorm()
            (dropout): Dropout(p=0.1, inplace=False)
          )
        )
      )
    )
    (final_layer_norm): T5LayerNorm()
    (dropout): Dropout(p=0.1, inplace=False)
  )
  (lm_head): Linear(in_features=512, out_features=32128, bias=False)
) got multiple values for keyword argument 'inputs_embeds'
', ici :"from transformers import TrainingArguments, Trainer

training_args = TrainingArguments(
    output_dir="/content/drive/MyDrive/Gen_Desc_Model/results_peft",
    learning_rate=5e-5, #Plus stable pour T5
    num_train_epochs=10, # plus long, dataset petit
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    logging_steps=10,
    save_strategy="epoch",
    eval_strategy="epoch",
    report_to="none",
    fp16=True,
    remove_unused_columns=False,
)

trainer = Trainer(
    model=peft_model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    data_collator=data_collator,  # the DataCollatorWithFusion
)", "trainer.train()"