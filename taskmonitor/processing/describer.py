# processing/describer.py

import os
import pandas as pd

# ───────────────── IMPORTS SERVICES ─────────────────
from services.description_builder import build_description
from services.context_extractor import extract_context_from_command
from services.file_description_service import FileDescriptionService

# ───────────────── CONFIG CENTRALISÉ ─────────────────
from core.config import NORMALIZED_EVENTS_FILE, DESCRIBED_EVENTS_FILE

# ───────────────── SCRIPT PRINCIPAL ─────────────────
def main():
    print("[1/4] Lecture CSV...")
    df = pd.read_csv(NORMALIZED_EVENTS_FILE).fillna("")
    df.columns = df.columns.str.strip().str.lower()

    # ── Collecte des fichiers pour IA
    print("[2/4] Collecte des noms de fichiers pour l'IA...")
    stems_to_process = set()

    # 1. Fichiers événements "file"
    for f in df[df.event_type.str.lower() == "file"]["file"]:
        if f:
            stems_to_process.add(os.path.splitext(os.path.basename(f))[0])

    # 2. Fichiers dans les commandes
    for cmd in df[df.event_type.str.lower() == "command"]["command"]:
        files, _ = extract_context_from_command(cmd)
        for f in files:
            stems_to_process.add(os.path.splitext(os.path.basename(f))[0])

    # ── Génération IA
    file_desc_map = {}

    if stems_to_process:
        stems_list = list(stems_to_process)

        print("[2.5/4] Chargement du service IA...")
        service = FileDescriptionService()
        service.load()

        print("[2.6/4] Génération des descriptions IA...")
        descriptions = service.generate_descriptions(stems_list)

        file_desc_map = dict(zip(stems_list, descriptions))

    # ── Construction descriptions finales
    print("[3/4] Construction de la colonne description...")
    df["description"] = df.apply(
        lambda r: build_description(r.to_dict(), file_desc_map),
        axis=1
    )

    # ── Sauvegarde
    df.to_csv(DESCRIBED_EVENTS_FILE, index=False)

    print(f"✅ Terminé ! {len(stems_to_process)} fichiers enrichis.")

# ── Permet d'exécuter directement ce script si besoin
if __name__ == "__main__":
    main()