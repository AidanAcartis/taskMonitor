import os
import re
import json

from .context_extractor import extract_context_from_command
from .command_description_service import describe_command
from resources.linux_special_files import LINUX_SPECIAL_FILES  # existant


from pathlib import Path
from core.config import BASE_DIR


# ─────────────────── LOAD JSON DICTS ───────────────────

DICT_DIR = BASE_DIR / "taskmonitor" / "dicts"

_CACHE = {}

def load_json(name):
    if name not in _CACHE:
        with open(DICT_DIR / name, "r") as f:
            _CACHE[name] = json.load(f)
    return _CACHE[name]

TOOLS = load_json("TOOLS.json")
FILE_EXTENSION = load_json("FILE_EXTENSION.json")
MIME_MAP = load_json("mime_map.json")

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
    # On cherche le match exact du chemin dans LINUX_SPECIAL_FILES
    special_match = None
    for path, info in LINUX_SPECIAL_FILES.items():
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
            if d in LINUX_SPECIAL_FILES:
                context_elements.append(f"targeting the special file {d} which is {LINUX_SPECIAL_FILES[d]}")
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
        if directory in LINUX_SPECIAL_FILES:
            return f"{directory}, directory, {LINUX_SPECIAL_FILES[directory]}, navigated by the user"
        return f"{directory}, directory, navigated by the user"

    return ""