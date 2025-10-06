import numpy as np
import torch
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt

sims_lexical = []
examples_to_show = []

# Pour chaque split
for split in ["train", "validation", "test"]:
    print(f"\nChecking {split} set ....")
    dataset_split = tokenized_datasets[split]  # tokenized_datasets contient lexical_embeds

    for i, ex in enumerate(tqdm(dataset_split, total=len(dataset_split))):
        # Récupérer le filename depuis le prompt décodé
        decoded_prompt = tokenizer.decode(ex["input_ids"], skip_special_tokens=True)
        try:
            filename_text = decoded_prompt.split("Filename:")[1].split("Description:")[0].strip()
        except:
            continue

        # --- Recalcul de l'embedding projeté ---
        recalc_embed = lex_model.encode(filename_text)  # shape = 384
        recalc_proj = proj_layer(torch.tensor(recalc_embed).float()).detach().numpy()  # shape = 512

        # --- Similarité cosinus ---
        stored_embed = np.array(ex["lexical_embeds"])
        sim = cosine_similarity(recalc_proj.reshape(1, -1), stored_embed.reshape(1, -1))[0][0]
        sims_lexical.append(sim)

        # Stocker quelques exemples pour inspection
        if i < 5:
            examples_to_show.append({
                "filename": filename_text,
                "similarity": sim,
                "stored_embed_sample": stored_embed[:10],
                "recalc_proj_sample": recalc_proj[:10]
            })

# --- Statistiques globales ---
print("\n📊 Global statistics:")
print(f"Mean similarity: {np.mean(sims_lexical):.4f}")
print(f"Min similarity: {np.min(sims_lexical):.4f}")
print(f"Max similarity: {np.max(sims_lexical):.4f}")

# --- Histogramme ---
plt.figure(figsize=(8,5))
plt.hist(sims_lexical, bins=50, color="skyblue", edgecolor="black", alpha=0.7)
plt.axvline(np.mean(sims_lexical), color="red", linestyle="--", label=f"Mean = {np.mean(sims_lexical):.4f}")
plt.title("Cosine similarity: stored lexical_embeds vs recalculated embeddings")
plt.xlabel("Cosine similarity")
plt.ylabel("Count")
plt.legend()
plt.show()

# --- Quelques exemples vérifiés ---
print("\n🔍 Quelques exemples vérifiés manuellement :")
for ex in examples_to_show:
    print(f"\nFilename: {ex['filename']}")
    print(f" → Similarity: {ex['similarity']:.4f}")
    print(f" → Stored_embed[:10]: {ex['stored_embed_sample']}")
    print(f" → Recalc_proj[:10]: {ex['recalc_proj_sample']}")
