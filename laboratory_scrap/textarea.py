import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialiser le navigateur
options = Options()
options.add_argument("user-data-dir=/home/aidan/.config/google-chrome/")  # Répertoire parent du profil
options.add_argument("--no-sandbox")  # Pour éviter les erreurs liées au sandboxing sur certains systèmes

# Lancer Chrome avec ce profil
driver = webdriver.Chrome(options=options)

try:
    # Ouvrir la page cible
    driver.get("https://chatgpt.com/")
    
    # Attendre que l'élément <textarea> soit présent
    textarea = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.block.h-10.w-full.resize-none.border-0.bg-transparent.px-0.py-2.text-token-text-primary.placeholder\\:text-token-text-tertiary"))
    )
    print("✅ Textarea trouvé !")

    # Vérifier si l'élément est caché et le rendre visible
    driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';", textarea)

    # Attendre un peu pour voir si le changement prend effet
    time.sleep(1)

    # Tenter d'envoyer du texte
    textarea.send_keys("Mon texte ici")
    textarea.send_keys(Keys.ENTER)
    print("✅ Texte envoyé !")

except Exception as e:
    print("❌ Erreur générale :", e)

finally:
    driver.quit()  # Toujours fermer le navigateur
