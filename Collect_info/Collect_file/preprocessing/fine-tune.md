Très bonne question 👍 tu touches pile à la différence entre :

* **Fine-tune classique intégral** → on entraîne *tous* les paramètres du modèle (comme ton code avec `T5WithFusion`).
* **PEFT/LoRA** → on **gèle le modèle de base** et on n’entraîne que de petites couches d’adaptation (*LoRA adapters*).

---

## ⚡ Dans ton cas (avec `T5WithFusion`)

Comme tu as un modèle **custom** (T5WithFusion qui ajoute les `lexical_embeds` au premier token), tu dois combiner **les deux étapes** :

1. Créer ton modèle custom (`T5WithFusion`).
2. Appliquer PEFT/LoRA *par-dessus*.

---

### 🚀 Étapes concrètes

#### 1. Définir ton modèle fusionné

```python
model = T5WithFusion("google/flan-t5-small")
```

#### 2. Définir la config LoRA

Ici, on cible les modules internes de T5 (souvent `q`, `v`, ou `k` dans les `attention` layers).

```python
from peft import LoraConfig, get_peft_model, TaskType

lora_config = LoraConfig(
    r=32,
    lora_alpha=32,
    target_modules=["q", "v"],  # tu peux aussi tester ["k", "o"] selon l’expérience
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.SEQ_2_SEQ_LM
)
```

#### 3. Appliquer LoRA à ton modèle fusionné

```python
peft_model = get_peft_model(model, lora_config)
```

⚠️ Ici, `model` est ton **T5WithFusion**, pas le T5 de base.

#### 4. Vérifier les paramètres entraînables

```python
from peft import get_peft_model_state_dict

def print_trainable_parameters(model):
    trainable = 0
    total = 0
    for _, param in model.named_parameters():
        total += param.numel()
        if param.requires_grad:
            trainable += param.numel()
    print(f"Trainable params: {trainable} / {total} ({100 * trainable/total:.2f}%)")

print_trainable_parameters(peft_model)
```

→ tu devrais voir seulement **quelques millions** de paramètres entraînables (vs. 77M pour T5-small entier).

#### 5. Définir Trainer avec PEFT

```python
from transformers import TrainingArguments, Trainer

training_args = TrainingArguments(
    output_dir="./results_peft",
    learning_rate=1e-3,  # plus haut qu’en full fine-tune
    num_train_epochs=3,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    logging_steps=10,
    save_strategy="epoch",
    evaluation_strategy="epoch",
)

trainer = Trainer(
    model=peft_model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    data_collator=data_collator,  # ton DataCollatorWithFusion
)

trainer.train()
```

#### 6. Sauvegarde

```python
peft_model.save_pretrained("./peft_t5_withfusion")
tokenizer.save_pretrained("./peft_t5_withfusion")
```

---

## 🔑 Résumé

* **Full fine-tune (ton premier code)** : tout le modèle est ajusté, coûteux en VRAM et temps.
* **LoRA fine-tune (PEFT)** : seul un petit sous-ensemble de paramètres est entraîné, beaucoup plus léger.
* Dans ton cas → tu **wrap ton T5WithFusion avec LoRA** (au lieu de T5 direct).

---

👉 Veux-tu que je t’écrive une **version inference adaptée pour ton modèle T5WithFusion + LoRA** (comment faire `generate()` avec les embeddings lexicaux) ?
