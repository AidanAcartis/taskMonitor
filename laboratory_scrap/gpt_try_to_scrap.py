import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

def scrap_chatgpt(question):
    """Automatise la récupération des réponses de ChatGPT sur le web"""
    
    # Lancer un navigateur Chrome furtif
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    
    try:
        # Ouvrir ChatGPT
        driver.get("https://chat.openai.com/")
        time.sleep(5)

        
        return response_text

    finally:
        driver.quit()

# Exemple d'utilisation : Pose directement la question sur Keima Katsuragi
question = "Keima Katsuragi"
reponse = scrap_chatgpt(question)

print("Réponse scrappée :")
print(reponse)
