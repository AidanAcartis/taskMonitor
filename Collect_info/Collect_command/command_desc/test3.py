#!/usr/bin/env python3
import re
import shlex
from pathlib import Path
from typing import List, Dict, Any, Optional
import itertools
import json

JSON_DIR = Path("dict_json")  # Répertoire JSON

# -------------------------
# 1. Parsing sécurisé
# -------------------------
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

def split_input_by_commands(user_input: str) -> List[str]:
    """
    Sépare l'input en plusieurs commandes si un séparateur est présent.
    Séparateurs classiques: |, &&, ;, || 
    """
    # regex simple pour détecter les séparateurs au top-level (pas à l'intérieur de quotes)
    parts = []
    cur = []
    in_s = None
    i = 0
    while i < len(user_input):
        ch = user_input[i]
        if ch in ("'", '"'):
            if in_s is None:
                in_s = ch
            elif in_s == ch:
                in_s = None
            cur.append(ch)
        elif in_s is None and user_input[i:i+2] in ("&&", "||"):
            parts.append("".join(cur).strip())
            cur = []
            i += 1  # skip next char of &&
        elif in_s is None and ch in ("|", ";"):
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    if cur:
        parts.append("".join(cur).strip())
    return [p for p in parts if p != ""]

def split_combined_flags(token: str) -> List[str]:
    """
    Si token = '-xvz', renvoie ['-x', '-v', '-z'].
    Sinon renvoie [token].
    Ne touche pas aux options longues comme --help.
    """
    if token.startswith("--") or len(token) <= 2 or not token.startswith("-"):
        return [token]
    return [f"-{c}" for c in token[1:]]

def describe_script_input(token: str) -> Optional[str]:
    """
    If the token is a local script like './script.sh', return a description.
    """
    if TYPE_REGEX["script"].match(token):
        return f"Run the script '{token}'"
    return None

def repair_combined_flags_in_command(cmd: str) -> str:
    """
    Remplace les flags combinés dans une commande par leur version séparée.
    Ex: 'tar -xvz /tmp' -> 'tar -x -v -z /tmp'
    ⚠️ Nmap et OpenSSL sont épargnés pour ne pas casser leurs options/sous-commandes.
    """
    tokens = safe_shlex_split(cmd)
    repaired_tokens = []

    # Commandes pour lesquelles on ne splitte pas les flags (case-insensitive)
    SKIP_SPLIT_CMDS = {"nmap", "openssl", "ntlmrelayx"}

    # Repérer la commande principale (si présente)
    main_cmd = tokens[0] if tokens else ""
    is_skip_cmd = main_cmd.lower() in SKIP_SPLIT_CMDS

    for t in tokens:
        if is_skip_cmd:
            # Ne rien splitter pour les commandes listées, juste ajouter le token
            repaired_tokens.append(t)
        else:
            repaired_tokens.extend(split_combined_flags(t))

    return " ".join(repaired_tokens)


# -------------------------
# 2. Tokenization contextuelle
# -------------------------
def tokenize_input_to_elements(user_input: str) -> List[str]:
    toks = safe_shlex_split(user_input)

    if not toks:
        return []

    cmd = toks[0]
    elems: List[str] = [cmd]
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

# -------------------------
# 3. Type detection simple
# -------------------------
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
SERVER = ["nginx", "apache"]
GATEWAY = ["gw"]
TCPDUMP_OPTIONS = {
    "-i": "network_interface",
    "-w": "file"
}
HYDRA_OPTIONS = {
    "-l": "username"
}
ARG_TYPE = ["root", "ssh", "port", "verbose", "show", "default", "get"]
INTERFACE_CMDS = ["ethtool", "ip", "ifconfig", "tcpdump"]
TYPE_REGEX = {
    # Chemins et fichiers
    "folder": re.compile(r"^(/|~)[\w\-/]+/?$"),
    "file": re.compile(r"^(?:/[\w\-/]+|\.?/[\w\-/]+|[\w\-.]+)\.[\w]+$"),
    "device": re.compile(r"^/dev/[^\s]+$"),
    "envfile": re.compile(r"^(?:\.|/)?[\w\.-]+\.(?:env|conf|ini)$"),
    "script": re.compile(r"^\./[\w\.-]+\.sh$"),
    "archive": re.compile(r"^[\w\.-]+\.(?:tar|gz|zip|bz2|xz)$"),

    # Réseau
    "ip": re.compile(
        r"^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
        r"\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
        r"\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
        r"\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)$"
    ),
    "ipv6": re.compile(r"^([0-9a-fA-F]{0,4}:){1,7}[0-9a-fA-F]{0,4}$"),
    "port": re.compile(r"^\d{1,5}$"),
    "url": re.compile(r"^https?://[^\s]+$", re.IGNORECASE),
    "remote_target": re.compile(r"^[\w.-]+@[\w\.-]+(:/[\w\./-]*)?$"),
    "http_method": re.compile(r"^(?:" + "|".join(HTTP_METHODS) + r")$", re.IGNORECASE),
    "server": re.compile(r"^(?:" + "|".join(SERVER) + r")$", re.IGNORECASE),
    "domain": re.compile(
            r"^(?:[a-zA-Z0-9][a-zA-Z0-9-]*\.)+"  # sous-domaines
            r"(com|net|org|info|biz|name|xyz|online|site|tech|app|"  # gTLD modernes
            r"fr|us|uk|de|jp|io|"                                      # ccTLD
            r"edu|gov|mil)"                                           # spécial/sponsorisé
            r"(?::\d{1,5})?$"                                         # port optionnel
        ),
    "dns_type": re.compile(r"^(A|AAAA|MX|CNAME|TXT|NS|SOA|PTR|SRV|CAA)$", re.IGNORECASE),
    "port_range": re.compile(r"^\d{1,5}-\d{1,5}$"),
    # cidr IPv4 simple ex: 192.168.1.0/24
    "cidr": re.compile(r"^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
                       r"(?:\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}"
                       r"/(?:[0-9]|[12]\d|3[0-2])$"),
    "arg_type": re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,19}$"),

    # Données
    "json": re.compile(r"^\{.*\}$"),
    "string": re.compile(r"^(['\"]).*\1$"),

    # Nombres et unités
    "number": re.compile(r"^-?\d+(\.\d+)?$"),
}

# -------------------------------
# 🔹 Dictionnaire de descriptions
# -------------------------------
TYPE_DESCRIPTION = {
    "file": "File",
    "folder": "Folder",
    "device": "Device",
    "envfile": "Environment file",
    "script": "Script",
    "archive": "Archive",
    "ip": "IP address",
    "ipv6": "IPv6 address",
    "port": "Port number",
    "url": "URL",
    "json": "JSON",
    "string": "String",
    "number": "Number",
    "remote_target": "Remote target",
    "arg": "Argument",
    "server": "Server",
    "http_method": "Http method",
    "domain": "Website / Domain",
    "dns_type": "DNS record type",
    "network_interface": "Network interface",
    "port_range": "Port range",
    "cidr": "Network (CIDR)",
    "gateway": "Gateway",
    "username": "Username",
    "python_module": "Python module"
}

def detect_type(token: str, main_cmd: Optional[str] = None, prev_token: Optional[str] = None, index: Optional[int] = None) -> str:
    token = token.strip()
    if not token:
        return "arg"

    if index == 0:
        return "cmd"

    # Commande principale
    if main_cmd and token == main_cmd:
        return "cmd"
    if main_cmd and token.startswith(main_cmd + " "):
        if any(tok.startswith("-") for tok in token.split()[1:]):
            return "cmdopt"
        elif len(token.split()) >= 1:
            return "cmdopt"
    if " " in token and any(tok.startswith("-") for tok in token.split()[1:]):
        return "cmdopt"
    
    prev_last = None
    if prev_token:
        prev_last = prev_token.strip().split()[-1]
    
    # String / JSON / URL
    if is_quoted(token):
        inner = token[1:-1]
        # JSON check
        if TYPE_REGEX["json"].match(inner):
            return "json"
        # URL check
        if TYPE_REGEX["url"].match(inner):
            return "url"
        return "string"
    
    # if token in ARG_TYPE:
    #     return "arg"
    if main_cmd == "python" and prev_token == "-m":
        return "python_module"
    
    # Remote target
    if TYPE_REGEX["remote_target"].match(token):
        return "remote_target"
    
    if TYPE_REGEX["domain"].match(token):
        return "domain"
    
    # IP, IPv6, URL
    for name in ["ip", "ipv6", "url"]:
        if TYPE_REGEX[name].match(token):
            return name
    
     # CIDR (ex: 192.168.1.0/24)
    if TYPE_REGEX["cidr"].match(token):
        return "cidr"

    # Port range (ex: 1-1024)
    if TYPE_REGEX["port_range"].match(token):
        # valider les bornes numériquement (optionnel mais recommandé)
        a, b = token.split("-", 1)
        try:
            ai = int(a); bi = int(b)
            if 0 <= ai <= 65535 and 0 <= bi <= 65535:
                return "port_range"
        except Exception:
            pass
    
    # -------------------------------
    # 🎯 Détection contextuelle Port vs Nombre
    # -------------------------------
    if TYPE_REGEX["port"].match(token):
        num = int(token)
        # Si précédé d'une option de port explicite
        if prev_token in ("-p", "--port", "--listen-port", "--connect-port", "port", "http.server", "redis-cli -p"):
            return "port"
        # Si c’est un port probable (dans une commande réseau)
        if main_cmd in ("ssh", "nc", "nmap", "telnet", "curl", "ftp") and 1 <= num <= 65535:
            return "port"
        # Sinon, c’est probablement un nombre
        return "number"

    # Nombres généraux
    if TYPE_REGEX["number"].match(token):
        return "number"
    
    if main_cmd == "tcpdump" and prev_token:
        last = prev_token.split()[-1]
        if last == "port":
            return "port" if TYPE_REGEX["port"].match(token) else "arg"

    # TCPDUMP contextual detection
    if main_cmd == "tcpdump" and prev_token:
        last = prev_token.split()[-1]
        if last in TCPDUMP_OPTIONS:
            return TCPDUMP_OPTIONS[last]
        
    if token.lower() in GATEWAY:
                return "gateway"
    
    if main_cmd == "hydra" and prev_last:
                if prev_last in HYDRA_OPTIONS:
                    return HYDRA_OPTIONS[prev_last]
                
    if token.upper() in HTTP_METHODS:
        return "http_method"
    
    if TYPE_REGEX["domain"].match(token):
        return "domain"

    if main_cmd == "python" and prev_token and prev_token.strip().endswith("-m"):
        return "python_module"
    
    if token.lower() in SERVER:
                return "server"

    if TYPE_REGEX["arg_type"].match(token):
        # But be careful: don't treat things that look like domain/ip/url as arg
        if not (TYPE_REGEX["domain"].match(token) or TYPE_REGEX["ip"].match(token) or TYPE_REGEX["url"].match(token) or TYPE_REGEX["dns_type"].match(token)):
            return "arg"

    # Fichiers, dossiers...
    for name in ["folder", "file", "device", "envfile", "script", "archive"]:
        if TYPE_REGEX[name].match(token):
            if TYPE_REGEX[name].match(token) or token == ".":
                return "folder" if token == "." else name
            # if main_cmd and "." in token:
            #     return "domain"  # ou "Website / Domain"
            # #in ("dig", "ping", "host", "openssl")

            # if main_cmd and token.upper() in HTTP_METHODS:
            #     return "http_method"
            # #in ("curl", "http", "wget")
            # Python module detection
            
            if main_cmd == "host" and TYPE_REGEX["dns_type"].match(token):
                return "dns_type"
            
            if main_cmd == "tcpdump" and prev_token in TCPDUMP_OPTIONS:
                return TCPDUMP_OPTIONS[prev_token]
            
            if main_cmd == "ethtool" and prev_token in INTERFACE_CMDS:
                return "network_interface"

            # si c’est "nginx" ou "apache", on renvoie "server" show
            # if token.lower() in SERVER:
            #     return "server"
            
            return name


    if token.startswith("-"):
        return "option"

    return "arg"


def normalize_token(tok: str) -> str:
    return " ".join(tok.strip().split())

# -------------------------
# 4. JSON utils
# -------------------------
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

# -------------------------
# 5. Placeholder expansion
# -------------------------
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
    if isinstance(pattern, list):
        expanded = []
        for p in pattern:
            expanded.extend(expand_alternatives(p))
        return expanded
    placeholders = extract_placeholders(pattern)
    if not placeholders:
        return [pattern.strip()]
    options_list = []
    for ph in placeholders:
        ph = ph.strip()
        core = ph[1:-1].strip() if ph.startswith("[") and ph.endswith("]") else ph
        opts = split_top_level_pipes(core)
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

def norm_cmd_token_for_match(s: str) -> str:
    """
    Normalize a command-type token for robust matching:
    - collapse multiple spaces
    - for options with =value, replace value with ={{}} so --wordlist=rockyou -> --wordlist={{}}
    """
    s = " ".join(s.split())
    # replace any =value occurrence within a token with ={{}} (first occurrence)
    s = re.sub(r'(=\S+)', '={{}}', s, count=1)
    return s


# -------------------------
# 6. Description matching
# -------------------------

def describe_input_elements(input_elems: List[str], db: Dict[str, Any]) -> List[str]:
    results: List[str] = []
    if not input_elems:
        return results

    cmdname = input_elems[0]
    entries = db.get(cmdname, [])

    # Normalisation + types globaux
    input_norm_elems = [normalize_token(el) for el in input_elems]
    input_types = [detect_type(el, main_cmd=cmdname, index=i) for i, el in enumerate(input_elems)]

    # indices et valeurs des tokens de type commande dans l'input
    input_cmd_indices = [i for i, t in enumerate(input_types) if t in ("cmd", "cmdopt")]
    input_cmd_norms = [input_norm_elems[i] for i in input_cmd_indices]

    matched_entry: Optional[Dict[str, Any]] = None
    matched_input_cmd_indices: List[int] = []

    # print("\n=== FULL DESCRIPTION CHECK (strict: cmd/cmdopt sequence equality) ===")
    # print(" Input command-type tokens (indices -> token):",
    #       [(i, input_norm_elems[i]) for i in input_cmd_indices])

    # Full match strict : comparer la séquence des tokens de type commande
    for entry_idx, entry in enumerate(entries):
        # print(f"\nChecking DB entry {entry_idx}: description='{entry.get('description')}'")
        cmdlist = []
        if "cmd" in entry:
            cmdlist.append(entry["cmd"])
        if "cmds" in entry:
            cmdlist.extend(entry["cmds"])

        for cp in cmdlist:
            for ex in expand_alternatives(cp):
                pat_elems = tokenize_input_to_elements(ex)
                pat_elems_norm = [normalize_token(pe) for pe in pat_elems]
                pat_types = [detect_type(pe, main_cmd=cmdname, index=k) for k, pe in enumerate(pat_elems)]
                # on ne garde que les tokens de type commande du pattern
                pat_cmd_indices = [i for i, t in enumerate(pat_types) if t in ("cmd", "cmdopt")]
                pat_cmd_norms = [pat_elems_norm[i] for i in pat_cmd_indices]

                # print(f" Pattern: '{ex}'") 
                # print(f"  Pattern tokens: {pat_elems_norm}")
                # print(f"  Pattern command-type tokens (indices -> token):",
                #       [(i, pat_elems_norm[i]) for i in pat_cmd_indices])

                # Strict full match: la sequence des tokens de type commande doit être exactement identique
                # (même longueur et mêmes éléments dans le même ordre)
                # if pat_cmd_norms and pat_cmd_norms == input_cmd_norms:
                if pat_cmd_norms and [norm_cmd_token_for_match(x) for x in pat_cmd_norms] == [norm_cmd_token_for_match(x) for x in input_cmd_norms]:

                    # print("  ✅ FULL MATCH (command-type sequences are exactly equal)")
                    matched_entry = entry
                    matched_input_cmd_indices = input_cmd_indices.copy()
                    break
                # else:
                #     print("  ❌ Not a full match (command-type sequences differ)")

            if matched_entry:
                break
        if matched_entry:
            break

    # si full match, on applique la description sur les éléments de type commande correspondants
    if matched_entry:
        # print("\n=== FULL DESCRIPTION APPLIED ===")
        # desc_full = matched_entry.get("description", "No description")
        # for i, el in enumerate(input_elems):
        #     prev_token = input_elems[i - 1] if i > 0 else None
        #     el_type = detect_type(el, cmdname, prev_token, index=i)

        #     if i in matched_input_cmd_indices:
        #         results.append(f"desc_{i}: {desc_full}")
        #     else:
        #         desc_label = TYPE_DESCRIPTION.get(el_type, "Argument")
        #         desc = f"{desc_label} '{el}'"
        #         results.append(f"desc_{i}: {desc}")
        #         # print(f" el_{i}: '{el}' -> fallback type '{el_type}' -> description: {desc}")
        # return results
        print("\n=== FULL DESCRIPTION APPLIED ===")
        desc_full = matched_entry.get("description", "No description")
        results_dict = {}

        for i, el in enumerate(input_elems):
            prev_token = input_elems[i - 1] if i > 0 else None
            el_type = detect_type(el, cmdname, prev_token, index=i)

            # description principale
            if i in matched_input_cmd_indices:
                results_dict["desc_cmd"] = desc_full
            else:
                desc_label = TYPE_DESCRIPTION.get(el_type, "Argument")
                results_dict[f"desc_arg_{i}"] = f"{desc_label} '{el}'"

        # affichage
        # print("Descriptions found:")
        # for k, v in results_dict.items():
        #     print(f"  {k}: {v}")

        # retour optionnel si tu veux l'utiliser ailleurs
        return [f"{k}: {v}" for k, v in results_dict.items()]


    # Sinon -> DESCRIPTION SEQUENTIELLE (retokenize each el_i and try to match)
    print("\n=== DESCRIPTION SEQUENTIELLE (retokenized per element) ===")
    for i, el in enumerate(input_elems):
        print(f"\nWorking on el_{i}: '{el}'")

        # Special case: local script
        script_desc = describe_script_input(el)
        if script_desc:
            results.append(f"desc_{i}: {script_desc}")
            continue

        if i == 0:
            results.append(f"desc_{i}: Command '{el}'")
            continue

        # retokenize this element alone
        sub_inputs = tokenize_input_to_elements(el)
        sub_norms = [normalize_token(s) for s in sub_inputs]
        sub_types = [detect_type(s, main_cmd=cmdname, index=j) for j, s in enumerate(sub_inputs)]
        sub_cmd_indices = [j for j, t in enumerate(sub_types) if t in ("cmd", "cmdopt")]
        sub_cmd_norms = [sub_norms[j] for j in sub_cmd_indices]

        # print("  sub tokens:", sub_norms)
        # print("  sub command-type tokens:", sub_cmd_norms)

        matched_sub_desc: Optional[str] = None

        # si cet element n'a aucun token de type commande -> fallback direct
        if not sub_cmd_norms:
            # print("  No command-type token inside this element -> fallback by type")
            matched_sub_desc = None
        else:
            # On cherche une entrée DB qui correspond au sous-input
            # Règle pratique (évite faux-positifs):
            #  - si sub_cmd_norms a longueur 1 (ex: "curl"), on n'accepte une correspondance
            #    que si le pattern a exactement le même nombre de tokens (i.e. pattern court)
            #    -> évite que "curl" match "curl https://..." (pattern complet).
            #  - si sub_cmd_norms a longueur >= 2, on cherche l'égalité exacte entre
            #    sub_cmd_norms et pat_cmd_norms.
            for entry_idx, entry in enumerate(entries):
                cmdlist = []
                if "cmd" in entry: cmdlist.append(entry["cmd"])
                if "cmds" in entry: cmdlist.extend(entry["cmds"])

                for cp in cmdlist:
                    for ex in expand_alternatives(cp):
                        pat_elems = tokenize_input_to_elements(ex)
                        pat_elems_norm = [normalize_token(pe) for pe in pat_elems]
                        pat_types = [detect_type(pe, main_cmd=cmdname, index=k) for k, pe in enumerate(pat_elems)]
                        pat_cmd_indices = [k for k, t in enumerate(pat_types) if t in ("cmd", "cmdopt")]
                        pat_cmd_norms = [pat_elems_norm[k] for k in pat_cmd_indices]

                        # debug
                        # print(f"    consider pattern '{ex}' -> pat_cmd_norms={pat_cmd_norms}")

                        if not pat_cmd_norms:
                            continue

                        # # règle : si sub length == 1, n'accepter que si pattern n'a qu'1 token total
                        # if len(sub_cmd_norms) == 1:
                        #     if pat_cmd_norms == sub_cmd_norms and len(pat_elems_norm) == 1:
                        #         matched_sub_desc = entry.get("description")

                        #         # print(f"   -> matched (single-token exact short pattern): '{ex}'")
                        #         break
                        # rule: handle the single-token sub-input case more robustly
                        if len(sub_cmd_norms) == 1:
                            # normalize both sides to ignore concrete values after '='
                            sub_normed = [norm_cmd_token_for_match(x) for x in sub_cmd_norms]
                            pat_normed = [norm_cmd_token_for_match(x) for x in pat_cmd_norms]
                            if pat_normed == sub_normed:
                                matched_sub_desc = entry.get("description")
                                break

                        else:
                            # pour multi-token sub-input, on exige égalité exacte des command-type tokens
                            if pat_cmd_norms == sub_cmd_norms:
                                matched_sub_desc = entry.get("description")
                                # print(f"   -> matched (multi-token): '{ex}'")
                                break
                    if matched_sub_desc:
                        break
                if matched_sub_desc:
                    break

        # assign description (matched_sub_desc ou fallback)
        if matched_sub_desc:
            desc = matched_sub_desc
        else:
            prev_token = input_elems[i - 1] if i > 0 else None
            el_type = detect_type(el, cmdname, prev_token, index=i)
            desc_label = TYPE_DESCRIPTION.get(el_type, "Argument")
            desc = f"{desc_label} '{el}'"


            # print(f" el_{i}: '{el}' -> fallback type '{el_type}' -> description: {desc}")

        results.append(f"desc_{i}: {desc}")

    return results

# -------------------------
# 7. Main
# -------------------------
def main():
    db = load_all_jsons(JSON_DIR)
    if not db:
        print(f"No JSON files loaded from {JSON_DIR}")
        return

    user_input = input("Enter command: ").strip()
    if not user_input:
        print("Empty input.")
        return
    
    # ----------------------------
    # Check for sudo prefix
    # ----------------------------
    has_sudo = False
    if user_input.startswith("sudo "):
        has_sudo = True
        user_input = user_input[5:].strip()  # remove 'sudo ' from the input

    # Séparer l'input en plusieurs commandes
    commands = split_input_by_commands(user_input)

    # Réparer les flags combinés dans chaque commande
    commands = [repair_combined_flags_in_command(c) for c in commands]

    for idx, cmd in enumerate(commands):
        print(f"\n=== Command {idx+1} ===")
        input_elems = tokenize_input_to_elements(cmd)
        print("Element analysis:")
        for i, e in enumerate(input_elems):
            print(f"  el_{i}: {e}")
        results = describe_input_elements(input_elems, db)  # <-- toujours appelé

        if has_sudo and results:
            results[0] = f"with sudo privilege: {results[0]}"

        print("Descriptions found:")
        for r in results:
            print(" ", r)


if __name__ == "__main__":
    main()
