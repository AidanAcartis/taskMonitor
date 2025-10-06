Tu peux exécuter ce script en permanence de plusieurs façons :  

### 1. **Lancer le script en arrière-plan avec `nohup`**
Cette méthode permet d'exécuter le script même après la fermeture du terminal :  
```bash
nohup /chemin/vers/ton_script.sh > /dev/null 2>&1 &
```
Cela lance le script et ignore toute sortie, pour éviter que le processus ne se bloque.  

---

### 2. **Utiliser `tmux` ou `screen`**  
Si tu veux pouvoir détacher et rattacher la session, utilise `tmux` ou `screen` :  
```bash
tmux new -s surveillance
bash /chemin/vers/ton_script.sh
```
Ensuite, tu peux détacher la session avec `Ctrl+B, D` et la retrouver avec :  
```bash
tmux attach -t surveillance
```

---

### 3. **Le lancer automatiquement au démarrage avec `systemd`**  
Créer un service `systemd` pour exécuter le script dès le démarrage :  

1. **Créer un fichier de service**  
   ```bash
   sudo nano /etc/systemd/system/surveillance.service
   ```
2. **Ajouter ceci dans le fichier** :
   ```ini
   [Unit]
   Description=Surveillance des fenêtres
   After=network.target

   [Service]
   ExecStart=/bin/bash /chemin/vers/ton_script.sh
   Restart=always
   User=aidan
   Environment=DISPLAY=:1
   Environment=XAUTHORITY=/home/aidan/.Xauthority

   [Install]
   WantedBy=multi-user.target
   ```
3. **Activer et démarrer le service** :
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable surveillance.service
   sudo systemctl start surveillance.service
   ```
4. **Vérifier son état** :
   ```bash
   systemctl status surveillance.service
   ```

---

### 4. **Utiliser `crontab` pour le lancer au démarrage**  
Ajoute cette ligne dans `crontab -e` :  
```bash
@reboot /bin/bash /chemin/vers/ton_script.sh &
```
Cela démarre le script automatiquement après un redémarrage.

---

**Quelle méthode préfères-tu ?** 😊