"""
describe_events.py
------------------
Lit events_normalized.csv, remplit la colonne 'description' selon event_type :

  file      → 'filename.ext' opened with 'App', in 'Directory', <description IA>
  app       → The user used 'App'
  directory → The user worked in 'Directory'
  command   → 'command', <description cmddesc>

Résultat écrit dans : events_described.csv
"""

import os
import re
import csv
import subprocess

import torch
import torch.nn as nn
import pandas as pd
from transformers import AutoTokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
CSV_INPUT   = "events_normalized.csv"
CSV_OUTPUT  = "events_described.csv"
MODEL_DIR   = "./Gen_Desc_Model/full_finetuned"
LEXICAL_DIM = 512
BATCH_SIZE  = 8
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ─────────────────────────────────────────────
# PARTIE 1 — Modèle T5 pour les fichiers
# ─────────────────────────────────────────────
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
    state     = torch.load(f"{MODEL_DIR}/pytorch_model.bin", map_location=DEVICE)
    model.load_state_dict(state, strict=False)
    model.to(DEVICE).eval()
    lex_model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"  Device : {DEVICE}")
    return tokenizer, model, lex_model


def generate_file_descriptions(filenames: list[str], tokenizer, model, lex_model) -> list[str]:
    """
    Génère une description IA pour chaque stem de fichier (sans extension).
    Retourne une liste de descriptions dans le même ordre.
    """
    descriptions = []

    for i in range(0, len(filenames), BATCH_SIZE):
        batch = filenames[i : i + BATCH_SIZE]

        prompts = [
            f"Given the following filename, generate a short description "
            f"of what the file is likely about.\n\nFilename: {name}\n\nDescription:"
            for name in batch
        ]

        inputs = tokenizer(
            prompts, return_tensors="pt",
            padding=True, truncation=True, max_length=128
        ).to(DEVICE)

        with torch.no_grad():
            outputs = model.generate(
                input_ids      = inputs["input_ids"],
                attention_mask = inputs["attention_mask"],
                max_new_tokens = 60,
                num_beams      = 3,
            )

        descriptions.extend(
            tokenizer.decode(o, skip_special_tokens=True) for o in outputs
        )
        print(f"    [{i + len(batch)}/{len(filenames)}] fichiers décrits")

    return descriptions


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


# ─────────────────────────────────────────────
# PARTIE 3 — Construction des descriptions
# ─────────────────────────────────────────────
def get_file_type(filename: str) -> str:
    """Retourne le type de fichier en anglais à partir de l'extension."""
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    TYPE_MAP = {
        "py"  : "Python script",  "sh"  : "shell script",
        "js"  : "JavaScript file","ts"  : "TypeScript file",
        "html": "HTML file",      "css" : "CSS file",
        "json": "JSON file",      "yaml": "YAML file",
        "yml" : "YAML file",      "toml": "TOML file",
        "txt" : "text file",      "md"  : "Markdown file",
        "csv" : "CSV file",       "xlsx": "Excel file",
        "xls" : "Excel file",     "pdf" : "PDF file",
        "png" : "PNG image",      "jpg" : "JPEG image",
        "jpeg": "JPEG image",     "svg" : "SVG image",
        "mp4" : "video file",     "mp3" : "audio file",
        "wav" : "audio file",     "zip" : "ZIP archive",
        "tar" : "archive file",   "log" : "log file",
        "conf": "configuration file", "cfg": "configuration file",
        "ini" : "configuration file", "sql": "SQL file",
        "db"  : "database file",  "c"   : "C source file",
        "cpp" : "C++ source file","h"   : "header file",
        "java": "Java file",      "rs"  : "Rust file",
        "go"  : "Go file",        "rb"  : "Ruby file",
        "php" : "PHP file",
    }
    return TYPE_MAP.get(ext, f"{ext.upper()} file" if ext else "file")


def build_description(row: dict, file_desc_map: dict) -> str:
    """
    Format calqué sur le dataset d'entraînement :

    file    → "filename filetype in /dir opened with App to work on <desc>"
    app     → "App used to verb title"
    dir     → "directory directory navigated by the user"
    command → "command command used to desc[, in /dir][, with file]"
    """
    etype = str(row.get("event_type", "")).strip().lower()

    # ── FILE ────────────────────────────────
    if etype == "file":
        filename  = str(row.get("file",      "")).strip()
        app       = str(row.get("app",       "")).strip()
        directory = str(row.get("directory", "")).strip()

        stem     = os.path.splitext(os.path.basename(filename))[0] if filename else ""
        ai_desc  = file_desc_map.get(stem, "")
        filetype = get_file_type(filename)

        parts = [f"{filename} {filetype}"]
        if directory:
            parts.append(f"in {directory}")
        if app:
            parts.append(f"opened with {app}")
        if ai_desc:
            ai_clean = re.sub(r"^[Ii]t likely (contains?|collects?)\s*", "", ai_desc).strip()
            if ai_clean:
                parts.append(f"to work on {ai_clean}")

        return " ".join(p for p in parts if p)

    # ── APP ─────────────────────────────────
    elif etype == "app":
        app = str(row.get("app", "")).strip()
        raw = str(row.get("raw", "")).strip()

        title = ""
        if raw and " - " in raw:
            parts_raw = raw.split(" - ")
            candidate = " - ".join(parts_raw[:-1]).strip()
            if candidate.lower() != app.lower():
                title = candidate

        def infer_verb(title: str, app: str) -> str:
            t = title.lower()
            a = app.lower()
            if any(k in t for k in ("youtube", "twitch", "netflix", "dailymotion",
                                     "vimeo", "peertube", "invidious")):
                return "watch"
            if a in ("vlc", "mpv", "totem", "celluloid"):
                return "watch"
            if any(k in t for k in ("spotify", "soundcloud", "deezer",
                                     "bandcamp", "last.fm", "music")):
                return "listen to music on"
            if a in ("rhythmbox", "clementine", "audacious", "amarok"):
                return "listen to music on"
            if any(k in t for k in ("gmail", "outlook", "inbox", "mail",
                                     "thunderbird", "protonmail")):
                return "read and write emails on"
            if a in ("thunderbird", "evolution", "geary"):
                return "read and write emails on"
            if a in ("visual studio code", "code", "gedit", "nano",
                     "vim", "neovim", "sublime text", "atom", "kate"):
                return "edit files using"
            if any(k in t for k in ("google docs", "overleaf", "notion",
                                     "libreoffice", "writer")):
                return "write a document using"
            if any(k in t for k in ("github", "gitlab", "bitbucket")):
                return "review code on"
            if any(k in t for k in ("stack overflow", "reddit", "wikipedia",
                                     "medium", "dev.to", "documentation",
                                     "mdn", "read the docs")):
                return "read content on"
            if a in ("nautilus", "thunar", "nemo", "dolphin", "files", "pcmanfm"):
                return "navigate files using"
            if a in ("brave", "firefox", "google-chrome", "chromium",
                     "brave-browser", "opera", "vivaldi"):
                return "browse the web using"
            return "use"

        verb = infer_verb(title, app)
        if title and app:
            return f"{app} used to {verb} {title}"
        elif app:
            return f"{app} application used by the user"
        return "application used by the user"

    # ── DIRECTORY ───────────────────────────
    elif etype == "directory":
        directory = str(row.get("directory", "")).strip()
        if directory:
            return f"{directory} directory navigated by the user"
        return "directory navigated by the user"

    # ── COMMAND ─────────────────────────────
    elif etype == "command":
        command  = str(row.get("command", "")).strip()
        cmd_desc = describe_command(command)
        cmd_files, cmd_dirs = extract_context_from_command(command)

        if cmd_desc and cmd_desc.strip() not in ("", "No description found"):
            cmd_desc_clean = cmd_desc.lstrip(", ").strip().rstrip(".")
            # Nettoyer préfixes résiduels cmddesc
            cmd_desc_clean = re.sub(r"^-\s*", "", cmd_desc_clean).strip()
            base = f"{command} command used to {cmd_desc_clean.lower()}"
        else:
            base = f"{command} command executed in terminal"

        context = []
        for d in cmd_dirs:
            context.append(f"in {d}")
        for f in cmd_files:
            context.append(f"with the {f} file")

        if context:
            return base + ", " + ", ".join(context)
        return base

    return ""


# ─────────────────────────────────────────────
print("=" * 60)
print("describe_events.py")
print("=" * 60)

# ── Lecture du CSV ───────────────────────────
print(f"\n[1/4] Lecture de {CSV_INPUT} ...")
df = pd.read_csv(CSV_INPUT)
df.columns = df.columns.str.strip().str.lower()

# S'assurer que les colonnes optionnelles existent
for col in ("file", "app", "directory", "command"):
    if col not in df.columns:
        df[col] = ""

df = df.fillna("")
print(f"      {len(df)} lignes chargées.")

# ── Génération des descriptions fichiers ─────
print("\n[2/4] Génération des descriptions de fichiers (T5) ...")
file_rows = df[df["event_type"].str.strip().str.lower() == "file"].copy()

file_desc_map = {}   # stem → description IA

if file_rows.empty:
    print("      Aucun fichier trouvé, étape ignorée.")
else:
    # Extraire les stems uniques
    stems = (
        file_rows["file"]
        .apply(lambda f: os.path.splitext(os.path.basename(str(f).strip()))[0])
        .dropna()
        .unique()
        .tolist()
    )
    stems = [s for s in stems if s]
    print(f"      {len(stems)} stems uniques : {stems}")

    tokenizer, t5_model, lex_model = load_t5_model()
    descriptions = generate_file_descriptions(stems, tokenizer, t5_model, lex_model)
    file_desc_map = dict(zip(stems, descriptions))

# ── Descriptions commandes ───────────────────
print("\n[3/4] Génération des descriptions de commandes (cmddesc) ...")
cmd_rows  = df[df["event_type"].str.strip().str.lower() == "command"]
print(f"      {len(cmd_rows)} commande(s) à décrire.")

# ── Construction colonne description ────────
print("\n[4/4] Construction de la colonne 'description' ...")
df["description"] = df.apply(
    lambda row: build_description(row.to_dict(), file_desc_map),
    axis=1
)

# ── Sauvegarde ───────────────────────────────
df.to_csv(CSV_OUTPUT, index=False)
print(f"\n✅ Fichier sauvegardé : {CSV_OUTPUT}")
print(f"   {len(df)} lignes traitées.\n")
print(df[["event_type", "file", "app", "directory", "command", "description"]].to_string(index=False))