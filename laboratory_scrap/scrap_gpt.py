import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration de Chrome pour Selenium
options = Options()
options.add_argument("window-size=1200x600")
driver = webdriver.Chrome(options=options)

def scrap_chatgpt():
    """Automatise la récupération des réponses de ChatGPT sur le web"""

    try:
        # Ouvrir ChatGPT
        driver.get("https://chat.openai.com/")
        time.sleep(5)  # Attendre que la page se charge

        try:
            # Sélectionner le champ <textarea>
            textarea = driver.find_element(By.CSS_SELECTOR, "textarea.block.h-10.w-full.resize-none.border-0.bg-transparent.px-0.py-2.text-token-text-primary.placeholder\\:text-token-text-tertiary")
            print("✅ Textarea trouvé !")
        except Exception as e:
            print("❌ Textarea non trouvé :", e)
            driver.quit()
            exit()

        # Vérifier si l'élément est caché et le rendre visible
        driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';", textarea)

        # Attendre un peu pour voir si le changement prend effet
        time.sleep(1)

        # Tenter d'envoyer du texte
        textarea.send_keys("Mon texte ici")
        textarea.send_keys(Keys.ENTER)
        print("✅ Texte envoyé !")
        # Attendre environ 10 secondes avant de rechercher le bouton
        time.sleep(10)
        print("Attente terminée, recherche du bouton...")

        try:
            # Sélectionner le bouton "Send" par son data-testid
            button = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="send-button"]')
            print("✅ Bouton trouvé ! Clic en cours...")
            button.click()  # Cliquer sur le bouton "Send"
        except Exception as e:
            print("❌ Bouton non trouvé :", e)
            driver.quit()
            return

        # Observer les mutations du DOM et attendre que la div de réponse apparaisse
        try:
            element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.markdown.prose.w-full.break-words.dark\\:prose-invert.dark'))
            )
            content = element.get_attribute("innerHTML")
            print("✅ Contenu extrait :", content)
        except Exception as e:
            print("❌ Erreur lors de la récupération du contenu :", e)
            driver.quit()
            return

        # Sauvegarder le contenu dans un fichier texte
        with open("last_div_content.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Fichier téléchargé : last_div_content.txt")

    finally:
        driver.quit()

scrap_chatgpt()
