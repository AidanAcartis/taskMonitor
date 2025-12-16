# Test de Flan-T5-small sur mon dataset

J'ai testé les résultats donnés par Flan-T5-small à partir des données de mon dataset.

```python
index = 32
example = dataset["test"][index]

filename = example["filename"]
gold_desc = example["file_desc"]

prompt = f"""
Given the following filename, generate a short description of what the file is likely about.

Filename: {filename}

Description:
"""
````

## Génération du modèle

```python
inputs = tokenizer(prompt, return_tensors="pt")

outputs = original_model.generate(
    inputs["input_ids"],
    max_new_tokens=200,
    do_sample=False
)

predicted_desc = tokenizer.decode(
    outputs[0],
    skip_special_tokens=True,
    clean_up_tokenization_spaces=True
)
```

## Affichage des résultats

```python
dash_line = "-" * 80
print(dash_line)
print(f"FILENAME:\n{filename}")
print(dash_line)
print(f"REFERENCE DESCRIPTION:\n{gold_desc}\n")
print(dash_line)
print(f"MODEL ZERO-SHOT PREDICTION:\n{predicted_desc}")
```

### Quelques résultats observés

---

**FILENAME:**
audit_trail
**REFERENCE DESCRIPTION:**
Likely containing records of system activities or user actions for auditing purposes.
**MODEL ZERO-SHOT PREDICTION:**
Audit_trail is a telecommunications company that is headquartered in the city of San Francisco, California.

---

**FILENAME:**
migration_script
**REFERENCE DESCRIPTION:**
Likely used to automate or assist with data or system migrations.
**MODEL ZERO-SHOT PREDICTION:**
Migrationscript is a file that contains a migration script.

---

**FILENAME:**
network_settings
**REFERENCE DESCRIPTION:**
Likely containing settings or parameters related to network configuration.
**MODEL ZERO-SHOT PREDICTION:**
Network_settings is a network setting that is used to configure network settings.

---

**FILENAME:**
optimize_cache
**REFERENCE DESCRIPTION:**
Likely used to optimize or clear cached data on the system.
**MODEL ZERO-SHOT PREDICTION:**
Optimize_cache is a file that is used to compress files.

---

Je remarque que rarement le modèle donne des réponses acceptables et que, le plus souvent, les résultats sont dérangeants.

Je comprends donc qu'un simple fine-tune ne suffira pas pour améliorer significativement les prédictions. Il faudra enseigner au modèle certaines techniques de génération.

J'ai pensé à une stratégie pour un fine-tune efficace :

1. Apprendre au modèle à générer des champs lexicaux proches des mots constituant le filename. Cela peut avoir plusieurs sens, mais je veux m'assurer de conserver les sens communs aux mots du filename.
2. Apprendre au modèle à former des phrases naturelles à partir de ces champs.
3. Comparer la phrase générée avec `example["file_desc"]` et ajuster l'entraînement pour que le modèle produise la bonne description.

Je veux maintenant savoir si c'est réellement possible de mettre cela en œuvre et comment m'y prendre.

