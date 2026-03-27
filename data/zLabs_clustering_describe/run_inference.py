"""
run_inference.py
----------------
Lit events_normalized.csv, génère une description pour chaque fichier,
et sauvegarde les résultats dans events_with_descriptions.csv.

Usage
-----
    python run_inference.py
"""

import os
import re
import torch
import torch.nn as nn
import pandas as pd
from transformers import AutoTokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────
# CONFIG — modifier si nécessaire
# ─────────────────────────────────────────────
CSV_INPUT   = "events_normalized.csv"
CSV_OUTPUT  = "events_with_descriptions.csv"
MODEL_DIR   = "./Gen_Desc_Model/full_finetuned"
LEXICAL_DIM = 512
BATCH_SIZE  = 8
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ─────────────────────────────────────────────
# MODEL
# ─────────────────────────────────────────────
class T5WithFusion(nn.Module):
    def __init__(self, model_name="google/flan-t5-small", lexical_dim=512):
        super().__init__()
        self.t5 = T5ForConditionalGeneration.from_pretrained(model_name)
        self.proj = nn.Linear(lexical_dim, self.t5.config.d_model)

    def forward(self, input_ids=None, attention_mask=None, labels=None, lexical_embeds=None, **kwargs):
        inputs_embeds = self.t5.encoder.embed_tokens(input_ids)
        if lexical_embeds is not None:
            lexical_proj = self.proj(lexical_embeds.float()).to(inputs_embeds.device)
            inputs_embeds = inputs_embeds + lexical_proj.unsqueeze(1)
        return self.t5(input_ids=None, attention_mask=attention_mask, labels=labels, inputs_embeds=inputs_embeds, **kwargs)

    def prepare_inputs_for_generation(self, input_ids, attention_mask=None, **kwargs):
        inputs = self.t5.prepare_inputs_for_generation(input_ids, attention_mask=attention_mask, **kwargs)
        if "lexical_embeds" in kwargs:
            inputs["lexical_embeds"] = kwargs["lexical_embeds"]
        return inputs

    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.t5, name)


# ─────────────────────────────────────────────
# PREPROCESSING
# ─────────────────────────────────────────────
def extract_file_inputs(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()

    file_df = df[df["event_type"].str.strip().str.lower() == "file"].copy()

    def get_stem(row):
        # Priorité 1 : colonne 'file'
        if pd.notna(row.get("file")) and str(row["file"]).strip():
            return os.path.splitext(os.path.basename(str(row["file"]).strip()))[0]
        # Priorité 2 : parser la colonne 'raw' -> "nom.ext - App"
        raw = str(row.get("raw", ""))
        match = re.match(r"^(.+?)\s+-\s+.+$", raw.strip())
        if match:
            candidate = match.group(1).strip()
            if "." in candidate:
                return os.path.splitext(os.path.basename(candidate))[0]
        return None

    file_df["input_name"] = file_df.apply(get_stem, axis=1)
    file_df = file_df[file_df["input_name"].notna() & (file_df["input_name"] != "")]
    return file_df.reset_index(drop=True)


# ─────────────────────────────────────────────
# INFERENCE
# ─────────────────────────────────────────────
def batch_generate_descriptions(filenames, tokenizer, model, lex_model):
    descriptions = []

    for i in range(0, len(filenames), BATCH_SIZE):
        batch = filenames[i : i + BATCH_SIZE]

        prompts = [
            f"Given the following filename, generate a short description "
            f"of what the file is likely about.\n\nFilename: {name}\n\nDescription:"
            for name in batch
        ]

        inputs = tokenizer(prompts, return_tensors="pt", padding=True, truncation=True, max_length=128).to(DEVICE)

        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_new_tokens=60,
                num_beams=3,
            )

        descriptions.extend([tokenizer.decode(o, skip_special_tokens=True) for o in outputs])
        print(f"  [{i + len(batch)}/{len(filenames)}] done")

    return descriptions


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":

    print(f"[1/4] Lecture de {CSV_INPUT} ...")
    file_df = extract_file_inputs(CSV_INPUT)
    print(f"      {len(file_df)} fichiers trouvés : {file_df['input_name'].tolist()}")

    print(f"\n[2/4] Chargement du modèle depuis {MODEL_DIR} ...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = T5WithFusion(model_name="google/flan-t5-small", lexical_dim=LEXICAL_DIM)
    state_dict = torch.load(f"{MODEL_DIR}/pytorch_model.bin", map_location=DEVICE)
    model.load_state_dict(state_dict, strict=False)
    model.to(DEVICE).eval()
    lex_model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"      Device : {DEVICE}")

    print(f"\n[3/4] Génération des descriptions ...")
    file_df["description"] = batch_generate_descriptions(
        file_df["input_name"].tolist(), tokenizer, model, lex_model
    )

    print(f"\n[4/4] Sauvegarde dans {CSV_OUTPUT} ...")
    file_df.to_csv(CSV_OUTPUT, index=False)

    print("\n✅ Résultats :")
    print(file_df[["input_name", "description"]].to_string(index=False))