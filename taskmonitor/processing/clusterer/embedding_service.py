"""
embedding_service.py
--------------------
Service dédié à la génération d'embeddings avec SentenceTransformer.
"""

from sentence_transformers import SentenceTransformer
from taskmonitor.core.config import CLUSTER_MODEL_DIR, DEVICE


class EmbeddingService:
    def __init__(self):
        """
        Initialise le modèle d'embeddings.
        """
        print(f"\n[3] Loading the model : {CLUSTER_MODEL_DIR} ...")

        self.model = SentenceTransformer(str(CLUSTER_MODEL_DIR), device=str(DEVICE))
        self.model.eval()

    def encode(self, tasks: list[str]):
        """
        Génère les embeddings normalisés des tâches.

        Args:
            tasks: liste de textes

        Returns:
            embeddings (tensor)
        """
        if not tasks:
            raise ValueError("The list of tasks is empty.")

        print("    Calculating embeddings ...")

        embeddings = self.model.encode(
            tasks,
            convert_to_tensor=True,
            normalize_embeddings=True
        )

        return embeddings