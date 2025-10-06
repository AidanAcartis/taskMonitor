import subprocess
import time
import csv
from tabulate import tabulate  # pip install tabulate

MODEL = "phi"

def generate_description_ollama(text):
    prompt = (
        f"I need you to guess what is this, guess what it does, just the function and the subject on which it is needed but no more example or explanation. "
        f"(I need a little description from your deduction in some sentences(not too long). Don't give any explanation just description and avoid those words: I, my, you, your) : '{text}'"
    )

    result = subprocess.run(
        ["ollama", "run", MODEL],
        input=prompt.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return result.stdout.decode().strip()

# Chronomètre total
total_start = time.time()

# Lecture de data_collect.txt
with open("data_collect.txt", "r", encoding="utf-8") as f:
    lignes = [line.strip().split("\t") for line in f if line.strip()]

# Préparation CSV
with open("data.csv", "w", newline="", encoding="utf-8") as f_out:
    writer = csv.writer(f_out, delimiter=';')
    writer.writerow(["date", "heure_ouverture", "heure_fermeture", "duration", "type", "name", "description"])

    for i, ligne in enumerate(lignes, 1):
        if len(ligne) < 6:
            continue

        date, heure_ouverture, heure_fermeture, duration, type_, name = ligne
        print(f"\n>> {i}. Génération de description pour : {name}")

        start = time.time()
        description = generate_description_ollama(name)
        elapsed = time.time() - start

        # Affichage lisible dans le terminal
        print(tabulate([[date, heure_ouverture, heure_fermeture, duration, type_, name, description]],
                       headers=["Date", "Heure Ouverture", "Heure Fermeture", "Durée", "Type", "Nom", "Description"],
                       tablefmt="grid"))

        print(f"⏱ Temps de réponse : {elapsed:.2f} secondes")

        writer.writerow([date, heure_ouverture, heure_fermeture, duration, type_, name, description])

# Temps total
total_duration = time.time() - total_start
print(f"\n✅ Temps total pour {len(lignes)} lignes : {total_duration:.2f} secondes")
