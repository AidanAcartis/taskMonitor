"""
embedding_service.py
--------------------
Service dedicated to generating embeddings using SentenceTransformer.
"""

from sentence_transformers import SentenceTransformer
from taskmonitor.core.config import CLUSTER_MODEL_DIR, DEVICE


class EmbeddingService:
    def __init__(self):
        """
        Initializes the embeddings template.
        """
        print(f"\n[3] Loading the model : {CLUSTER_MODEL_DIR} ...")

        self.model = SentenceTransformer(str(CLUSTER_MODEL_DIR), device=str(DEVICE))
        self.model.eval()

    def encode(self, tasks: list[str]):
        """
        Generates the normalized embeddings for the tasks.

        Args:
            tasks: list of texts

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