import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -------------------------
# Fichiers d'entrée et sortie
# -------------------------
input_file = "input.txt"  # fichier .txt avec une global_task par ligne
output_file = "task_items_responses.jsonl"

# -------------------------
# Prompt template
# -------------------------
prompt_template = """
I will give you a sentence that describes a global task.Your mission: generate a list of "task_items" that correspond exactly to this task.  Rules:  - Each "task_item" should be a short sentence describing a file, an application, a website, or a command used to accomplish this task.  - For a file, include: name, extension/type, directory if relevant, application used to open it, and a concise description of what it does.  - For an application, include: name and usage.  - For a website, include: name, directory if relevant, application used to open it, and usage.  - For a command, include only a concise description, without the prefix "Command".  - The list of "task_items" should be varied, but it must include at least 3 files and 3 commands. It can also include applications and websites if relevant.  - Output only the task_items: no explanations, no JSON wrapper, no extra text. Each sentence should be enclosed in quotes and separated by commas, like this:"task_item 1","task_item 2","...","task_item N"Here is the global task to process:  "{global_task_description}"
"""

# -------------------------
# Initialisation du driver
# -------------------------
# driver = uc.Chrome()
driver = uc.Chrome(version_main=140)
wait = WebDriverWait(driver, 60)

try:
    driver.get("https://chat.openai.com/")
    print(">>> Veuillez vous connecter manuellement si nécessaire...")
    time.sleep(30)  # temps pour login manuel

    text_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProseMirror")))

    with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "a", encoding="utf-8") as f_out:
        for idx, line in enumerate(f_in):
            global_task = line.strip()
            if not global_task:
                continue

            prompt = prompt_template.format(global_task_description=global_task)

            # Envoyer le prompt à ChatGPT
            text_input.send_keys(prompt, Keys.ENTER)
            print(f">>> Prompt sent for task {idx}: {global_task}")

            # Attente pour la réponse (ajuster selon vitesse)
            time.sleep(25)

            # Récupération de la dernière réponse
            messages = driver.find_elements(By.CSS_SELECTOR, "div.markdown")
            if messages:
                response_text = messages[-1].text.strip()
                # 1️Supprimer les guillemets superflus au début/fin
                if response_text.startswith('"') and response_text.endswith('"'):
                    response_text = response_text[1:-1]

                # 2 Supprimer les \n superflus à l'intérieur
                response_text = response_text.replace("\n", " ").replace("\r", " ")

                # 3 Séparer les task_items en fonction des ","
                raw_items = response_text.split('","')

                # Nettoyage de chaque item
                task_items_clean = []
                for item in raw_items:
                    item = item.strip()
                    # Supprimer guillemets résiduels
                    item = item.strip('"')
                    item = item.strip().strip('"')
                    item = item.replace("\n", " ").replace("\r", " ")
                
                    # Normaliser les espaces multiples
                    item = ' '.join(item.split())
                    task_items_clean.append(item)

                # Construire l'entrée JSONL
                entry = {
                    "id": str(idx),
                    "task_items": [item.strip() for item in response_text.split('",') if item.strip()],
                    "global_task_description": global_task
                }
                f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                print(f">>> Response saved for task {idx}")
            else:
                print(f">>> No response for task {idx}")

            time.sleep(5)  # petite pause avant le suivant

except Exception as e:
    print("Error:", e)

finally:
    driver.quit()
    print(">>> Browser closed")
