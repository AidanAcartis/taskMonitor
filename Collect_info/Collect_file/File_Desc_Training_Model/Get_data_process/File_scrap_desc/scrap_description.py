import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

input_file = "../Get_Files/Files_list.jsonl"
output_file = "response.jsonl"

prompt_template = """
Describe the following file in 2 sentences maximum. Include: what it is according to the extension ({ext}), what he does according to his name ({fname}), where it is located ({directory}), which application opens it ({app})
"""

# -------------------------
# Utiliser mon profil Chrome pour garder la session
# -------------------------
# options = uc.ChromeOptions()
# options.add_argument(r"--user-data-dir=/home/ton_user/.config/google-chrome")  # Change selon ton OS
# options.add_argument(r"--profile-directory=Default")  # ou "Profile 1" si nécessaire

# driver = uc.Chrome(options=options)

#Init the browser
driver = uc.Chrome()
# driver.execute_script("window.open('');")
# driver.switch_to.window(driver.window_handles[-1])
try:
    driver.get("https://chat.openai.com/")
    wait = WebDriverWait(driver, 60)

    print(">>> Veuillez vous connecter manuellement si nécessaire...")
    time.sleep(30)  # temps pour login manuel, tu peux augmenter si besoin

    # Input zone 
    text_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProseMirror")))
    print("Print the output")

    with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "a", encoding="utf-8") as f_out:
        for line in f_in:
            entry = json.loads(line.strip())

            #Remove this after
            # -----------------------------
            # Ignorer les entrées déjà traitées
            # -----------------------------
            if int(entry["id"]) < 1725:
                continue

            fname = entry["filename"]
            ext = entry["extension"]
            directory = entry["directory"]
            app = entry["application"]

            # Build the prompt
            prompt = prompt_template.format(ext=ext, fname=fname, directory=directory, app=app)

            #Send to chatGPT
            text_input.send_keys(prompt, Keys.ENTER)
            print(f"Prompt sended to {fname}")

            #Wait for the response
            time.sleep(25)

            messages = driver.find_elements(By.CSS_SELECTOR, "div.markdown")
            if messages:
                response = messages[-1].text.strip()
                entry["description"] = response
                f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                print(f"response received for {fname}")
            else:
                print(f"No response for {fname}")

            # Little pause before the next sending
            time.sleep(5)

except Exception as e:
    print("Error :", e)

finally:
    driver.quit()
    print("Browser closed!!")