---

# 📂 File Description Training Model

This project trains a model to **generate human-like descriptions of files** (based on filename, extension, directory, and application).
It follows a multi-step pipeline: collecting file names, extracting file properties, generating synthetic descriptions, building a dataset, and finally training a fine-tuned model.

---

## 🏗 Project Structure

```
File_Desc_Training_Model/
│
├── dataset/                     # Final dataset for training
│   ├── file_desc_data/          # JSONL dataset of filenames and descriptions
│   └── file-description.py
│
├── Get_data_process/            # Data collection and preprocessing
│   ├── Get_Files/               # File name generation and property extraction
│   └── File_scrap_desc/         # Scraping AI-generated file descriptions
│
├── Notebook_Training/           # Training notebooks
│   └── File_desc_full_fine_tune.ipynb
│
└── README.md                    # Project documentation
```

---

## 🚀 Step 1 – Generate Synthetic File Names

**Location:** `Get_data_process/Get_Files/get_examples_GPT.py`

This script automatically generates **file names** in bulk (e.g., `extract_window_events.sh - Collect_file - Visual Studio Code`).

* It uses `undetected_chromedriver` + `selenium` to interact with ChatGPT via the browser.
* Prompts are crafted to produce 35 new file entries per batch.
* The generated names are saved into `Files_list.txt`.

Result:

```
0 extract_window_events.sh - Collect_file - Visual Studio Code
1 script_to_get_title.sh - all_script - Visual Studio Code
...
```

---

## 📑 Step 2 – Extract File Properties

**Location:** `Get_data_process/Get_Files/get_files_proprities.py`

This script converts raw file name entries into structured JSON format:

* Splits each entry into **filename**, **extension**, **directory**, and **application**.
* Outputs the structured version into `Files_list.jsonl`.

Example output:

```json
{"id": "0", "filename": "extract_window_events", "extension": "sh", "directory": "Collect_file", "application": "Visual Studio Code"}
```

---

## 📝 Step 3 – Generate File Descriptions

**Location:** `Get_data_process/File_scrap_desc/scrap_description.py`

This script sends each structured file entry (`filename + extension + directory + application`) to ChatGPT and asks for a short description.

* The prompt asks for a **2-sentence description**: what the file is, what it does, where it is, and which app can open it.
* The script uses Selenium automation to capture the responses.
* Results are stored in `response.jsonl`.

Example response:

```json
{
  "id": "0",
  "filename": "extract_window_events",
  "extension": "sh",
  "directory": "Collect_file",
  "application": "Visual Studio Code",
  "description": "This is a shell script (.sh) named extract_window_events.sh located in the Collect_file directory. It likely extracts window-related events from a system or application and can be opened and edited using Visual Studio Code."
}
```

---

## 📚 Step 4 – Build Final Dataset

**Location:** `dataset/file-description.py`

This script extracts only the relevant fields (**filename** and **description**) and prepares the final training dataset in JSONL format.

* Input: `response.jsonl`
* Output: `file_description.jsonl`

Final dataset example:

```json
{"id": "0", "filename": "extract_window_events", "file_desc": "This is a shell script (.sh) named extract_window_events.sh located in the Collect_file directory. It likely extracts window-related events from a system or application and can be opened and edited using Visual Studio Code."}
```

---

## 🧑‍💻 Step 5 – Model Training

**Location:** `Notebook_Training/File_desc_full_fine_tune.ipynb`

This notebook fine-tunes a language model (e.g., Flan-T5, etc.) on the `file_description.jsonl` dataset.

* **Input:** filename (and context like extension, directory, application).
* **Output:** natural language description of the file.

The training process includes:

1. Dataset loading & preprocessing.
2. Model fine-tuning with PEFT or full fine-tuning.
3. Evaluation with metrics like ROUGE.
4. Comparison with baseline and base models.

---

## ✅ Summary of Workflow

1. **Generate filenames** → via GPT prompts (`get_examples_GPT.py`).
2. **Extract properties** → structured JSON (`get_files_proprities.py`).
3. **Generate descriptions** → AI-generated explanations (`scrap_description.py`).
4. **Build final dataset** → clean JSONL (`file-description.py`).
5. **Train model** → fine-tuned model to describe files (`File_desc_full_fine_tune.ipynb`).

---
