import torch
from typing import List
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer

from taskmonitor.models.t5_fusion import T5WithFusion # modèle pur
from taskmonitor.core.config import GEN_DESC_MODEL_DIR, DEVICE, BATCH_SIZE, LEXICAL_DIM, INFERENCE_CONFIG

# ─────────────────── SERVICE DE DESCRIPTION DES FICHIERS ───────────────────

class FileDescriptionService:
    """
    Service POO dédié à la génération de descriptions pour des fichiers via T5 + embeddings lexicaux.
    """

    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.lex_model = None

    def load(self):
        """Charge le tokenizer, le modèle et le modèle lexical."""
        print(f"[FileDesc] Loading from {GEN_DESC_MODEL_DIR} ...")
        self.tokenizer = AutoTokenizer.from_pretrained(GEN_DESC_MODEL_DIR)

        self.model = T5WithFusion(
            model_name="google/flan-t5-small",
            lexical_dim=LEXICAL_DIM
        )

        state = torch.load(GEN_DESC_MODEL_DIR / "pytorch_model.bin", map_location=DEVICE)
        self.model.load_state_dict(state, strict=False)
        self.model.to(DEVICE).eval()

        self.lex_model = SentenceTransformer("all-MiniLM-L6-v2")
        print(f"[FileDesc] Device : {DEVICE}")

    def generate_descriptions(self, filenames: List[str]) -> List[str]:
        """
        Génère les descriptions IA pour une liste de fichiers.
        Chaque fichier est traité par batch.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        descriptions = []

        for i in range(0, len(filenames), BATCH_SIZE):
            batch = filenames[i: i + BATCH_SIZE]

            prompts = [
                f"Describe the specific purpose of the following file.\n\nFilename: {name}\n\nDescription:"
                for name in batch
            ]

            inputs = self.tokenizer(
                prompts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=128
            ).to(DEVICE)

            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    **INFERENCE_CONFIG
                )

            decoded = [self.tokenizer.decode(o, skip_special_tokens=True) for o in outputs]
            descriptions.extend(decoded)

            print(f"[FileDesc] {i + len(batch)}/{len(filenames)} processed files")

        return descriptions