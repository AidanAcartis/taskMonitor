import re
import shlex
from typing import List

# -------------------------
# Secure scanning
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
    Splits the input into multiple commands if a separator is present.
    Classic separators: |, &&, ;, ||
    """
    # simple regex to detect top-level separators (not inside quotes)
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
    If token = '-xvz', returns ['-x', '-v', '-z'].
    Otherwise, returns [token].
    Do not touch long options like --help.
    """
    if token.startswith("--") or len(token) <= 2 or not token.startswith("-"):
        return [token]
    return [f"-{c}" for c in token[1:]]


# -------------------------
# Contextual Tokenization
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
