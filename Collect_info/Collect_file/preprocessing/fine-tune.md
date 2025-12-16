# Fine-tuning classique vs PEFT/LoRA dans mon cas

Cette question touche directement à la différence entre deux approches :

- **Fine-tuning intégral** : j’entraîne l’ensemble des paramètres du modèle.
- **PEFT / LoRA** : je gèle le modèle de base et je n’entraîne que de petites couches d’adaptation (les adapters LoRA).

---

## Mon cas spécifique : T5WithFusion

J’utilise un modèle **custom**, `T5WithFusion`, qui modifie l’entrée de T5 en intégrant des `lexical_embeds` sous forme de token spécial.  
Je ne peux donc pas appliquer LoRA directement sur un T5 standard sans tenir compte de cette modification.

La bonne approche consiste à :

1. Construire mon modèle personnalisé (`T5WithFusion`).
2. Appliquer **LoRA par-dessus ce modèle**, et non sur T5 seul.

---

## Étapes concrètes

### 1. Créer le modèle fusionné

Je commence par instancier mon modèle personnalisé :

```python
model = T5WithFusion("google/flan-t5-small")
````

À ce stade, il s’agit encore d’un fine-tuning classique si je l’entraîne tel quel.

---

### 2. Définir la configuration LoRA

Je définis ensuite la configuration PEFT.
Je cible les modules internes de l’attention de T5, en pratique les projections `q` et `v`, qui sont généralement les plus efficaces.

```python
from peft import LoraConfig, get_peft_model, TaskType

lora_config = LoraConfig(
    r=32,
    lora_alpha=32,
    target_modules=["q", "v"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.SEQ_2_SEQ_LM
)
```

---

### 3. Appliquer LoRA sur le modèle fusionné

J’applique ensuite LoRA **sur mon modèle custom**, et non sur un T5 brut.

```python
peft_model = get_peft_model(model, lora_config)
```

À partir de là :

* le backbone T5 est gelé,
* seules les couches LoRA (et éventuellement mes couches ajoutées) sont entraînables.

---

### 4. Vérifier les paramètres entraînables

Avant d’entraîner, je vérifie que seuls quelques paramètres sont bien entraînables.

```python
def print_trainable_parameters(model):
    trainable = 0
    total = 0
    for _, param in model.named_parameters():
        total += param.numel()
        if param.requires_grad:
            trainable += param.numel()
    print(f"Trainable params: {trainable} / {total} ({100 * trainable / total:.2f}%)")

print_trainable_parameters(peft_model)
```

Je dois observer une fraction très faible de paramètres entraînables par rapport au total, ce qui confirme que LoRA est bien en place.

---

### 5. Définir le Trainer avec PEFT

Je peux ensuite utiliser le `Trainer` de Hugging Face normalement, en conservant mon `DataCollatorWithFusion`.

```python
from transformers import TrainingArguments, Trainer

training_args = TrainingArguments(
    output_dir="./results_peft",
    learning_rate=1e-3,
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
    data_collator=data_collator,
)

trainer.train()
```

Dans ce cadre, le learning rate est plus élevé que pour un fine-tuning intégral, car seules des couches d’adaptation sont entraînées.

---

### 6. Sauvegarde du modèle

Une fois l’entraînement terminé, je sauvegarde uniquement les poids LoRA et le tokenizer.

```python
peft_model.save_pretrained("./peft_t5_withfusion")
tokenizer.save_pretrained("./peft_t5_withfusion")
```

Cela me permet de recharger facilement le modèle plus tard sans avoir à stocker tout le backbone.

---

## Synthèse

* Le **fine-tuning intégral** entraîne tous les paramètres du modèle, ce qui est coûteux en VRAM et en temps.
* Le **fine-tuning LoRA (PEFT)** entraîne uniquement un petit sous-ensemble de paramètres, ce qui est beaucoup plus léger.
* Dans mon cas, la bonne pratique est de **construire d’abord `T5WithFusion`, puis de l’envelopper avec LoRA**.

Cette approche me permet de combiner :

* une architecture personnalisée,
* une adaptation efficace,
* et un coût d’entraînement raisonnable.


