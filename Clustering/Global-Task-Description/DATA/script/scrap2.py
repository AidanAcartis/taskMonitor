import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

input_file = "activity_data_resolve.jsonl"
output_file = "activity_data_augmented2.jsonl"

prompt_template = """Pour chaque cluster de subtasks créer :- Version originale- 2 paraphrases automatiques- 1 version avec outil remplacé- 1 version avec mot clé supprimé.Voici le cluster :{cluster}. Donner uniquement les nouvelles structures en format JSON valide(faites tres attention aux erreurs json et jsonl). Aucune phrase d'introduction. Répondre directement avec un objet JSON structuré.La réponse doit être dans ce format :(id: ,  task_items_versions: [ (version_type: original,      task_items: [ ... ]    ),    () version_type: paraphrase_1,      task_items: [ ... ]    ),    (     version_type: paraphrase_2,      task_items: [ ... ]    ), (     version_type: tool_replaced,      task_items: [ ... ]    ),    (      version_type: keyword_removed,      task_items: [ ... ]    )  ])"""

driver = uc.Chrome(version_main=145)
wait = WebDriverWait(driver, 80)

try:
    driver.get("https://chat.openai.com/")
    print(">>> Connectez-vous si nécessaire...")
    time.sleep(30)

    text_input = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProseMirror"))
    )

    with open(input_file, "r", encoding="utf-8") as f_in, \
         open(output_file, "w", encoding="utf-8") as f_out:

        for line_idx, line in enumerate(f_in):
            if not line.strip():
                continue

            if line_idx < 161:
                continue

            idx = line_idx  
            original_entry = json.loads(line)
            cluster = json.dumps(original_entry, ensure_ascii=False)

            prompt = prompt_template.format(cluster=cluster)

            text_input.send_keys(prompt)
            text_input.send_keys(Keys.ENTER)

            print(f">>> Prompt envoyé pour le cluster {idx}")

            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.markdown"))
            )

            messages = driver.find_elements(By.CSS_SELECTOR, "div.markdown")

            if not messages:
                print(f">>> Pas de réponse pour {idx}")
                continue

            response_text = messages[-1].text.strip()

            response_text = response_text.replace("\n", " ").replace("\r", " ")

            entry_to_write = {
                "original_id": original_entry.get("id", str(idx)),
                "raw_response": response_text
            }
            f_out.write(json.dumps(entry_to_write, ensure_ascii=False) + "\n")
            print(f">>> Sauvegardé cluster {idx} (brut)")

            time.sleep(40)

except Exception as e:
    print("Erreur:", e)

finally:
    driver.quit()
    print(">>> Browser fermé")