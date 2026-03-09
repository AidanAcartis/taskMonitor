import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

files_list_path = "Files_list.txt"

# Charge the last row to know what is the last number
def get_last_number():
    try:
        with open(files_list_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return 0
            last_line = lines[-1].strip()
            if last_line:
                return int(last_line.split()[0])
    except FileNotFoundError:
        return 0
    return 0

#Prompt
def make_prompt(start_num):
    return f"""
    In `Files_list.txt`, which contains a numbered list of files in this format:"24 Titles.txt - all_script - Visual Studio Code". Each line follows the structure:<number> <filename> - <folder> - <application>. Generates exactly 35 new lines. Numbers must start at {start_num} and increment by 1. Filenames must be varied (extensions: .sh, .txt, .py, .log, .md, .json, .xml, .cfg....).. Create directories like: Collect_file, all_script, system_logs, utils, configs. with applications like: Visual Studio Code, Google Chrome, Notepad++, Sublime Text, PyCharm. No exact duplicates of lines already in `Files_list.txt`. Give me the 35 lines directly in the expected format, without explanation.
"""

#Init the browser
driver = uc.Chrome()

try:
    driver.get("https://chat.openai.com/")
    wait = WebDriverWait(driver, 60)

    print(">>> Veuillez vous connecter manuellement si nécessaire...")
    time.sleep(30)  # temps pour login manuel

    # Zone d'input
    text_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProseMirror")))

    # Charge the existed lines
    try:
        with open(files_list_path, "r", encoding="utf-8") as f:
            existing = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        existing = set()

    # Number of rounds (55) or until reaching 2000 lines
    for i in range(55):
        start_num = get_last_number() + 1
        prompt = make_prompt(start_num)

        #Send the prompt
        text_input.send_keys(prompt, Keys.ENTER)
        print(f"Prompt sended (batch {i+1}/55, start={start_num})")

        #Wait for the response
        time.sleep(25)

        messages = driver.find_elements(By.CSS_SELECTOR, "div.markdown")
        if not messages:
            print("Not founded messages")
            continue

        response = messages[-1].text.strip()
        new_lines = response.splitlines()

        appended = 0
        with open(files_list_path, "a", encoding="utf-8") as f:
            for l in new_lines:
                line = l.strip()
                if line and line not in existing:
                    f.write(line + "\n")
                    existing.add(line)
                    appended += 1

        print(f"{appended} new lines appended in Files.txt")

        #Wait for the next input
        time.sleep(10)

        #Verify if the completed 2000
        if len(existing) >= 2000:
            print("already 2000 lines")
            break

except Exception as e:
    print("Error :", e)

finally:
    driver.quit()
    print(" Browser closed!!")