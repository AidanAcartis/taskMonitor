Parfait — voici une grosse liste variée de commandes (avec exemples) réparties par domaine : **web, système, réseau, pentest/sécurité, développement, bases de données, conteneurs / cloud, utilitaires divers**.
Tu peux les copier-coller dans ton outil pour tester le parsing (`el_1`, `el_2`, …) et la recherche dans `dict_json`.

Je donne pour chaque commande : la **ligne d’exemple** et **une courte description** (une phrase), pour que tu aies du contenu de test réaliste.

---

# Web / HTTP / APIs

```bash
curl -X GET "https://api.example.com/users" -H "Accept: application/json"
curl -X POST "https://api.example.com/login" -d '{"user":"alice","pw":"x"}' -H "Content-Type: application/json"
http GET https://example.com/api/status
wget -q --show-progress https://example.com/archive.tar.gz
ntlmrelayx -tf targets.txt -smb2-support
```

Descriptions courtes : requêtes GET/POST, téléchargement de fichier, test d’API.

# System / Files / Process

```bash
ls -la /var/log
ls -l /home/user -a
stat /etc/passwd
df -h
du -sh /home/user/projects
ps aux | grep nginx
top -b -n1
htop
nice -n 10 ./long_job.sh
kill -9 12345
systemctl status nginx
journalctl -u nginx --since "1 hour ago"
sudo reboot
```

Descriptions : listing, espace disque, processus, gestion service, redémarrage.

# Networking (client / tools)

```bash
ip addr show
ip route get 8.8.8.8
ss -tuln
netstat -tulnp
traceroute -n 8.8.8.8
mtr --report 8.8.8.8
ping -c 4 1.1.1.1
curl -I https://example.com
dig +short example.com
host -t mx example.com
tcpdump -i eth0 port 80 -w capture.pcap
nmap -sS -p 1-1024 192.168.1.0/24
nmap -sV --script=vuln 10.0.0.5
```

# Networking (server / config)

```bash
iptables -L -n
ufw status verbose
route add default gw 192.168.1.1
systemd-resolve --status
ethtool eth0
```

# Pentest / Sécurité / Forensics (tests)

```bash
hydra -l admin -P wordlist.txt ssh://10.0.0.5
medusa -h 10.0.0.5 -u root -P passlist.txt -M ssh
sqlmap -u "http://vuln/test.php?id=1" --batch --dbs
john --wordlist=rockyou.txt hashes.txt
gobuster dir -u https://example.com -w common.txt -t 50
ffuf -u https://example.com/FUZZ -w fuzz.txt -mc 200
nikto -h https://example.com
openssl s_client -connect example.com:443 -servername example.com
wireshark
```

# Development / Build / Version control

```bash
git clone https://github.com/user/repo.git
git checkout -b feature/foo
git commit -am "fix bug"
git push origin HEAD
docker build -t myapp:latest .
docker run --rm -p 8080:80 myapp:latest
docker-compose up -d
npm install express
npm run build
yarn add lodash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/ -q
make test
```

# Language runtimes / REPL / scripts

```bash
node server.js
node --watch server.js
node -e "console.log(process.version)"
python app.py
python -m http.server 8000
ruby script.rb
php -S 0.0.0.0:8000 -t public
```

# Databases / Query tools

```bash
psql -h localhost -U alice -d mydb -c "SELECT count(*) FROM users;"
mysql -u root -p -e "SHOW DATABASES;"
sqlite3 /tmp/test.db "SELECT name FROM sqlite_master WHERE type='table';"
redis-cli -h 127.0.0.1 -p 6379 CLUSTER INFO
mongo --eval 'db.stats()' mongodb://localhost:27017
pg_dump -U postgres -d mydb -F c -f dump.c
```

# Containers / Cloud CLI

```bash
kubectl get pods -n kube-system
kubectl logs -f deploy/nginx
aws s3 ls s3://my-bucket --recursive
aws ec2 describe-instances --filters Name=instance-state-name,Values=running
gcloud compute instances list --filter="zone:( us-central1-a )"
az vm list -o table
helm repo add stable https://charts.helm.sh/stable
helm install mychart stable/nginx
```

# Utilities / Text processing / Archives

```bash
tar -czvf archive.tgz /path/to/dir
unzip file.zip -d /tmp
grep -r "TODO" src/
grep -rnI --color=auto "password" /etc
awk -F: '{print $1}' /etc/passwd
sed -n '1,200p' logfile.log
cut -d',' -f1 data.csv | sort | uniq -c
jq '.users[] | {name: .name, id: .id}' data.json
base64 -d token.txt | jq
split -b 10M big.iso part_
```

# Email / Messaging / LDAP

```bash
sendmail -v user@example.com < mail.txt
msmtp --host=smtp.example.com --port=587 --tls --user=alice
ldapsearch -x -H ldap://ldap.example.org -b "dc=example,dc=org" "(uid=aidan)"
```

# Build / CI tools

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t myorg/myapp:multi .
circleci local execute
gitlab-runner exec docker myjob
ansible-playbook -i hosts site.yml --limit webservers
```

# Monitoring / Metrics / Logs

```bash
curl -s http://localhost:9090/api/v1/query?query=up
promtool check config /etc/prometheus/prometheus.yml
journalctl -u docker --since "2025-10-01"
htop
```

# Misc (useful one-liners)

```bash
echo "hello" | md5sum
openssl genrsa -out key.pem 2048
ssh -i ~/.ssh/id_rsa -p 2222 user@host
scp -P 2222 file user@host:/tmp
rsync -avz /src/ remote:/dest/
crontab -l
atq
whoami
uptime
last -n 5
```

---

### Remarques pour tes tests

* Inclure des commandes avec **options courtes (`-r -a`)** et **longues (`--color --recursive`)** permet de tester la fusion `cmd + option`.
* Ajouter des modèles dans `dict_json` pour ces commandes (p.ex. `grep -r <path>`, `ls -l`, `ls -a`, `docker run -p <host>:<container>`, `kubectl get pods -n <ns>`) te permettra d’obtenir des descriptions `desc_i`.
* Pour le parsing d’arguments entre guillemets (`'main'` ou `"search pattern"`), assure-toi que `shlex.split` est utilisé pour conserver les groupes comme un argument unique.
* Pour le pentest, certaines commandes (hydra, nmap scripts, sqlmap) ont beaucoup d’options — ce sont de bons cas pour tester alternatives `{{[-r|--recursive]}}`.

---

Si tu veux, je peux aussi :

* te fournir un **fichier `test_commands.txt`** contenant une grosse sélection (toutes les lignes ci‑dessus) prêt à être bouclé par ton script,
* ou générer automatiquement des **entrées JSON d’exemple** pour `dict_json/` correspondant à ces commandes (description + patterns) afin que tu aies du contenu de test immédiat.

Laquelle préfères‑tu ?
