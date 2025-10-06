import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

def scrap_chatgpt():
    """Automatise la récupération des réponses de ChatGPT sur le web"""

    # Lancer un navigateur Chrome furtif
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)

    try:
        # Ouvrir ChatGPT
        driver.get("https://chat.openai.com/")
        time.sleep(20)

        # Sélectionner le champ <textarea> en utilisant un sélecteur échappé
        textarea = driver.find_element(By.CSS_SELECTOR, "textarea.block.h-10.w-full.resize-none.border-0.bg-transparent.px-0.py-2.text-token-text-primary.placeholder\\:text-token-text-tertiary")

        if textarea:  # Vérifier si l'élément existe
            # Faire une action sur l'élément (par exemple, taper du texte)
            textarea.send_keys("Bonjour Selenium !")

    finally:
        driver.quit()

# Appeler la fonction sans paramètre
scrap_chatgpt()
