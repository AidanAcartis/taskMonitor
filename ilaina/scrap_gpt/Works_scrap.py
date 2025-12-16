import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Je commence par initialiser le navigateur Chrome
driver = uc.Chrome()

try:
    # J'ouvre la page de ChatGPT
    driver.get("https://chat.openai.com/")
    time.sleep(5)  # Je laisse le temps à la page de se charger complètement

    # J'attends que la zone de saisie soit disponible
    wait = WebDriverWait(driver, 15)
    text_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProseMirror")))

    print("Zone de texte trouvée !")

    # J'envoie le texte à ChatGPT et je simule la touche Entrée
    text_input.send_keys(
        "Tu vas jouer un rôle maintenant. Tu es un chatbot dans une plateforme de service de vente de pizza, tu donnes des recommandations et fournis tous les services autour de la pizza. Tu dois répondre avec satisfaction selon la demande de l'utilisateur. Donne ta réponse au format JSON avec d'abord le petit message que tu donnes et ensuite les informations, car je dois traiter les réponses JSON avant de les envoyer au front. Termine avec la phrase 'voila mon ami' lorsque tu as fini.",
        Keys.ENTER
    )
    print("Message envoyé !")

    # Je laisse le temps à ChatGPT de générer sa réponse
    time.sleep(60)

    # Je vérifie si une réponse est apparue
    messages = driver.find_elements(By.CSS_SELECTOR, "div.markdown")
    if messages:
        print("Réponse trouvée :", messages[-1].text)
    else:
        print("Aucune réponse reçue.")

except Exception as e:
    print("Erreur :", e)

finally:
    # Je ferme le navigateur pour libérer les ressources
    driver.quit()
    print("Navigateur fermé.")
