import pychrome
import time
import traceback

try:
    # Créer une instance du navigateur
    browser = pychrome.Browser(url="http://localhost:9222")  # Assurez-vous que Chrome/Chromium est lancé avec l'option remote-debugging-port=9222

    # Démarrer une nouvelle session
    tab = browser.new_tab()

    # Ouvrir une page web
    tab.start()
    tab.Page.navigate(url="https://chat.openai.com/")  # Remplacez par l'URL que vous souhaitez tester

    # Attendez que la page se charge (par polling)
    while True:
        # Vérifie si la page est entièrement chargée
        result = tab.Runtime.evaluate(expression="document.readyState")
        if result["result"]["value"] == "complete":
            break
        time.sleep(1)

    # Prendre une capture d'écran
    screenshot = tab.Page.captureScreenshot(format="png", result=True)

    # Vérifiez si la capture a bien fonctionné
    if screenshot.get("data"):
        with open("screenshot.png", "wb") as f:
            f.write(screenshot["data"].encode("utf-8"))
        print("Capture d'écran prise et sauvegardée sous 'screenshot.png'.")
    else:
        print("Erreur lors de la capture d'écran.")

    # Fermer la session
    tab.stop()

except Exception as e:
    print("Une erreur est survenue lors de l'exécution du script.")
    traceback.print_exc()
