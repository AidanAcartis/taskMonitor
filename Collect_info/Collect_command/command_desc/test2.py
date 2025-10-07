#!/usr/bin/env python3
import re
import shlex
from pathlib import Path
from typing import List, Dict, Any, Optional
import itertools
import json

# ==========================================================
# 🔹 1. Répertoire des patterns JSON
# ==========================================================
JSON_DIR = Path("dict_json")  # Met tes fichiers JSON ici


# ==========================================================
# 🔹 2. Parsing sécurisé (ne change pas)
# ==========================================================
def safe_shlex_split(s: str) -> List[str]:
    try:
        return shlex.split(s, posix=False)
    except Exception:
        return s.split()


def is_quoted(tok: str) -> bool:
    return (tok.startswith('"') and tok.endswith('"')) or (tok.startswith("'") and tok.endswith("'"))


def looks_like_option(tok: str) -> bool:
    return tok.startswith("-") and not is_quoted(tok)


def looks_like_subcommand(tok: str) -> bool:
    if is_quoted(tok) or tok.startswith("-"):
        return False
    return bool(re.match(r"^[a-zA-Z]+$", tok))


# ==========================================================
# 🔹 3. Tokenization contextuelle (exacte)
# ==========================================================
def tokenize_input_to_elements(user_input: str) -> List[str]:
    toks = safe_shlex_split(user_input)
    if not toks:
        return []

    cmd = toks[0]
    elems: List[str] = [cmd]  # el_0 = commande principale
    option_attachable = None
    attachable_allowed = True

    for t in toks[1:]:
        if is_quoted(t):
            elems.append(t)
            attachable_allowed = False
            continue
        if looks_like_option(t):
            if option_attachable:
                elems.append(f"{cmd} {option_attachable} {t}")
            else:
                elems.append(f"{cmd} {t}")
            attachable_allowed = False
            continue
        if attachable_allowed and looks_like_subcommand(t):
            option_attachable = t
            elems.append(f"{cmd} {t}")
            attachable_allowed = False
            continue
        elems.append(t)
        attachable_allowed = False

    return elems


# ==========================================================
# 🔹 4. Type detection simple
# ==========================================================
TYPE_REGEX = {
    "url": re.compile(r"^https?://[^\s]+$", re.IGNORECASE),
    "ip": re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$"),
    "port": re.compile(r"^\d+$"),
    "file": re.compile(r"^[^\s]+\.[a-zA-Z0-9]+$"),
    "string": re.compile(r"^(['\"]).*\1$"),
}


def detect_type(token: str, main_cmd: Optional[str] = None) -> str:
    token = token.strip()
    
    if main_cmd and token == main_cmd:
        return "cmd"

    if main_cmd and token.startswith(main_cmd + " "):
        # Si elle contient une option (-x), c’est une commande avec option
        if any(tok.startswith("-") for tok in token.split()[1:]):
            return "cmdopt"
        # Sinon, si c’est une sous-commande attachée à la commande principale
        elif len(token.split()) >= 1:
            return "cmdopt"

    if " " in token and any(tok.startswith("-") for tok in token.split()[1:]):
        return "cmdopt"
    for name, rx in TYPE_REGEX.items():
        if rx.match(token):
            return name
    if token.startswith("-"):
        return "option"
    return "arg"


def normalize_token(tok: str) -> str:
    return " ".join(tok.strip().split())


# ==========================================================
# 🔹 5. JSON utilities
# ==========================================================
def load_all_jsons(json_dir: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for p in sorted(json_dir.glob("*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
                for k, v in d.items():
                    data.setdefault(k, []).extend(v if isinstance(v, list) else [v])
        except Exception as e:
            print(f"Warning: cannot load {p}: {e}")
    return data


# ==========================================================
# 🔹 6. Placeholder expansion
# ==========================================================
def extract_placeholders(pattern: str) -> List[str]:
    return re.findall(r"\{\{(.*?)\}\}", pattern, flags=re.DOTALL)


def split_top_level_pipes(s: str) -> List[str]:
    parts = []
    cur = []
    in_s = None
    for ch in s:
        if ch in ("'", '"'):
            if in_s is None:
                in_s = ch
            elif in_s == ch:
                in_s = None
            cur.append(ch)
        elif ch == "|" and in_s is None:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur).strip())
    return [p for p in parts if p != ""]


def expand_alternatives(pattern) -> List[str]:
    # Si pattern est une liste, on la transforme en string (ou on prend chaque élément séparément)
    if isinstance(pattern, list):
        expanded = []
        for p in pattern:
            expanded.extend(expand_alternatives(p))
        return expanded

    # pattern est maintenant bien un string
    placeholders = extract_placeholders(pattern)
    if not placeholders:
        return [pattern.strip()]

    options_list = []
    for ph in placeholders:
        ph = ph.strip()
        core = ph[1:-1].strip() if ph.startswith("[") and ph.endswith("]") else ph
        opts = split_top_level_pipes(core)
        opts = [o for o in opts if o != ""]
        if not opts:
            opts = [core]
        options_list.append(opts)

    combos = list(itertools.product(*options_list))
    expanded = []
    for combo in combos:
        out = pattern
        for ph, val in zip(placeholders, combo):
            out = out.replace("{{" + ph + "}}", val, 1)
        expanded.append(" ".join(out.split()))
    return expanded

# ==========================================================
# 🔹 7. Description matching (nouvelle technique avec debug)
# ==========================================================
def describe_input_elements(input_elems: List[str], db: Dict[str, Any]) -> List[str]:
    results = []

    if not input_elems:
        return results

    cmdname = input_elems[0]
    entries = db.get(cmdname, [])

    # Normalisation des input elems
    input_norm_elems = [normalize_token(el) for el in input_elems]

    # Détecte types des elements
    input_types = [detect_type(el, main_cmd=cmdname) for el in input_elems]

    # ✅ On va décider description pour les tokens de type commande
    matched_entry = None
    matched_cmd_tokens = []

    # On parcourt toutes les entrées possibles de la DB
    for entry_idx, entry in enumerate(entries):
        print(f"\n🔍 Checking DB entry {entry_idx}: description='{entry.get('description')}'")
        cmdlist = []
        if "cmd" in entry and entry["cmd"]:
            cmdlist.append(entry["cmd"])
        if "cmds" in entry:
            cmdlist.extend([c for c in entry["cmds"] if isinstance(c, str)])

        for cp_idx, cp in enumerate(cmdlist):
            for ex_idx, ex in enumerate(expand_alternatives(cp)):
                pat_elems = tokenize_input_to_elements(ex)
                pat_elems_norm = [normalize_token(pe) for pe in pat_elems]
                pat_types = [detect_type(pe, main_cmd=cmdname) for pe in pat_elems]

                # Sélectionne uniquement les tokens de type cmd/cmdopt
                pat_cmd_indices = [i for i, t in enumerate(pat_types) if t in ("cmd", "cmdopt")]

                print(f"   → Pattern '{ex}' tokens: {pat_elems_norm}")
                print(f"     cmd indices: {pat_cmd_indices}")

                # Vérifie correspondance séquentielle
                match = True
                for idx, pat_idx in enumerate(pat_cmd_indices):
                    if idx >= len(input_norm_elems):
                        match = False
                        print(f"       ❌ Input shorter than pattern, break")
                        break
                    print(f"       Comparing input '{input_norm_elems[idx]}' <-> pattern '{pat_elems_norm[pat_idx]}'")
                    if input_norm_elems[idx] != pat_elems_norm[pat_idx]:
                        match = False
                        print(f"       ❌ Not matching")
                        break
                    else:
                        print(f"       ✅ Matching")
                if match:
                    print(f"     ✅ FULL MATCH with this pattern")
                    matched_entry = entry
                    matched_cmd_tokens = pat_cmd_indices
                    break
            if matched_entry:
                break
        if matched_entry:
            break

    # Construction des descriptions pour chaque el_i
    for i, el in enumerate(input_elems):
        el_type = input_types[i]
        el_norm = input_norm_elems[i]

        if matched_entry and i in matched_cmd_tokens:
            desc = matched_entry.get("description")
            print(f"el_{i}: '{el}' → matched command → description: {desc}")
        else:
            # fallback type descriptions
            if el_type == "url":
                desc = f"URL '{el}'"
            elif el_type == "file":
                desc = f"File '{el}'"
            elif el_type == "string":
                desc = f"String {el}"
            elif el_type == "cmdopt":
                desc = f"Option {el}"
            else:
                desc = f"Argument {el}"
            print(f"el_{i}: '{el}' → fallback type '{el_type}' → description: {desc}")

        results.append(f"desc_{i}: {desc}")

    return results


# ==========================================================
# 🔹 8. Main
# ==========================================================
def main():
    db = load_all_jsons(JSON_DIR)
    if not db:
        print(f"No JSON files loaded from {JSON_DIR}")
        return

    user_input = input("Enter command: ").strip()
    if not user_input:
        print("Empty input.")
        return

    input_elems = tokenize_input_to_elements(user_input)
    print("\nElement analysis:")
    for i, e in enumerate(input_elems):
        print(f"  el_{i}: {e}")

    # individual element descriptions
    results = describe_input_elements(input_elems, db)
    print("\nDescriptions found:")
    for r in results:
        print(" ", r)


if __name__ == "__main__":
    main()
