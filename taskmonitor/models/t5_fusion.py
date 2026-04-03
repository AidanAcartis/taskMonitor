import torch
import torch.nn as nn
from transformers import AutoTokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer
from typing import List

from core.config import GEN_DESC_MODEL_DIR, DEVICE, BATCH_SIZE, LEXICAL_DIM, INFERENCE_CONFIG

# ───────────────── MODEL ─────────────────

class T5WithFusion(nn.Module):
    def __init__(self, model_name="google/flan-t5-small", lexical_dim=512):
        super().__init__()
        self.t5 = T5ForConditionalGeneration.from_pretrained(model_name)
        self.proj = nn.Linear(lexical_dim, self.t5.config.d_model)

    def forward(self, input_ids=None, attention_mask=None, labels=None,
                lexical_embeds=None, **kwargs):
        inputs_embeds = self.t5.encoder.embed_tokens(input_ids)

        if lexical_embeds is not None:
            lexical_proj = self.proj(lexical_embeds.float()).to(inputs_embeds.device)
            inputs_embeds = inputs_embeds + lexical_proj.unsqueeze(1)

        return self.t5(
            input_ids=None,
            attention_mask=attention_mask,
            labels=labels,
            inputs_embeds=inputs_embeds,
            **kwargs
        )

    def prepare_inputs_for_generation(self, input_ids, attention_mask=None, **kwargs):
        inputs = self.t5.prepare_inputs_for_generation(
            input_ids,
            attention_mask=attention_mask,
            **kwargs
        )

        if "lexical_embeds" in kwargs:
            inputs["lexical_embeds"] = kwargs["lexical_embeds"]

        return inputs

    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.t5, name)


# ───────────────── SERVICE POO ─────────────────

class T5FusionService:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.lex_model = None

    def load(self):
        """Charge tous les modèles nécessaires"""
        print(f"[T5] Chargement depuis {GEN_DESC_MODEL_DIR}")

        self.tokenizer = AutoTokenizer.from_pretrained(GEN_DESC_MODEL_DIR)

        self.model = T5WithFusion(
            model_name="google/flan-t5-small",
            lexical_dim=LEXICAL_DIM
        )

        state = torch.load(
            GEN_DESC_MODEL_DIR / "pytorch_model.bin",
            map_location=DEVICE
        )

        self.model.load_state_dict(state, strict=False)
        self.model.to(DEVICE).eval()

        self.lex_model = SentenceTransformer("all-MiniLM-L6-v2")

        print(f"[T5] Device : {DEVICE}")
