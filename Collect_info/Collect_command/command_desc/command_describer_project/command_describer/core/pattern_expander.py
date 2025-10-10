import re
import itertools
from typing import List, Union

# -------------------------
# Placeholder expansion
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