import os
import re
from typing import List, Tuple

# Dossiers connus pour détecter les répertoires
KNOWN_DIRS = {
    "Desktop", "Music", "Public", "Documents", "Videos",
    "Downloads", "Pictures", "Templates",
    # racine filesystem Linux
    "bin", "etc", "lib", "lib32", "lib64", "libx32", "opt", "sbin",
    "tmp", "usr", "var", "home", "root", "boot", "dev", "proc",
    "run", "srv", "sys", "mnt", "media", "snap", "cdrom",
    "lost+found",
}

# Regex pour détecter un fichier
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