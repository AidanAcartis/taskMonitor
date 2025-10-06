Oui, mais cela dépend du navigateur utilisé et des permissions disponibles.  

---

### 🔹 **Méthodes pour récupérer l'heure d'ouverture et de fermeture d'un site**  

#### ✅ **Méthode 1 : Utiliser l’historique des navigateurs (heure d’ouverture uniquement)**  
Les navigateurs comme **Chrome** et **Firefox** stockent l'heure d'accès aux sites dans une base de données SQLite.  
Mais, cela ne donne que **l’heure d’ouverture**, pas la fermeture.  

##### 🔸 **Récupérer l'heure d'ouverture sur Firefox**  
```bash
sqlite3 ~/.mozilla/firefox/*.default-release/places.sqlite "
SELECT url, datetime(last_visit_date/1000000, 'unixepoch', 'localtime') 
FROM moz_places 
ORDER BY last_visit_date DESC;"
```

##### 🔸 **Récupérer l'heure d'ouverture sur Chrome**  
```bash
sqlite3 ~/.config/google-chrome/Default/History "
SELECT url, datetime(last_visit_time/1000000-11644473600, 'unixepoch', 'localtime') 
FROM urls 
ORDER BY last_visit_time DESC;"
```
📌 **Limite** : Cela donne **seulement** l’heure où le site a été ouvert, pas quand il a été fermé.

---

#### ✅ **Méthode 2 : Capturer les processus du navigateur (début et fin de session)**
Si tu veux suivre **l’ouverture et la fermeture d’un site**, tu peux surveiller les processus du navigateur et les onglets ouverts en temps réel.

##### 🔸 **Surveiller les onglets ouverts en temps réel (Firefox & Chrome)**
Utiliser **`wmctrl`** et **`xdotool`** sur Linux pour suivre les fenêtres et onglets :
```bash
while true; do
    wmctrl -l | grep -E "Firefox|Chrome" >> sites_ouverts.log
    sleep 5
done
```
📌 **Limite** : Cela capture les **titres des fenêtres**, mais ne donne pas l’heure exacte de fermeture d’un site.

---

#### ✅ **Méthode 3 : Utiliser un script Python pour surveiller les onglets**  
Python peut surveiller les fenêtres ouvertes et détecter les changements :  

```python
import time
import psutil
from datetime import datetime

visited_sites = {}

def get_active_window():
    try:
        import pygetwindow as gw
        return gw.getActiveWindow().title
    except:
        return None

while True:
    active_window = get_active_window()
    
    if active_window and ("Firefox" in active_window or "Chrome" in active_window):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if active_window not in visited_sites:
            visited_sites[active_window] = {'open_time': now, 'close_time': None}
        
        visited_sites[active_window]['close_time'] = now
    
    time.sleep(5)
    
    # Sauvegarde des données
    with open("sites_visites.log", "w") as f:
        for site, times in visited_sites.items():
            f.write(f"{site} | Ouvert : {times['open_time']} | Fermé : {times['close_time']}\n")
```
📌 **Avantage** : Cela enregistre **l'heure d’ouverture ET de fermeture** d’un site.  
📌 **Limite** : Ce script surveille les **fenêtres visibles** et ne peut pas voir les onglets en arrière-plan.

---

### **Quelle est la meilleure méthode ?**  
✔ Si tu veux juste l’heure d’ouverture → **Historique SQLite**  
✔ Si tu veux ouverture + fermeture → **Surveillance des fenêtres (Python ou Bash)**  

Tu veux un script Python complet qui fait tout automatiquement ?