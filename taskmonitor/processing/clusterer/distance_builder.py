"""
distance_builder.py
-------------------
Construit la matrice de distance à partir des embeddings.
"""

import numpy as np
from sentence_transformers import util


class DistanceBuilder:
    def __init__(self):
        pass

    def build(self, embeddings):
        """
        Construit la matrice de distance cosinus.

        Args:
            embeddings: tensor (n_samples, dim)

        Returns:
            dist_matrix: ndarray (n_samples, n_samples)
        """

        if embeddings is None:
            raise ValueError("Embeddings non fournis.")

        print("\n[4] Calcul de la matrice de distance ...")

        # Similarité cosinus
        sim_matrix = util.cos_sim(embeddings, embeddings).cpu().numpy()

        # Distance = 1 - similarité
        dist_matrix = 1 - sim_matrix

        # Sécurité numérique (évite valeurs négatives)
        dist_matrix = np.clip(dist_matrix, 0, None)

        return dist_matrix