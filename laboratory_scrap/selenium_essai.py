import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def scrap_chatgpt(question):
    """Automatise la récupération des réponses de ChatGPT sur le web"""

    # Lancer un navigateur Chrome furtif
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)

    try:
        # Ouvrir ChatGPT
        driver.get("https://chat.openai.com/")
        time.sleep(450000)  # Attendre un peu que la page se charge

        # # Ouvrir la console de développement (Ctrl + Shift + I)
        # driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.SHIFT + 'i')
        # time.sleep(30)  # Rester dans la console pendant 30 secondes
        
        # # Attendre encore un peu si nécessaire (ajuster si besoin)
        # time.sleep(30)  # 30 secondes de plus pour observer la console ou effectuer d'autres actions
        
        # # Vous pouvez également ajouter ici d'autres actions que vous voulez faire sur la page

    finally:
        driver.quit()

# Exemple d'utilisation
question = "Keima Katsuragi"
scrap_chatgpt(question)
