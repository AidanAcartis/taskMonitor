#!/usr/bin/env python3
"""
describe_cmd_full.py

Usage: python3 test_program.py
Then type a command when prompted, for example:
  ls -l /home/user -a
  curl -d '{"name":"bob"}' -H "Content-Type: application/json" http://example.com/users/1234
"""

import json
import re
import shlex
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import itertools

JSON_DIR = Path("dict_json")

# simple type regexes
TYPE_REGEX = {
    "url": re.compile(r"^https?://[^\s]+$", re.IGNORECASE),
    "ip": re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$"),
    "port": re.compile(r"^[1-9][0-9]{0,4}$"),
    "path": re.compile(r"^(/[^/\s]+)+$"),
    "file": re.compile(r"^[^\s]+\.[a-zA-Z0-9]+$"),
    "number": re.compile(r"^\d+$"),
    "string": re.compile(r"^(['\"]).*\1$"),
}


# ---------------------------
# Utilities
# ---------------------------
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


def normalize_token(tok: str) -> str:
    """Normalize token for comparison: strip outer quotes and collapse spaces."""
    s = tok.strip()
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        s = s[1:-1]
    return " ".join(s.split())


# ---------------------------
# Placeholder expansion
# ---------------------------
def extract_placeholders(pattern: str) -> List[str]:
    # non-greedy capture between {{ and }}
    return re.findall(r"\{\{(.*?)\}\}", pattern, flags=re.DOTALL)


def split_top_level_pipes(s: str) -> List[str]:
    """Split on '|' but ignore pipes inside quotes."""
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


def expand_alternatives(pattern: str) -> List[str]:
    """
    Expand placeholders like:
      {{[-d|--data]}} => -d  OR --data  (strip surrounding [])
      {{'Content-Type: application/json'}} => 'Content-Type: application/json' (kept as single option)
      {{GET|POST}} => GET OR POST
    Returns list of expanded pattern strings.
    """
    if not pattern or not isinstance(pattern, str):
        return []
    placeholders = extract_placeholders(pattern)
    if not placeholders:
        return [pattern.strip()]

    # build list of options for each placeholder
    options_list = []
    for ph in placeholders:
        ph = ph.strip()
        # remove surrounding square brackets if present (optional indicator)
        if ph.startswith("[") and ph.endswith("]"):
            core = ph[1:-1].strip()
        else:
            core = ph

        # split alternatives by top-level '|'
        opts = split_top_level_pipes(core)
        # keep exact tokens (including quotes, dashes, etc.)
        opts = [o for o in opts if o != ""]
        if not opts:
            opts = [core]
        options_list.append(opts)

    combinations = list(itertools.product(*options_list))
    expanded = []
    for combo in combinations:
        out = pattern
        # replace placeholders one by one (first occurrence)
        for ph, val in zip(placeholders, combo):
            out = out.replace("{{" + ph + "}}", val, 1)
        expanded.append(" ".join(out.split()))
    return expanded


# ---------------------------
# Tokenization helpers
# ---------------------------
def safe_shlex_split(s: str) -> List[str]:
    """Try shlex.split, fallback to simple split if syntax issues."""
    try:
        return shlex.split(s)
    except ValueError:
        # remove unmatched quotes then split
        s2 = s.replace('"', "").replace("'", "")
        return s2.split()


def tokenize_pattern_to_elements(pattern: str) -> List[str]:
    """
    From an expanded pattern build pattern elements:
      - tokens that start with '-' become 'cmd opt' (e.g. 'curl -d')
      - tokens that don't start with '-' are standalone (args/urls/strings)
    """
    toks = safe_shlex_split(pattern)
    if not toks:
        return []
    cmd = toks[0]
    elems: List[str] = []
    for t in toks[1:]:
        if t.startswith("-"):
            elems.append(f"{cmd} {t}")
        else:
            elems.append(t)
    # if pattern had only the command, we might want the bare cmd as element
    if not any(e.startswith(cmd + " ") for e in elems) and len(toks) == 1:
        elems.insert(0, cmd)
    return elems


def tokenize_input_to_elements(user_input: str) -> List[str]:
    toks = safe_shlex_split(user_input)
    if not toks:
        return []
    cmd = toks[0]
    elems: List[str] = []
    for t in toks[1:]:
        if t.startswith("-"):
            elems.append(f"{cmd} {t}")
        else:
            elems.append(t)
    return elems

def tokenize_input_to_elements_with_main_cmd(user_input: str) -> List[str]:
    """
    Wrapper autour de tokenize_input_to_elements pour ajouter la commande principale
    devant les sous-commandes non-argument (files, path, ip, port, number).
    """
    elems = tokenize_input_to_elements(user_input)
    if not elems:
        return []

    cmd = elems[0].split()[0]  # main command
    result: List[str] = []
    for el in elems:
        el_type = detect_type(el)
        # si ce n'est pas un vrai argument externe, mais pas déjà attaché au cmd
        if el_type not in ("path", "directory", "file", "ip", "port", "number") and not el.startswith(cmd + " "):
            result.append(f"{cmd} {el}")
        else:
            result.append(el)
    return result


# ---------------------------
# Type detection
# ---------------------------
def detect_type(token: str) -> str:
    # cmd+option
    if " " in token and token.split()[1].startswith("-"):
        return "cmdopt"
    for name, rx in TYPE_REGEX.items():
        if rx.match(token):
            if name == "path":
                return "directory"
            if name == "file":
                return "file"
            if name == "number":
                return "number"
            return name
    if token.startswith("-"):
        return "option"
    if TYPE_REGEX["string"].match(token):
        return "string"
    return "arg"


# ---------------------------
# Compare pattern vs input
# ---------------------------
def compare_pattern_vs_input(pattern_elems: List[str], input_elems: List[str]) -> Tuple[int, int]:
    """
    Returns (matches, total) comparing pattern elements to input elements.
    Comparison uses normalized tokens (strip outer quotes).
    For placeholders that look like urls/paths/strings we try type matching.
    """
    matches = 0
    total = len(pattern_elems)
    if total == 0:
        return 0, 0

    # precompute normalized forms & types
    input_norm = [normalize_token(x) for x in input_elems]
    input_types = [detect_type(x) for x in input_elems]

    for p in pattern_elems:
        pn = normalize_token(p)
        # if pattern element is a cmdopt (e.g. 'curl -d')
        if " " in pn and pn.split()[1].startswith("-"):
            # match if exact normalized token appears in input OR long/short equivalence
            if pn in input_norm:
                matches += 1
                continue
            # try partial compare: compare option part ignoring command name
            try:
                _, popt = pn.split(None, 1)
                for ie in input_norm:
                    if " " in ie:
                        _, iopt = ie.split(None, 1)
                        if iopt == popt:
                            matches += 1
                            break
            except Exception:
                pass
        else:
            # pattern element not a cmdopt; try type-based matching
            if re.search(r"https?://", pn, re.IGNORECASE):
                if any(t == "url" for t in input_types):
                    matches += 1
                    continue
            if "/" in pn and not pn.startswith("http"):
                if any(t in ("directory", "file") for t in input_types):
                    matches += 1
                    continue
            # quoted example strings in pattern -> match string/arg in input
            if (pn.startswith("'") and pn.endswith("'")) or (pn.startswith('"') and pn.endswith('"')):
                if any(t in ("string", "arg") for t in input_types):
                    matches += 1
                    continue
            # fallback: exact literal presence among normalized inputs
            if pn in input_norm:
                matches += 1
                continue
    return matches, total


# ---------------------------
# Find best match for main command
# ---------------------------
def find_best_match_for_command(cmdname: str, input_elems: List[str], db: Dict[str, Any]) -> Optional[Tuple[str, str, float]]:
    entries = db.get(cmdname)
    if not entries:
        return None

    best_score = 0.0
    best_entry_desc = None
    best_pattern_str = None

    # keep only command/option elements from input for matching full-pattern command check
    input_cmd_elems = [el for el in input_elems if detect_type(el) in ("cmdopt", "option", "cmd")]
    input_cmd_norm = [normalize_token(x) for x in input_cmd_elems]

    for entry in entries:
        cmd_field_list = []
        if "cmd" in entry and entry["cmd"]:
            cmd_field_list.append(entry["cmd"])
        if "cmds" in entry and isinstance(entry["cmds"], list):
            cmd_field_list.extend([c for c in entry["cmds"] if isinstance(c, str)])

        for cmd_pattern in cmd_field_list:
            for ex in expand_alternatives(cmd_pattern):
                pattern_elems = tokenize_pattern_to_elements(ex)
                # keep only pattern elements that are command/option-like
                pattern_cmd_elems = [pe for pe in pattern_elems if detect_type(pe) in ("cmdopt", "option", "cmd")]
                pattern_cmd_norm = [normalize_token(x) for x in pattern_cmd_elems]

                # full match condition: all input command elements are present (consider normalized compare & equivalence)
                full_ok = True
                for ice in input_cmd_norm:
                    # check direct equality or option-part equality
                    if ice in pattern_cmd_norm:
                        continue
                    # try ignore command name: compare option portion only
                    try:
                        _, iopt = ice.split(None, 1)
                    except ValueError:
                        iopt = ice
                    found = False
                    for pcn in pattern_cmd_norm:
                        try:
                            _, popt = pcn.split(None, 1)
                        except ValueError:
                            popt = pcn
                        if iopt == popt:
                            found = True
                            break
                    if not found:
                        full_ok = False
                        break

                if full_ok and input_cmd_norm:
                    # we have a full match of all input cmd/option elements against this pattern
                    return entry.get("description"), ex, 100.0

                # partial score: how many input command elements are present
                matches = 0
                for ice in input_cmd_norm:
                    if ice in pattern_cmd_norm:
                        matches += 1
                        continue
                    # try option part match
                    try:
                        _, iopt = ice.split(None, 1)
                    except ValueError:
                        iopt = ice
                    for pcn in pattern_cmd_norm:
                        try:
                            _, popt = pcn.split(None, 1)
                        except ValueError:
                            popt = pcn
                        if iopt == popt:
                            matches += 1
                            break
                total = len(input_cmd_norm) if input_cmd_norm else 0
                score = (matches / total * 100) if total > 0 else 0.0
                if score > best_score:
                    best_score = score
                    best_entry_desc = entry.get("description")
                    best_pattern_str = ex

    if best_score > 0:
        return best_entry_desc, best_pattern_str, best_score
    return None


# ---------------------------
# Describe input elements individually
# ---------------------------
def find_description_for_cmdopt(cmdopt: str, db: Dict[str, Any]) -> Optional[str]:
    parts = cmdopt.split(None, 1)
    if len(parts) < 2:
        return None
    base, opt = parts
    entries = db.get(base)
    if not entries:
        return None
    opt_norm = normalize_token(cmdopt)
    for entry in entries:
        cmdlist = []
        if "cmd" in entry and entry["cmd"]:
            cmdlist.append(entry["cmd"])
        if "cmds" in entry:
            cmdlist.extend([c for c in entry["cmds"] if isinstance(c, str)])
        for cp in cmdlist:
            for ex in expand_alternatives(cp):
                pat_elems = tokenize_pattern_to_elements(ex)
                for pe in pat_elems:
                    if normalize_token(pe) == opt_norm:
                        return entry.get("description")
    return None


def describe_input_elements(input_elems: List[str], db: Dict[str, Any]) -> List[str]:
    results = []
    for i, el in enumerate(input_elems, start=1):
        found_desc = None
        el_type = detect_type(el)
        el_norm = normalize_token(el)

        # if element is command/option: try to find matching single-element patterns in DB
        if el_type in ("cmdopt", "option", "cmd"):
            for cmdname, entries in db.items():
                for entry in entries:
                    cmdlist = []
                    if "cmd" in entry and entry["cmd"]:
                        cmdlist.append(entry["cmd"])
                    if "cmds" in entry:
                        cmdlist.extend([c for c in entry["cmds"] if isinstance(c, str)])
                    for cp in cmdlist:
                        for ex in expand_alternatives(cp):
                            pat_elems = tokenize_pattern_to_elements(ex)
                            # only patterns with a single element that match this element
                            if len(pat_elems) == 1 and normalize_token(pat_elems[0]) == el_norm:
                                found_desc = entry.get("description")
                                break
                        if found_desc:
                            break
                    if found_desc:
                        break
                if found_desc:
                    break

        # fallback by type when no DB description found
        if not found_desc:
            if el_type == "directory":
                found_desc = f"Directory '{el}'"
            elif el_type == "file":
                found_desc = f"File '{el}'"
            elif el_type == "url":
                found_desc = f"URL '{el}'"
            elif el_type == "ip":
                found_desc = f"IP address {el}"
            elif el_type == "port":
                found_desc = f"Port {el}"
            elif el_type == "number":
                found_desc = f"Number {el}"
            elif el_type == "string":
                found_desc = f"String {el}"
            elif el_type == "cmdopt":
                maybe = find_description_for_cmdopt(el, db)
                if maybe:
                    found_desc = maybe
                else:
                    found_desc = f"Option {el}"
            else:
                found_desc = f"Argument {el}"

        results.append(f"desc_{i}: {found_desc}")
    return results


# ---------------------------
# Main
# ---------------------------
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
    for i, e in enumerate(input_elems, start=1):
        print(f"  el_{i}: {e}")

    toks = safe_shlex_split(user_input)
    if not toks:
        print("No tokens.")
        return
    main_cmd = toks[0]

    # try full/partial match among command entries
    match = find_best_match_for_command(main_cmd, input_elems, db)
    # only show "full command description" when it's truly 100%
    if match and match[2] == 100.0:
        desc, matched_pattern, _ = match
        print("\nFull command description:")
        print(f"  desc: {desc}  (matched pattern: {matched_pattern})")

    # always produce individual element descriptions (fallbacks included)
    results = describe_input_elements(input_elems, db)
    print("\nDescriptions found:")
    for r in results:
        print(" ", r)


if __name__ == "__main__":
    main()
