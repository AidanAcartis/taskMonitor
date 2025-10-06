Cloudflare utilise plusieurs techniques pour bloquer les bots et les scripts automatisés. Voici quelques méthodes pour contourner cette protection et interagir avec la page via Selenium :  

---

### ✅ **Solutions possibles :**

#### 1️⃣ **Utiliser un navigateur avec un profil utilisateur réel**
Cloudflare détecte souvent Selenium par la signature du navigateur. Tu peux utiliser un profil Chrome existant pour tromper le système.

```python
from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument("user-data-dir=/chemin/vers/profil/chrome")  # Remplace par ton chemin réel

driver = webdriver.Chrome(options=options)
driver.get("https://www.site.com/")
```
📌 **Trouver le chemin du profil Chrome :**
- **Windows** : `C:\Users\TON_NOM\AppData\Local\Google\Chrome\User Data`
- **Linux/macOS** : `~/.config/google-chrome/` ou `~/.config/chromium/`

---

#### 2️⃣ **Utiliser des User-Agents réalistes**
Cloudflare détecte Selenium grâce aux User-Agents par défaut. Change-les pour ressembler à un vrai utilisateur.

```python
from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)
driver.get("https://www.site.com/")
```

---

#### 3️⃣ **Émuler les mouvements d'un vrai utilisateur**
Ajoute des pauses et des actions humaines pour éviter d'être détecté.

```python
import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

driver = webdriver.Chrome()
driver.get("https://www.site.com/")

time.sleep(5)  # Attendre que la page se charge

# Simuler un scroll vers le bas
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

# Simuler un mouvement de souris
action = ActionChains(driver)
action.move_by_offset(100, 100).perform()
time.sleep(1)

print("✅ Navigation effectuée avec succès")
```

---

#### 4️⃣ **Utiliser un proxy pour masquer ton IP**
Cloudflare peut bloquer ton IP. Utilise un proxy résidentiel ou un VPN.

```python
from selenium import webdriver

proxy = "IP_PROXY:PORT"  # Exemple: 192.168.1.1:8080

options = webdriver.ChromeOptions()
options.add_argument(f'--proxy-server={proxy}')

driver = webdriver.Chrome(options=options)
driver.get("https://www.site.com/")
```

---

#### 5️⃣ **Utiliser le mode sans tête (Headless) avec des précautions**
Cloudflare bloque souvent le mode **headless**, mais tu peux l’améliorer :

```python
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Exécuter sans affichage
options.add_argument("--disable-blink-features=AutomationControlled")  # Masquer Selenium
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # Masquer Selenium

driver.get("https://www.site.com/")
```

---

### 📌 **Conclusion**
Si Cloudflare bloque ton script :
✅ **Essaye d'utiliser un profil utilisateur**  
✅ **Change ton User-Agent**  
✅ **Simule un comportement humain (scroll, mouvements de souris)**  
✅ **Utilise un proxy ou un VPN si ton IP est bloquée**  
✅ **Utilise le mode headless avec des modifications**  

Si Cloudflare affiche un **CAPTCHA**, il faudra un **solveur CAPTCHA** (ex. TwoCaptcha) pour le contourner.

Tu veux essayer une de ces solutions et voir si ça marche ? 🚀