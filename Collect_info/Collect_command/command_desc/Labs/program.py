#!/usr/bin/env python3
import re
import shlex
from typing import List

# ==========================================================
# 🔹 1. Parsing sécurisé
# ==========================================================
def safe_shlex_split(s: str) -> List[str]:
    try:
        return shlex.split(s, posix=False)
    except Exception:
        return s.split()

# ==========================================================
# 🔹 2. Types génériques
# ==========================================================
def is_special_token(tok: str) -> bool:
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", tok):
        return True
    if re.match(r"^\d+$", tok):
        return True
    if re.match(r"^[\w,\s-]+\.[A-Za-z0-9]{1,4}$", tok):
        return True
    if tok.startswith("/") or tok.startswith("./") or tok.startswith("../"):
        return True
    if re.match(r"https?://", tok):
        return True
    return False

def is_quoted(tok: str) -> bool:
    return (tok.startswith('"') and tok.endswith('"')) or (tok.startswith("'") and tok.endswith("'"))

def looks_like_option(tok: str) -> bool:
    return tok.startswith("-") and not is_special_token(tok) and not is_quoted(tok)

def looks_like_subcommand(tok: str) -> bool:
    # Mot alphabétique simple, pas spécial et pas option
    if is_special_token(tok) or is_quoted(tok) or tok.startswith("-"):
        return False
    return bool(re.match(r"^[a-zA-Z]+$", tok))

# ==========================================================
# 🔹 3. Tokenisation contextuelle
# ==========================================================
def tokenize_input_to_elements(user_input: str) -> List[str]:
    toks = safe_shlex_split(user_input)
    if not toks:
        return []

    cmd = toks[0]
    elems: List[str] = []

    # Ajouter el_0 = commande principale
    elems.append(cmd)

    option_attachable = None  # la seule sous-commande alphabétique qui peut être attachée
    attachable_allowed = True # true seulement pour le premier token alphabétique après cmd

    for i, t in enumerate(toks[1:], start=1):
        # Token entre guillemets
        if is_quoted(t):
            elems.append(t)
            attachable_allowed = False
            continue

        # Option - ou -- => attachée à cmd + option attachable si elle existe
        if looks_like_option(t):
            if option_attachable:
                elems.append(f"{cmd} {option_attachable} {t}")
            else:
                elems.append(f"{cmd} {t}")
            attachable_allowed = False
            continue

        # Sous-commande alphabétique attachable uniquement si elle est avant toute option
        if attachable_allowed and looks_like_subcommand(t):
            option_attachable = t
            elems.append(f"{cmd} {t}")
            attachable_allowed = False
            continue

        # Tout autre token => argument simple
        elems.append(t)
        attachable_allowed = False

    return elems

# ==========================================================
# 🔹 4. Affichage simulé
# ==========================================================
def describe_elements(elems: List[str]):
    print("\nElement analysis:")
    for i, e in enumerate(elems):
        print(f"  el_{i}: {e}")

    print("\nDescriptions found:")
    for i, e in enumerate(elems):
        if is_quoted(e):
            print(f"  desc_{i}: Comment / Literal {e}")
        else:
            print(f"  desc_{i}: Argument {e}")

# ==========================================================
# 🔹 5. Programme principal
# ==========================================================
if __name__ == "__main__":
    user_input = input("Enter command: ").strip()
    if not user_input:
        print("No input provided.")
    else:
        elems = tokenize_input_to_elements(user_input)
        describe_elements(elems)
