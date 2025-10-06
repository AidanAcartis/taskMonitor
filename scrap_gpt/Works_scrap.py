import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialisation du navigateur
driver = uc.Chrome()

try:
    # Ouvrir la page
    driver.get("https://chat.openai.com/")
    time.sleep(5)  # Attendre que la page charge

    # Attendre la zone de saisie
    wait = WebDriverWait(driver, 15)
    text_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProseMirror")))

    print("✅ Zone de texte trouvée !")

    # Envoyer du texte et appuyer sur Entrée
    text_input.send_keys("Tu vas jouer un rôle maintenant. Tu es un chatbot dans un plateforme de service de vente pizza, recommadation pizza(bref tous les services qui tourne autour),qui répond avec satisfaction à la demande de l'utilisateur selon sa demande, les informations qu'il veut. Donner ta réponse en format json avec le petit message que tu donne dabord + les informations parce que je dois traiter dabord les réponses json avant de les envoyer au front(finish with the word voila mon ami when you finished)", Keys.ENTER)
    print("📝 Message envoyé !")

    # Attendre la réponse de ChatGPT
    time.sleep(60)

    # Vérifier si une réponse apparaît
    messages = driver.find_elements(By.CSS_SELECTOR, "div.markdown")
    if messages:
        print("✅ Réponse trouvée :", messages[-1].text)
    else:
        print("❌ Aucune réponse reçue.")

except Exception as e:
    print("❌ Erreur :", e)

finally:
    driver.quit()
    print("🚪 Navigateur fermé.")
