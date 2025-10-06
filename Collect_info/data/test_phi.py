import subprocess
import time

# Choisis ton modèle local : mistral, phi, llama3, etc.
MODEL = "phi"

def generate_description_ollama(text):
    prompt = f"I need you to guess what is this, guess what it does, just the function and the subject on which it is needed but no more example or explanation.(I need a little description from your deduction in some sentences(not too long). Don't give any explanation just description and avoid those words: I, my, you, your) : '{text}'"
    
    result = subprocess.run(
        ["ollama", "run", MODEL],
        input=prompt.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return result.stdout.decode()

# Lecture des lignes
with open("descriptions.txt", "r") as f:
    lignes = [line.strip() for line in f if line.strip()]

# Chrono total
total_start = time.time()

# Génération et affichage
for i, ligne in enumerate(lignes, 1):
    print(f"\n>> {i}. {ligne}")

    start = time.time()
    response = generate_description_ollama(ligne)
    duration = time.time() - start

    print(response.strip())
    print(f"⏱ Temps de réponse : {duration:.2f} secondes")

# Temps total
total_duration = time.time() - total_start
print(f"\n✅ Temps total pour {len(lignes)} lignes : {total_duration:.2f} secondes")
