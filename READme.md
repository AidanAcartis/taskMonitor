# Activity Monitoring & Classification System

## Project Overview

The **Activity Monitoring & Classification System** is a complex project developed using **Python**, **Bash**, and **Machine Learning**.  
The goal of this project is to monitor all user activities on a machine (opened files, visited pages, launched applications, executed commands), reconstruct detailed descriptions of these activities using ML models, and classify them into meaningful categories (e.g., gaming, studying quantum physics, watching movies).  

This project demonstrates strong skills in **system design, data collection, feature extraction, and ML modeling** using transformers and attention mechanisms for multimodal sequential understanding.  
It is intended as a research-oriented and practical tool for activity analysis, and showcases abstraction, algorithmic thinking, and software engineering capabilities.  

> ⚠️ **Note:** The project is still in progress. The integration into a complete software system are under development.

---

## Project Structure

The project is organized into the following main directories:

### 1. `Clustering/`

This folder contains scripts, notebooks, and data for clustering tasks and generating descriptive clusters.

#### `Clustering/Clustering_Project/`
Notebooks and data for clustering small tasks:
- **`Clustering_small_tasks.ipynb`** — Jupyter notebook implementing the clustering workflow on example activities.
- `activity_data.jsonl` — raw input data for clustering.
- `train_examples.pkl` — preprocessed training examples.
- `READme.md` — documentation for this subproject.

#### `Clustering/Global-Task-Description/`
Notebooks and data for training models to generate global task descriptions:
- **`Tuning_T5_Data_augmented.ipynb`** — notebook for fine-tuning Flan-T5 on augmented datasets.
- `DATA/` — folder containing datasets used for training.
- `READme.md` — documentation and notes for this subproject.

#### `Collect_info/Collect_file/File_Desc_Training_Model/Notebook_Training/`
Additional notebooks for model training and evaluation:
- **`File_desc_full_fine_tune.ipynb`** — notebook for full fine-tuning of the task description model.
- `ROUGE_histogramme.png`, `t-SNE_clusters_similar.png` — visualizations generated during training.
- `READme.md` — explanations and instructions for this training workflow.

#### Other files in `Clustering/`
- JSON files (`clusters_descriptions.jsonl`, `commands_descriptions_1.jsonl`, etc.) — structured data for clustering and feature extraction.
- Markdown files (`activity.md`, `clustering.md`, etc.) — documentation and exploratory analysis.
  
### 2. `Collect_info/`
Handles data collection from the system.  
- **`Collect_command/`** — Scripts to collect and describe executed commands.  
  - `save_history.py`, `script.sh` — scripts for collecting command history.  
  - `command_desc/command_describer_project/` — ML models and scripts to generate textual descriptions of commands.  
- **`Collect_data/`** — Scripts for collecting general activity data (`collect_data.py`).  
- **`Collect_file/`** — Scripts and notebooks for file monitoring and feature extraction, including the training dataset for the file description model.  
  - `File_Desc_Training_Model/` — Dataset and notebooks for fine-tuning ML models to describe file activities.  

### 3. `data/`
Contains raw and preprocessed data used for training and testing the models.  
- `create_data.py` — Script to process raw activity logs into structured training data.  
- `data_collect.txt`, `descriptions.txt` — Example datasets for training and testing.  

---

## Key Features

- Systematic collection of user activities across multiple sources (files, commands, applications).  
- Reconstruction of activity descriptions using ML models (transformers, Flan-T5).  
- Clustering and analysis of activities to detect patterns and classify behaviors.  
- Modular and extensible design, allowing integration with additional ML models or data sources.

---

## Future Work

- Complete the **final classification pipeline** for assigning activity categories.  
- Combine all modules into a **fully integrated software application**.  
- Improve model performance and implement real-time monitoring features.

---

## Usage

1. Collect data using scripts in `Collect_info/`.  
2. Preprocess and structure data using `data/create_data.py` and related scripts.  
3. Perform clustering and feature extraction in `Clustering/`.  
4. Train and fine-tune ML models using notebooks in `Collect_file/File_Desc_Training_Model/Notebook_Training/`.  
5. (Planned) Integrate classification pipeline to produce a complete activity monitoring application.

---

## License

This project is currently under development. All scripts and notebooks are for **research and educational purposes**.

