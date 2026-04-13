Ton installation Docker est incomplète — il manque le plugin Compose. Voici comment régler ça :

**1. Installer Docker correctement (version complète)**
```bash
# Désinstaller l'ancienne version partielle
sudo apt remove docker docker.io containerd runc

# Installer les dépendances
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# Ajouter la clé GPG officielle Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Ajouter le dépôt officiel
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Installer Docker + Compose plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

**2. Ajouter ton user au groupe docker**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**3. Vérifier**
```bash
docker --version
docker compose version
```

Les deux doivent répondre. Ensuite on peut builder l'image.