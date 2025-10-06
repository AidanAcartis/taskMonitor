import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def recherche_google(query):
    """Scrape les résultats Google en contournant les protections anti-bots."""
    
    # Lancer un navigateur Chrome furtif
    options = uc.ChromeOptions()
    options.headless = False  # Mettre True pour exécuter en arrière-plan
    driver = uc.Chrome(options=options)

    try:
        # Ouvrir Google
        driver.get("https://www.google.com")
        time.sleep(2)

        # Trouver la barre de recherche et taper la requête
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)

        # Récupérer les résultats
        results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")

        extracted_data = []
        for result in results[:5]:  # Prendre les 5 premiers résultats
            try:
                title = result.find_element(By.TAG_NAME, "h3").text
                link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                description = result.find_element(By.CSS_SELECTOR, ".VwiC3b").text
                extracted_data.append((title, link, description))
            except:
                continue

        return extracted_data
    
    finally:
        driver.quit()

# Exemple d'utilisation
if __name__ == "__main__":
    question = input("Que veux-tu rechercher ? ")
    resultats = recherche_google(question)
    
    print("\nRésultats Google :")
    for i, (title, link, desc) in enumerate(resultats, start=1):
        print(f"\n{i}. {title}\n   🔗 {link}\n   📝 {desc}")
