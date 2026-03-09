import subprocess 
import time
import csv
from tabulate import tabulate 
import re

MODEL = "phi"

def generate_description_ollama(name, type_):
    # If the type is "file-directory-App"
    if type_ == "file-directory-App":
        # Case: file with structure name - folder - application
        if " - " in name and name.count(" - ") == 2:
            parts = name.split(" - ")
            if len(parts) == 3:
                filename, directory, app = parts
                prompt = f"""
Based on the file name, guess what this file '{filename}' does by turning the filename into sentence. Also mention that it is located in the folder '{directory}' and was opened with the application {app}. Maximum three sentences. No explanation, and avoid 'I', 'you', 'your', 'my'.
"""
            else:
                prompt = f"Briefly describe '{name}' by turning the name you get into sentence in two sentences. No explanation, and avoid 'I', 'you', 'your', 'my'."
        # Case: just a word => a folder
        elif re.match(r"^\w+$", name):
            prompt = f"The user worked inside the folder named {name}. One sentence only.No explanation, and avoid 'I', 'you', 'your', 'my'."
        # Case: just a word => a folder"
        # Generic case
        else:
            prompt = f"Briefly describe the file or folder '{name}' by turning the name into sentence, in a maximum of two sentences. No explanation. Avoid 'I', 'you', etc."

    # If it is a command
    elif type_.lower() in ["commande", "command"]:
        prompt = f"""
Give a description (maximum two sentences) of the following shell command:
{name}

No explanation. No use of 'I', 'you', etc. Just describe what it does.
"""

    # Default case
    else:
        prompt = f"Briefly describe: {name} in a maximum of two sentences. No explanation."

    # Ollama call
    result = subprocess.run(
        ["ollama", "run", MODEL],
        input=prompt.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return result.stdout.decode().strip()

# Total timer
total_start = time.time()

# Read the file data_collect.txt
with open("data_collect.txt", "r", encoding="utf-8") as f:
    lines = [line.strip().split("\t") for line in f if line.strip()]

# Prepare CSV
with open("data.csv", "w", newline='', encoding="utf-8") as f_out:
    writer = csv.writer(f_out, delimiter=';')
    writer.writerow(["date", "heure_ouverture", "heure_fermeture", "duration", "type", "name", "description"])

    for i, line in enumerate(lines, 1):
        if len(line) < 6:
            continue
        date, heure_ouverture, heure_fermeture, duration, type_, name = line
        print(f"\n >> {i}. Generate description for : {name} [{type_}]")

        start = time.time()
        description = generate_description_ollama(name, type_)
        elapsed = time.time() - start

        # Terminal display
        print(tabulate([[name, description]], headers=["Name", "Description"], tablefmt="grid"))

        print(f"⏱ Response time : {elapsed:.2f} seconds")

        writer.writerow([date, heure_ouverture, heure_fermeture, duration, type_, name, description])

# Total time
total_duration = time.time() - total_start
print(f"\n  Total time for {len(lines)} lines: {total_duration:.2f} seconds")
