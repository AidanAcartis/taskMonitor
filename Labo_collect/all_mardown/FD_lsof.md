La colonne **FD** (File Descriptor) de `lsof` indique le descripteur de fichier utilisé par un processus. Il existe plusieurs types de valeurs dans cette colonne, classées selon leur usage.  

---

### 🔹 **Catégories de valeurs de la colonne FD dans `lsof`**  

#### **1️⃣ Descripteurs de fichiers standards**  
- **0u** → Entrée standard (**stdin**)  
- **1u** → Sortie standard (**stdout**)  
- **2u** → Erreur standard (**stderr**)  

📌 **Note** : Le suffixe `u` indique que le fichier est ouvert en lecture et écriture.  

---

#### **2️⃣ Types d’accès**  
Chaque descripteur de fichier peut être suivi de :  
- **r** → Ouvert en lecture seule (Read)  
- **w** → Ouvert en écriture seule (Write)  
- **u** → Ouvert en lecture et écriture (Update)  

Exemple :  
- `3r` → Descripteur de fichier 3 en lecture seule  
- `4w` → Descripteur de fichier 4 en écriture seule  
- `5u` → Descripteur de fichier 5 en lecture et écriture  

---

#### **3️⃣ Types spéciaux de descripteurs**  
- **cwd** → Répertoire de travail actuel (**Current Working Directory**)  
- **rtd** → Répertoire racine du processus (**Root Directory**)  
- **txt** → Fichier binaire exécuté par le processus (**Text file** = Code exécutable)  
- **mem** → Fichier de bibliothèque chargée en mémoire (**Memory-mapped file**)  
- **mmap** → Fichier mappé en mémoire (**Memory mapping**)  

---

#### **4️⃣ Sockets et connexions réseau**  
- **TYPE=IPv4 / IPv6** → Socket réseau  
- **UDP** → Socket UDP  
- **TCP** → Socket TCP  
- **sock** → Socket UNIX  
- **PIPE** → Tube nommé (pipe)  
- **FIFO** → FIFO (First-In-First-Out)  

Exemple :  
- `10u IPv4` → Descripteur 10, ouvert en lecture/écriture, utilisé pour une connexion IPv4  
- `7u sock` → Descripteur 7 utilisé pour un socket UNIX  

---

#### **5️⃣ Descripteurs liés aux verrous et périphériques**  
- **CHR** → Périphérique de type caractère (**Character device**)  
- **BLK** → Périphérique de type bloc (**Block device**)  
- **DEL** → Fichier supprimé mais toujours en cours d’utilisation  
- **LCK** → Verrou sur un fichier (**Lock**)  

---

### 💡 **Liste complète des valeurs possibles de la colonne FD dans `lsof`**  

| Type FD  | Signification |
|----------|--------------|
| `cwd`    | Répertoire de travail actuel |
| `rtd`    | Répertoire racine du processus |
| `txt`    | Fichier binaire exécuté |
| `mem`    | Bibliothèque chargée en mémoire |
| `mmap`   | Fichier mappé en mémoire |
| `0u`     | Entrée standard (stdin) |
| `1u`     | Sortie standard (stdout) |
| `2u`     | Erreur standard (stderr) |
| `N[r/w/u]` | Descripteur de fichier ordinaire (lecture, écriture, ou mise à jour) |
| `TYPE=IPv4` | Socket réseau IPv4 |
| `TYPE=IPv6` | Socket réseau IPv6 |
| `sock`   | Socket UNIX |
| `UDP`    | Socket UDP |
| `TCP`    | Socket TCP |
| `PIPE`   | Tube nommé (pipe) |
| `FIFO`   | FIFO (First-In-First-Out) |
| `CHR`    | Périphérique de type caractère |
| `BLK`    | Périphérique de type bloc |
| `DEL`    | Fichier supprimé mais encore utilisé |
| `LCK`    | Verrou sur un fichier |

---

📌 **Comment voir ces valeurs en direct ?**  
Exécutez la commande suivante :  
```sh
lsof -nP | awk '{print $4}' | sort | uniq -c
```
Cela affichera tous les types de FD utilisés par les processus en cours sur votre machine. 🚀