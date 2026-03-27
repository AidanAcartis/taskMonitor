import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

input_file  = "activity_data.jsonl"
output_file = "activity_data_corrected.jsonl"  # on ajoute à la suite

MISSING_IDS = {"0", "10", "12", "14", "15", "17", "18", "20", "21", "24",
               "27", "36", "45", "51", "58", "98", "119", "120", "140", "160", "162"}

prompt_template = """Tu es un expert en analyse d'activité utilisateur sur Linux.Voici un exemple de dataset existant :{cluster}. Corrige cet exemple en suivant ces règles STRICTES : RÈGLE 1 — task_items : chaque item doit décrire UNIQUEMENT ce qu'est l'outil/fichier/commande, sans révéler l'intention :- Fichier : "nom.ext, type, /chemin, opened with App, [description neutre du contenu]"- Commande : "commande, command, executed in terminal, [rôle/fonction technique de la commande]"- Application : "App, application, [rôle/fonction technique de l'application]". Exemples CORRECTS de task_items :- "nginx.conf, configuration file, /etc/nginx, opened with nano, stores web server directives and virtual host settings"- "sudo apt update, command, executed in terminal, refreshes the local package index from remote repositories"- "git push, command, executed in terminal, uploads local branch commits to a remote repository"- "Postman, application, sends HTTP requests and displays server responses for API testing"- "data_file.txt, text file, /data, opened with VS Code, contains tabular records of collected activity events". Exemples INCORRECTS (révèlent l'intention) :- "nginx.conf opened with nano to configure web server" ❌- "sudo apt update command used to update packages before installing brave" ❌. RÈGLE 2 — global_task_intention : UNE phrase courte qui décrit l'intention globale abstraite de l'utilisateur.- Doit être une vraie abstraction, PAS une copie d'un task_item- Commence par un verbe d'action : "Install", "Configure", "Debug", "Manage", "Monitor"... Exemples CORRECTS de global_task_intention :- "Install and configure Brave browser from official APT repository"- "Debug Xorg display driver errors from system logs"- "Version and synchronize project source code with remote git repository"- "Edit and inspect system network configuration files". Exemples INCORRECTS :- "Push local commits to a remote repository" ❌ (copie d'un task_item)- "Use git push command" ❌ (trop littéral). Réponds UNIQUEMENT avec un objet JSON valide. Aucune introduction. Format :{{"id": "{entry_id}",  "task_items": ["...", "...", "..."],  "global_task_intention": "..."}}"""

# ── Charger les entrées manquantes depuis le fichier source ──────────────────
missing_entries = {}
with open(input_file, "r", encoding="utf-8") as f:
    for line_idx, line in enumerate(f):
        if not line.strip():
            continue
        entry    = json.loads(line)
        entry_id = str(entry.get("id", line_idx))
        if entry_id in MISSING_IDS:
            missing_entries[entry_id] = entry

# Trier par ID numérique croissant
sorted_entries = sorted(missing_entries.items(), key=lambda x: int(x[0]))
print(f">>> {len(sorted_entries)} entrées manquantes trouvées : {[e[0] for e in sorted_entries]}")

# ── Scraping ─────────────────────────────────────────────────────────────────
driver = uc.Chrome(version_main=145)
wait   = WebDriverWait(driver, 80)

try:
    driver.get("https://chat.openai.com/")
    print(">>> Connectez-vous si nécessaire...")
    time.sleep(30)

    text_input = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProseMirror"))
    )

    # Ouvrir en mode append pour ajouter à la suite du fichier existant
    with open(output_file, "a", encoding="utf-8") as f_out:

        for entry_id, original_entry in sorted_entries:
            cluster = json.dumps(original_entry, ensure_ascii=False)
            prompt  = prompt_template.format(cluster=cluster, entry_id=entry_id)

            text_input.send_keys(prompt)
            text_input.send_keys(Keys.ENTER)
            print(f">>> Prompt envoyé pour l'id {entry_id}")

            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.markdown"))
            )

            messages = driver.find_elements(By.CSS_SELECTOR, "div.markdown")
            if not messages:
                print(f">>> Pas de réponse pour {entry_id}")
                continue

            response_text = messages[-1].text.strip()
            response_text = response_text.replace("\n", " ").replace("\r", " ")

            entry_to_write = {
                "original_id": entry_id,
                "raw_response": response_text
            }
            f_out.write(json.dumps(entry_to_write, ensure_ascii=False) + "\n")
            print(f">>> Sauvegardé id {entry_id} (brut)")

            time.sleep(40)

    print(f"\n✅ Terminé — {len(sorted_entries)} entrées manquantes traitées.")

except Exception as e:
    print("Erreur:", e)

finally:
    driver.quit()
    print(">>> Browser fermé")