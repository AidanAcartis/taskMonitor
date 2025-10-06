import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Initialisation du navigateur
driver = webdriver.Chrome()

try:
    # Ouvrir la page
    driver.get("https://chat.openai.com/")
    time.sleep(5)  # Attendre que la page charge

    try:
        # Sélectionner le vrai champ de saisie
        text_input = driver.find_element(By.CSS_SELECTOR, "div.ProseMirror")
        print("✅ Zone de texte trouvée !")
    except Exception as e:
        print("❌ Zone de texte introuvable :", e)
        driver.quit()
        exit()

    # Envoyer du texte dans la vraie zone de saisie
    text_input.send_keys("Monkey D. Luffy")
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
        exit()

    # Attendre 40 secondes avant de fermer le navigateur
    print("⏳ Attente de 40 secondes avant fermeture...")
    time.sleep(40)

except Exception as e:
    print("❌ Erreur :", e)

finally:
    driver.quit()  # Toujours fermer le navigateur
    print("🚪 Navigateur fermé.")
