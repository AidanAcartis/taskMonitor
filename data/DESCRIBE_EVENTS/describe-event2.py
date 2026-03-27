import os, re, subprocess, json
import torch, torch.nn as nn, pandas as pd
from transformers import AutoTokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer

# ───────────────── CONFIG ─────────────────
CSV_INPUT   = "events_normalized.csv"
CSV_OUTPUT  = "events_described.csv"
MODEL_DIR   = "./Gen_Desc_Model/full_finetuned"
LEXICAL_DIM = 512
BATCH_SIZE  = 8
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ───────────────── DICTS SUPPLÉMENTAIRES ─────────────────
linux_special_files = {
    # ── SYSTEM CONFIG & ENVIRONMENT ──────────────────
    "/etc/environment": "global environment variables",
    "/etc/profile": "system-wide shell profile",
    "/etc/bash.bashrc": "system-wide bash config (Debian/Ubuntu)",
    "/etc/bashrc": "system-wide bash config (RHEL/CentOS)",
    "/etc/hostname": "system static hostname",
    "/etc/issue": "pre-login message/system identification",
    "/etc/motd": "message of the day (post-login)",
    "/etc/locale.conf": "system language and regional settings",
    "/etc/os-release": "operating system identification",
    "/etc/shells": "list of valid login shells",
    "/etc/timezone": "system timezone configuration",
    "/etc/skel/.bashrc": "default bashrc template for new users",
    
    # ── USER SHELL CONFIGS (HOME) ────────────────────
    "~/.bashrc": "user-specific bash aliases and functions",
    "~/.bash_profile": "user login shell configuration",
    "~/.bash_logout": "commands executed at user logout",
    "~/.profile": "user-specific environment settings",
    "~/.zshrc": "Zsh shell configuration (if installed)",
    
    # ── NETWORK & DNS ────────────────────────────────
    "/etc/hosts": "static hostname to IP mapping",
    "/etc/resolv.conf": "DNS resolver configuration",
    "/etc/network/interfaces": "legacy network interface config",
    "/etc/netplan": "modern network configuration (Ubuntu/Debian)",
    "/etc/nsswitch.conf": "name service switch configuration",
    "/etc/host.conf": "resolver lookup order",
    "/etc/protocols": "list of IP protocols and numbers",
    "/etc/services": "list of port names and numbers",
    
    # ── USERS & SECURITY ─────────────────────────────
    "/etc/passwd": "user account information",
    "/etc/shadow": "secure user password hashes",
    "/etc/group": "group account information",
    "/etc/gshadow": "secure group password hashes",
    "/etc/sudoers": "sudo privileges configuration",
    "/etc/pam.d": "pluggable authentication modules config",
    "/etc/login.defs": "shadow password suite configuration",
    "/etc/securetty": "list of terminals allowed for root login",
    "/etc/security/limits.conf": "system resource limits for users",
    "~/.ssh/authorized_keys": "SSH public keys for remote access",
    "~/.ssh/id_rsa": "SSH private key (highly sensitive)",
    "~/.ssh/known_hosts": "list of trusted remote host keys",
    
    # ── FILESYSTEM & STORAGE ─────────────────────────
    "/etc/fstab": "static information about filesystems",
    "/etc/mtab": "list of currently mounted filesystems",
    "/etc/crypttab": "encrypted device table",
    "/etc/exports": "NFS server export configuration",
    "/etc/auto.master": "autofs mount points configuration",
    
    # ── SERVICES & CRON ──────────────────────────────
    "/etc/crontab": "system-wide cron schedule",
    "/etc/cron.d": "modular system cron jobs",
    "/etc/systemd/system": "systemd service unit files",
    "/etc/ssh/sshd_config": "SSH server daemon configuration",
    "/etc/nginx/nginx.conf": "Nginx web server configuration",
    "/etc/apache2/apache2.conf": "Apache web server configuration",
    "/etc/mysql/my.cnf": "MySQL/MariaDB database configuration",
    "/etc/redis/redis.conf": "Redis server configuration",
    
    # ── PACKAGE MANAGEMENT ───────────────────────────
    "/etc/apt/sources.list": "APT software repository list",
    "/etc/apt/sources.list.d": "additional APT repository files",
    "/etc/yum.repos.d": "YUM/DNF repository configuration",
    "/var/lib/dpkg/status": "installed package status database",
    
    # ── KERNEL & HARDWARE ────────────────────────────
    "/etc/modules": "list of kernel modules to load at boot",
    "/etc/modprobe.d": "kernel module loading rules",
    "/etc/sysctl.conf": "kernel runtime parameters (sysctl)",
    "/etc/X11/xorg.conf": "X Server (graphics) configuration",
    "/boot/grub/grub.cfg": "GRUB bootloader configuration",
    
    # ── VIRTUAL FILESYSTEMS (KERNEL/PROCESS) ──────────
    "/proc/cpuinfo": "processor and architecture details",
    "/proc/meminfo": "detailed memory usage statistics",
    "/proc/uptime": "system uptime and idle time",
    "/proc/version": "kernel version and build info",
    "/proc/cmdline": "bootloader kernel parameters",
    "/proc/net/dev": "network interface statistics",
    "/proc/sys": "kernel runtime parameters (sysctl)",
    "/proc/self/exe": "link to current process executable",
    "/dev/null": "null device (data sink)",
    "/dev/zero": "zero device (null byte generator)",
    "/dev/random": "blocking random number generator",
    "/dev/urandom": "non-blocking random number generator",
    "/dev/sda": "primary hard drive device file",
    
    # ── LOGS & HISTORY ────────────────────────────────
    "/var/log/syslog": "central system log (Debian/Ubuntu)",
    "/var/log/messages": "general system log (RHEL/CentOS)",
    "/var/log/auth.log": "authentication and security logs",
    "/var/log/kern.log": "kernel messages log",
    "/var/log/dmesg": "kernel ring buffer messages",
    "/var/log/dpkg.log": "Debian package manager logs",
    "/var/log/apt/history.log": "apt package history",
    "/var/log/faillog": "failed login attempts",
    "/var/log/lastlog": "last login information for users",
    "/var/log/wtmp": "login/logout history (binary)",
    "/var/log/btmp": "failed login records (binary)",
    "~/.bash_history": "user shell command history",
}

# Charger les fichiers JSON
FILE_EXTENSION = json.load(open("./DICT/FILE_EXTENSION.json"))
MIME_MAP        = json.load(open("./DICT/mime_map.json"))
TOOLS           = json.load(open("./DICT/TOOLS.json"))

# ─────────────────── CLASSES & MODELS ───────────────────
# ─────────────────────────────────────────────
# PARTIE 1 — Modèle T5 pour les fichiers
# ─────────────────────────────────────────────
# ───────────────── CONFIGURATION D'INFÉRENCE ─────────────────
# Ces paramètres forcent le modèle à être plus précis et varié
INFERENCE_CONFIG = {
    "num_beams": 5,                # Explore plus de chemins pour trouver des mots clés (ex: windows)
    "no_repeat_ngram_size": 3,     # Empêche la répétition de suites de 3 mots (ex: "monitoring and monitoring")
    "repetition_penalty": 1.5,     # Pénalise fortement la réutilisation des mêmes mots
    "length_penalty": 1.0,         # Équilibre entre phrases courtes et longues
    "max_new_tokens": 50,          # Limite de longueur pour éviter les phrases qui divaguent
    "early_stopping": True         # Arrête la recherche dès qu'une phrase cohérente est finie
}

# ─────────────────── CLASSES & MODELS ───────────────────

class T5WithFusion(nn.Module):
    def __init__(self, model_name="google/flan-t5-small", lexical_dim=512):
        super().__init__()
        self.t5  = T5ForConditionalGeneration.from_pretrained(model_name)
        self.proj = nn.Linear(lexical_dim, self.t5.config.d_model)

    def forward(self, input_ids=None, attention_mask=None, labels=None,
                lexical_embeds=None, **kwargs):
        inputs_embeds = self.t5.encoder.embed_tokens(input_ids)
        if lexical_embeds is not None:
            lexical_proj  = self.proj(lexical_embeds.float()).to(inputs_embeds.device)
            inputs_embeds = inputs_embeds + lexical_proj.unsqueeze(1)
        return self.t5(
            input_ids=None, attention_mask=attention_mask,
            labels=labels, inputs_embeds=inputs_embeds, **kwargs
        )

    def prepare_inputs_for_generation(self, input_ids, attention_mask=None, **kwargs):
        # Assure que les embeds lexicaux sont transmis pendant la génération auto-régressive
        inputs = self.t5.prepare_inputs_for_generation(
            input_ids, attention_mask=attention_mask, **kwargs
        )
        if "lexical_embeds" in kwargs:
            inputs["lexical_embeds"] = kwargs["lexical_embeds"]
        return inputs

    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.t5, name)


def load_t5_model():
    """Charge tokenizer + modèle T5 fine-tuné."""
    print(f"  Chargement du modèle depuis {MODEL_DIR} ...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model     = T5WithFusion(model_name="google/flan-t5-small", lexical_dim=LEXICAL_DIM)
    
    # Chargement des poids
    state = torch.load(f"{MODEL_DIR}/pytorch_model.bin", map_location=DEVICE)
    model.load_state_dict(state, strict=False)
    model.to(DEVICE).eval()
    
    lex_model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"  Device : {DEVICE}")
    return tokenizer, model, lex_model


def generate_file_descriptions(filenames: list[str], tokenizer, model, lex_model) -> list[str]:
    """
    Génère une description IA avec correction des répétitions et focus amélioré.
    """
    descriptions = []

    for i in range(0, len(filenames), BATCH_SIZE):
        batch = filenames[i : i + BATCH_SIZE]

        # Note : On a légèrement modifié le prompt pour être plus directif ("specific purpose")
        prompts = [
            f"Describe the specific purpose of the following file.\n\nFilename: {name}\n\nDescription:"
            for name in batch
        ]

        inputs = tokenizer(
            prompts, return_tensors="pt",
            padding=True, truncation=True, max_length=128
        ).to(DEVICE)

        with torch.no_grad():
            # Injection de l'INFERENCE_CONFIG ici
            outputs = model.generate(
                input_ids      = inputs["input_ids"],
                attention_mask = inputs["attention_mask"],
                **INFERENCE_CONFIG
            )

        descriptions.extend(
            tokenizer.decode(o, skip_special_tokens=True) for o in outputs
        )
        print(f"    [{i + len(batch)}/{len(filenames)}] fichiers décrits avec succès")

    return descriptions

# ─────────────────── FONCTIONS UTILES ───────────────────
# ─────────────────────────────────────────────
# PARTIE 2 — cmddesc pour les commandes
# ─────────────────────────────────────────────
NOISE_PREFIXES = (
    "Command '", "Argument '", "String '",
    "Number '", "IP address '", "URL '", "JSON '",
    "File '", "Folder '", "Server '",
)

KNOWN_DIRS = {
    "Desktop", "Music", "Public", "Documents", "Videos",
    "Downloads", "Pictures", "Templates",
    # racine filesystem Linux
    "bin", "etc", "lib", "lib32", "lib64", "libx32", "opt", "sbin",
    "tmp", "usr", "var", "home", "root", "boot", "dev", "proc",
    "run", "srv", "sys", "mnt", "media", "snap", "cdrom",
    "lost+found",
}

FILE_RE = re.compile(r"\.[a-zA-Z0-9]+$")


def is_directory(token: str) -> bool:
    """Retourne True si le token ressemble à un répertoire."""
    if "/" in token:
        return True
    if token in KNOWN_DIRS:
        return True
    
    return False


def is_file(token: str) -> bool:
    """Retourne True si le token ressemble à un fichier (a une extension)."""
    return bool(FILE_RE.search(token)) and "/" not in token.rstrip("/")


def extract_context_from_command(command: str) -> tuple[list[str], list[str]]:
    """
    Parcourt les tokens d'une commande et retourne :
      - la liste des fichiers détectés
      - la liste des répertoires détectés
    On ignore les flags (commençant par -) et le premier token (la commande).
    """
    tokens = command.split()
    files, dirs = [], []

    for token in tokens[1:]:
        clean = token.strip("'\"")
        if not clean or clean.startswith("-"):
            continue

        basename = os.path.basename(clean.rstrip("/"))
        if is_file(basename):
            files.append(clean)
        elif is_directory(clean):
            dirs.append(clean)

    # Dédupliquer en préservant l'ordre
    seen  = set()
    files = [f for f in files if not (f in seen or seen.add(f))]
    seen  = set()
    dirs  = [d for d in dirs  if not (d in seen or seen.add(d))]

    return files, dirs


def run_cmddesc(command: str) -> str:
    result = subprocess.run(
        ["cmddesc"], input=command, capture_output=True, text=True
    )
    return result.stdout


def parse_cmddesc_output(raw_output: str) -> str:
    def is_noise(value: str) -> bool:
        return any(value.startswith(p) for p in NOISE_PREFIXES)

    def extract_value(line: str) -> str:
        return re.sub(r"^(desc_\w+|with sudo privilege):\s*", "", line.strip()).strip()

    sub_commands, current, mode = [], [], None

    for line in raw_output.splitlines():
        s = line.strip()

        if re.match(r"^=== Command \d+", s):
            if current:
                sub_commands.append(" + ".join(current))
            current, mode = [], None

        elif "FULL DESCRIPTION APPLIED" in s:
            mode = "full"

        elif "DESCRIPTION SEQUENTIELLE" in s:
            mode = "sequential"

        elif re.match(r"^(desc_|with sudo)", s):
            value = extract_value(s)
            if not value or is_noise(value):
                continue
            if mode == "full":
                if s.lstrip().startswith("desc_cmd"):
                    current.insert(0, value)
                else:
                    current.append(value)
            elif mode == "sequential":
                current.append(value)

    if current:
        sub_commands.append(" + ".join(current))

    result = " | ".join(sub_commands) if sub_commands else "No description found"

    # Nettoyer les préfixes résiduels de cmddesc
    result = re.sub(r"\bdesc_\w+:\s*", "", result).strip()
    result = re.sub(r"\s*\+\s*-\s*", ", ", result)
    result = re.sub(r"Command\s+'[^']+'\s*\+?\s*", "", result).strip()
    result = re.sub(r"^\s*-\s*", "", result).strip()   # tiret résiduel en début
    result = re.sub(r",\s*,", ",", result).strip()     # double virgule
    result = re.sub(r",\s*$", "", result).strip()      # virgule finale
    result = re.sub(r"\s{2,}", " ", result).strip()

    return result if result else "No description found"


def describe_command(command: str) -> str:
    command = command.strip()
    if not command:
        return ""
    try:
        return parse_cmddesc_output(run_cmddesc(command))
    except Exception as e:
        return f"[ERROR: {e}]"
    
def get_file_type(filename: str) -> str:
    """Retourne l'extension ou le type basé sur les dictionnaires."""
    ext = os.path.splitext(filename)[1].lower()
    types = []
    if ext in MIME_MAP: types.append(MIME_MAP[ext].get("comment", ""))
    if ext in FILE_EXTENSION: types.append(FILE_EXTENSION[ext])
    return ", ".join(types) if types else "file"

# ─────────────────── DESCRIPTION FINALE ───────────────────
def amplify_description(target: str, file_desc_map: dict = None) -> str:
    """
    Moteur de détection : Scanne le texte pour enrichir via IA et Dictionnaires.
    Priorité aux Linux Special Files.
    """
    file_desc_map = file_desc_map or {}
    elements = []
    
    # 1. Vérifier si la cible (ou une partie) est un fichier spécial Linux
    # On cherche le match exact du chemin dans linux_special_files
    special_match = None
    for path, info in linux_special_files.items():
        if path in target:
            special_match = info
            break
    
    if special_match:
        elements.append(special_match)
    else:
        # 2. Si pas special, on cherche l'extension et l'IA
        basename = os.path.basename(target.rstrip("/"))
        stem = os.path.splitext(basename)[0]
        
        # Extension / MIME
        ftype = get_file_type(target)
        if ftype != "file":
            elements.append(ftype)
            
        # IA Description
        if stem in file_desc_map:
            ai_val = file_desc_map[stem]
            ai_val = re.sub(r"^[Ii]t (likely|probably) (contains?|collects?|is|provides?)\s*", "", ai_val).strip()
            elements.append(ai_val)

    # 3. Dictionnaire TOOLS (pour détecter bash, nano, etc.)
    for tool, tool_desc in TOOLS.items():
        if re.search(rf"\b{re.escape(tool)}\b", target, re.IGNORECASE):
            elements.append(tool_desc)

    seen = set()
    unique = [e for e in elements if e and not (e.lower() in seen or seen.add(e.lower()))]
    return ", ".join(unique)


def build_description(row: dict, file_desc_map: dict) -> str:
    """
    Formateur final optimisé pour le dataset d'entraînement.
    Incorpore la logique infer_verb et élimine les parenthèses pour une lecture fluide.
    """
    etype = str(row.get("event_type", "")).strip().lower()

    # ── 1. TYPE: FILE ────────────────────────────────
    if etype == "file":
        filename  = str(row.get("file",      "")).strip()
        app       = str(row.get("app",       "")).strip()
        directory = str(row.get("directory", "")).strip()
        enriched_info = amplify_description(filename, file_desc_map)
        
        # Format: Nom, type, contexte, action, contenu
        parts = [f"{filename}, file"]
        if directory: parts.append(f"stored in {directory}")
        if app: parts.append(f"opened with {app}")
        if enriched_info: parts.append(f"contains data related to {enriched_info}")
        
        return ", ".join(p for p in parts if p)

    # ── 2. TYPE: COMMAND ─────────────────────────────
    elif etype == "command":
        command = str(row.get("command", "")).strip()
        cmd_desc = describe_command(command) 
        cmd_files, cmd_dirs = extract_context_from_command(command)

        if cmd_desc and cmd_desc.strip() not in ("", "No description found"):
            cmd_desc_clean = re.sub(r"^-\s*", "", cmd_desc.strip().rstrip(".")).lower()
            base = f"{command}, command, executed in terminal, used to {cmd_desc_clean}"
        else:
            base = f"{command}, command, executed in terminal"

        context_elements = []
        for d in cmd_dirs:
            if d in linux_special_files:
                context_elements.append(f"targeting the special file {d} which is {linux_special_files[d]}")
            else:
                context_elements.append(f"in {d}")
        
        for f in cmd_files:
            f_amplified = amplify_description(f, file_desc_map)
            if f_amplified:
                # Nettoyage des parenthèses éventuelles issues des dictionnaires
                clean_info = f_amplified.replace("(", "").replace(")", "")
                context_elements.append(f"with the {f} file which is a {clean_info}")
            else:
                context_elements.append(f"with the {f} file")

        if context_elements:
            return base + " " + " and ".join(context_elements)
        return base

    # ── 3. TYPE: APP ─────────────────────────────────
    elif etype == "app":
        app = str(row.get("app", "")).strip()
        raw = str(row.get("raw", "")).strip()
        
        title = ""
        if raw and " - " in raw:
            parts_raw = raw.split(" - ")
            candidate = " - ".join(parts_raw[:-1]).strip()
            if candidate.lower() != app.lower():
                title = candidate

        # --- Logique infer_verb réintégrée ---
        def infer_verb(title_str: str, app_str: str) -> str:
            t = title_str.lower()
            a = app_str.lower()
            if any(k in t for k in ("youtube", "twitch", "netflix", "dailymotion", "vimeo", "peertube", "invidious")):
                return "watch"
            if a in ("vlc", "mpv", "totem", "celluloid"):
                return "watch"
            if any(k in t for k in ("spotify", "soundcloud", "deezer", "bandcamp", "last.fm", "music")):
                return "listen to music on"
            if a in ("rhythmbox", "clementine", "audacious", "amarok"):
                return "listen to music on"
            if any(k in t for k in ("gmail", "outlook", "inbox", "mail", "thunderbird", "protonmail")):
                return "read and write emails on"
            if a in ("thunderbird", "evolution", "geary"):
                return "read and write emails on"
            if a in ("visual studio code", "code", "gedit", "nano", "vim", "neovim", "sublime text", "atom", "kate"):
                return "edit files using"
            if any(k in t for k in ("google docs", "overleaf", "notion", "libreoffice", "writer")):
                return "write a document using"
            if any(k in t for k in ("github", "gitlab", "bitbucket")):
                return "review code on"
            if any(k in t for k in ("stack overflow", "reddit", "wikipedia", "medium", "dev.to", "documentation", "mdn", "read the docs")):
                return "read content on"
            if a in ("nautilus", "thunar", "nemo", "dolphin", "files", "pcmanfm"):
                return "navigate files using"
            if a in ("brave", "firefox", "google-chrome", "chromium", "brave-browser", "opera", "vivaldi"):
                return "browse the web using"
            return "use"

        verb = infer_verb(title, app)
        
        if title:
            return f"{app}, application, used to {verb} {title}"
        
        # Description bonus via TOOLS si pas de titre
        app_desc = TOOLS.get(app, "application")
        return f"{app}, {app_desc}, used by the user"

    # ── 4. TYPE: DIRECTORY ───────────────────────────
    elif etype == "directory":
        directory = str(row.get("directory", "")).strip()
        if directory in linux_special_files:
            return f"{directory}, directory, {linux_special_files[directory]}, navigated by the user"
        return f"{directory}, directory, navigated by the user"

    return ""


# ─────────────────── SCRIPT PRINCIPAL ───────────────────
print("[1/4] Lecture CSV...")
df = pd.read_csv(CSV_INPUT).fillna("")
df.columns = df.columns.str.strip().str.lower()

# ── Extraction groupée pour T5 (Fichiers + Commandes)
print("[2/4] Collecte des noms de fichiers pour l'IA...")
stems_to_process = set()

# 1. On récupère les fichiers des événements "file"
for f in df[df.event_type.str.lower()=="file"]["file"]:
    if f:
        stems_to_process.add(os.path.splitext(os.path.basename(f))[0])

# 2. On récupère les fichiers cachés dans les événements "command"
for cmd in df[df.event_type.str.lower()=="command"]["command"]:
    files, _ = extract_context_from_command(cmd)
    for f in files:
        stems_to_process.add(os.path.splitext(os.path.basename(f))[0])

file_desc_map = {}
if stems_to_process:
    stems_list = list(stems_to_process)
    tokenizer, t5_model, lex_model = load_t5_model()
    # On génère les descriptions pour TOUS les fichiers détectés partout
    descriptions = generate_file_descriptions(stems_list, tokenizer, t5_model, lex_model)
    file_desc_map = dict(zip(stems_list, descriptions))

# ── Construction description finale
print("[3/4] Construction de la colonne description...")
df["description"] = df.apply(lambda r: build_description(r.to_dict(), file_desc_map), axis=1)

# ── Sauvegarde
df.to_csv(CSV_OUTPUT, index=False)
print(f"✅ Terminé ! Descriptions générées pour {len(stems_to_process)} fichiers uniques.")