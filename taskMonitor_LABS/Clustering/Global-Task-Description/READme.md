# Global Task Inference from Task Items

## Overview

This project explores how a language model can infer a **global task description** from a list of low-level task items.

In many real-world scenarios, users perform a sequence of actions using tools, files, commands, or interfaces. While each step describes a small action, these actions often correspond to a **higher-level objective**.

The goal of this project is to train a model that can automatically infer this higher-level objective from the list of task items.

For example:

Input task items:

* open server.js in /api using VS Code
* install express dependencies with npm
* define routes in routes.js
* test endpoints with Postman
* deploy API with docker-compose

Expected output:

Build and deploy a REST API service.

To achieve this, I fine-tune **FLAN-T5-small** using **LoRA adapters** on a dataset of task sequences and their corresponding global descriptions.

---

# Dataset

The dataset is stored as a JSONL file:

```
DATA_AUGMENTED_ENRICHED.jsonl
```

Each entry contains:

* an identifier
* multiple versions of the task items
* a global task description

Example structure:

```
{
  "id": 0,
  "task_items_versions": [
    {
      "version_type": "original",
      "task_items": [...]
    },
    {
      "version_type": "paraphrase_1",
      "task_items": [...]
    }
  ],
  "global_task_description": "Develop and maintain responsive websites..."
}
```

The dataset includes several **augmented versions of task sequences**:

* original
* paraphrase_1
* paraphrase_2
* tool_replaced
* keyword_removed

This augmentation helps the model learn **semantic patterns instead of memorizing specific tool names or phrases**.

---

# Dataset Exploration

The notebook first loads and inspects the dataset using pandas:

```
df = pd.read_json('DATA_AUGMENTED_ENRICHED.jsonl', lines=True)
```

Some statistics about the dataset:

| Metric                            | Value          |
| --------------------------------- | -------------- |
| Number of samples                 | 2000           |
| Average global description length | ~52 characters |
| Average number of task items      | ~45            |

This indicates that the dataset contains relatively **rich task sequences**, which encourages the model to learn abstraction.

---

# Data Preparation

The dataset stores multiple versions of task items inside nested structures.

I first normalize and extract these versions into separate columns:

* original
* paraphrase_1
* paraphrase_2
* tool_replaced
* keyword_removed

This allows me to generate multiple training examples per task.

---

# Text Normalization

Before training, task items undergo several normalization steps:

1. **Syntax normalization**

   * remove formatting artifacts
   * normalize spacing
   * clean quotes

2. **Path normalization**

Paths such as:

```
/var/www/project
/api/routes
```

are replaced with a placeholder:

```
<PATH>
```

This prevents the model from overfitting to specific directories.

Example transformation:

```
server.js file in /api opened with VS Code
```

becomes

```
server.js file in <PATH> opened with VS Code
```

---

# Prompt Construction

Instead of directly feeding the task list to the model, I construct a structured prompt.

Example prompt:

```
You are given a list of task items:

- ...
- ...
- ...

Your goal is to infer the underlying global objective.

Step 1: Extract key concepts.
Step 2: Identify the domain.
Step 3: Determine the main action.
Step 4: Produce a concise global task description.
```

This prompt encourages the model to perform **structured reasoning** before generating the final description.

---

# Training Setup

Model:

```
google/flan-t5-small
```

Training method:

```
LoRA (Low-Rank Adaptation)
```

LoRA allows efficient fine-tuning by updating only a small number of parameters.

Configuration:

* rank (r): 32
* alpha: 32
* dropout: 0.05

Sequence lengths:

* input length: 512 tokens
* target length: 128 tokens

---

# Dataset Split

The dataset is converted to HuggingFace format and split into:

* 90% training
* 10% validation

```
dataset = dataset.train_test_split(test_size=0.1, seed=42)
```

---

# Training

Training is performed using the HuggingFace Trainer.

Key parameters:

* epochs: 50
* evaluation every 50 steps
* beam search used during generation
* model saved with LoRA adapters

The trained adapter is saved separately from the base model.

---

# Inference

After training, the LoRA adapter is loaded on top of the base FLAN-T5 model.

The model receives a list of task items and generates a concise global description.

Example usage:

```
prediction = generate_prediction(task_items)
```

Example input:

* open router admin page
* configure WiFi SSID and password
* test connectivity with ping
* measure bandwidth with speedtest

Example output:

Configure a home WiFi network.

---

# Example Evaluation Tasks

The notebook evaluates the model on several domains:

* machine learning workflows
* cybersecurity analysis
* API development
* Linux server administration
* mobile application design
* cloud infrastructure automation
* business data analysis
* video editing and publishing
* gaming and streaming
* online shopping workflows

These tests help evaluate how well the model **generalizes across different domains**.

---

# Project Goal

This project explores a broader research question:

How can we automatically infer a **high-level human objective** from a sequence of low-level actions?

Potential applications include:

* workflow understanding
* user intent detection
* automation systems
* developer activity analysis
* intelligent assistants

---

# Requirements

Main libraries used in this project:

* transformers
* peft
* datasets
* torch
* pandas
* scikit-learn

---

# Running the Notebook

1. Install dependencies

```
pip install transformers datasets peft torch pandas scikit-learn
```

2. Download the dataset.

3. Run the notebook cells in order:

* dataset loading
* preprocessing
* prompt construction
* training
* evaluation

---

# Notes

This repository focuses on **learning task abstraction**, where the model maps a sequence of actions to a single higher-level goal.

The notebook contains the complete pipeline:

* dataset processing
* prompt engineering
* LoRA fine-tuning
* inference
* qualitative evaluation.
