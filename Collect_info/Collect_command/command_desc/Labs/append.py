#!/usr/bin/env python3
"""
Automatisation : pour chaque commande parent dans les JSON (dict_json/*.json),
lancer `cmd --help`, parser les options et les merger comme enfants sous la clé command.

Usage:
  python3 enrich_tldr_with_options.py
"""

import os
import json
import subprocess
import re
import shutil
from glob import glob

# CONFIG
JSON_DIR = os.path.expanduser("./dict_json")   # dossier contenant common.json, linux.json, ...
BACKUP_DIR = os.path.expanduser("./dict_json_backup")
TIMEOUT = 4  # secondes pour exécuter `cmd --help`
VERBOSE = True

# heuristiques pour deviner si une option prend un argument (mot-clés dans la description)
ARG_KEYWORDS = [
    "file", "path", "string", "name", "id", "pid", "user", "seconds", "count",
    "number", "dir", "directory", "host", "address", "pattern", "timeout", "port",
]

# Regex : détecter une ligne d'option (commence par espaces + -)
RE_OPTION_LINE = re.compile(r'^\s+(?:-{1,2}\S[^\n]*)$')

def run_help(cmd):
    """Try `cmd --help` then `cmd -h`. Return combined output (stdout+stderr) or None."""
    for opt in ("--help", "-h"):
        try:
            p = subprocess.run([cmd, opt], capture_output=True, text=True, timeout=TIMEOUT)
        except FileNotFoundError:
            return None
        except Exception:
            continue
        out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
        out = out.strip()
        if out:
            return out
    return None

def extract_option_lines(help_text):
    """Return list of continuous blocks (strings) that represent option lines.
    We gather lines that start with '-' (possibly wrapped) and join wrapped lines that start with whitespace.
    """
    lines = help_text.splitlines()
    opt_blocks = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if RE_OPTION_LINE.match(ln):
            # Start a block - gather this line and subsequent indented continuation lines
            block_lines = [ln.rstrip()]
            j = i + 1
            while j < len(lines) and (lines[j].startswith('    ') or lines[j].startswith('\t')):
                block_lines.append(lines[j].strip())
                j += 1
            opt_blocks.append(" ".join(block_lines).strip())
            i = j
        else:
            i += 1
    return opt_blocks

def split_left_desc(block):
    """
    Split a block into left (option tokens) and description by finding at least two spaces boundary.
    Fallback: split at ' - ' or first occurrence of '  ' (two spaces).
    """
    parts = re.split(r'\s{2,}', block, maxsplit=1)
    if len(parts) == 2:
        left, desc = parts[0].strip(), parts[1].strip()
    else:
        # fallback: try split by ' - ' or ':' then remainder
        m = re.match(r'^(.+?)\s+-\s+(.*)$', block)
        if m:
            left, desc = m.group(1).strip(), m.group(2).strip()
        else:
            # fallback splitting by first occurrence of '  ' or by first ' - ' else whole line
            parts2 = re.split(r'\s-\s', block, maxsplit=1)
            if len(parts2) == 2:
                left, desc = parts2[0].strip(), parts2[1].strip()
            else:
                left, desc = block.strip(), ""
    return left, desc

def extract_option_tokens(left_part):
    """
    From left part like "-d, --delimiter <string>" or "-a --all" extract option tokens ['-d','--delimiter'].
    """
    # remove surrounding parentheses
    left = left_part.strip().strip('()')
    # split by comma or spaces but keep tokens starting with '-'
    tokens = re.split(r'[,\s]+', left)
    opts = [t for t in tokens if t.startswith('-')]
    # normalize tokens (remove trailing punctuation)
    opts = [re.sub(r'[,:;]$', '', t) for t in opts]
    return opts

def needs_argument(desc, opts):
    """Heuristic: if long option present or description contains keyword, assume needs arg."""
    # if any token contains '=' or is a long option, assume arg likely
    if any('=' in o for o in opts):
        return True
    if any(o.startswith('--') for o in opts):
        # long options often take args but not always; check description for keywords
        if any(k in desc.lower() for k in ARG_KEYWORDS):
            return True
        # fallback: long option suggests argument more likely
        return True
    # short option may take arg if description contains keyword
    if any(k in desc.lower() for k in ARG_KEYWORDS):
        return True
    return False

def choose_placeholder_from_desc(desc):
    desc_lower = desc.lower()
    for k in ARG_KEYWORDS:
        if k in desc_lower:
            # map some keywords to nicer placeholders
            if k in ("file", "path", "dir", "directory"):
                return "<path>"
            if k in ("pid","id","number","count","port"):
                return "<id>"
            if k in ("string","name","host","address","pattern"):
                return "<string>"
            if k in ("user","username"):
                return "<user>"
            if k in ("seconds","timeout"):
                return "<seconds>"
            if k == "port":
                return "<port>"
    return "<arg>"

def build_variants(command_name, opts, desc):
    """
    Given command name and option tokens list, return plausible command variants.
    e.g. opts=['-d','--delimiter'] -> ["pgrep -d <string>", "pgrep --delimiter <string>"]
    """
    variants = []
    arg_needed = needs_argument(desc, opts)
    placeholder = choose_placeholder_from_desc(desc) if arg_needed else ""
    for o in opts:
        if arg_needed:
            variants.append(f"{command_name} {o} {placeholder}".strip())
        else:
            variants.append(f"{command_name} {o}")
    # deduplicate preserving order
    seen = set(); out=[]
    for v in variants:
        if v not in seen:
            seen.add(v); out.append(v)
    return out

def merge_options_into_data(data, cmd_name, options_parsed):
    """
    Merge parsed options (list of tuples (opts_list, desc)) into data dict under key cmd_name.
    data[cmd_name] is expected to be a list of entries (existing examples).
    We'll append new entries of form {"description": desc, "cmds": [...]}
    Avoid duplicates by checking existing descriptions and existing cmds.
    """
    if cmd_name not in data or not isinstance(data[cmd_name], list):
        data.setdefault(cmd_name, [])

    # build index of existing descriptions -> entry
    existing_by_desc = {}
    existing_cmds_set = set()
    for entry in data[cmd_name]:
        # description may be under keys 'description' or 'desc_correspondant'
        desc_key = entry.get("description") or entry.get("desc_correspondant") or entry.get("desc") or ""
        existing_by_desc[desc_key.lower()] = entry
        # gather existing cmds
        if "cmds" in entry and isinstance(entry["cmds"], list):
            for c in entry["cmds"]:
                existing_cmds_set.add(c)
        elif "cmd" in entry:
            existing_cmds_set.add(entry["cmd"])

    added = 0
    for opts, desc in options_parsed:
        desc_norm = desc.strip()
        if not desc_norm:
            continue
        cmds = build_variants(cmd_name, opts, desc_norm)
        # try match by similar description (substring)
        matched = None
        for ex_desc_lower, entry in existing_by_desc.items():
            if ex_desc_lower and desc_norm.lower() in ex_desc_lower:
                matched = entry
                break
            if ex_desc_lower and ex_desc_lower in desc_norm.lower():
                matched = entry
                break
        if matched:
            # ensure 'cmds' exists
            cur_cmds = set(matched.get("cmds", []))
            # add any new cmds
            for c in cmds:
                if c not in cur_cmds:
                    cur_cmds.add(c)
                    if c not in existing_cmds_set:
                        existing_cmds_set.add(c)
            matched["cmds"] = sorted(cur_cmds)
        else:
            # skip if all cmd variants already exist globally
            if all(c in existing_cmds_set for c in cmds):
                continue
            new_entry = {"description": desc_norm, "cmds": cmds}
            data[cmd_name].append(new_entry)
            # update indexes
            existing_by_desc[desc_norm.lower()] = new_entry
            for c in cmds:
                existing_cmds_set.add(c)
            added += 1
    return added

def process_one_json(json_path):
    print(f"[+] Processing {json_path}")
    # backup
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy(json_path, os.path.join(BACKUP_DIR, os.path.basename(json_path)))
    with open(json_path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except Exception:
            print(f"[!] Failed to parse JSON {json_path}")
            return

    total_added = 0
    # iterate commands (keys)
    for cmd_name in list(data.keys()):
        # only simple command names (no spaces); skip complex keys if any
        if not isinstance(cmd_name, str) or " " in cmd_name:
            continue
        help_text = run_help(cmd_name)
        if not help_text:
            if VERBOSE:
                print(f"    [-] no help for {cmd_name} (skipping)")
            continue
        opt_blocks = extract_option_lines(help_text)
        if not opt_blocks:
            if VERBOSE:
                print(f"    [i] no option lines parsed for {cmd_name}")
            continue
        # parse each block into tokens + desc
        options_parsed = []
        for blk in opt_blocks:
            left, desc = split_left_desc(blk)
            opts = extract_option_tokens(left)
            if not opts:
                continue
            options_parsed.append((opts, desc))
        if not options_parsed:
            continue
        added = merge_options_into_data(data, cmd_name, options_parsed)
        if VERBOSE:
            print(f"    [+] {cmd_name}: parsed {len(options_parsed)} options, added {added}")
        total_added += added

    # save updated json
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    print(f"[+] Done {json_path} (added {total_added} entries)")

def main():
    json_files = glob(os.path.join(JSON_DIR, "*.json"))
    if not json_files:
        print(f"[!] No .json files found in {JSON_DIR}")
        return
    for jf in json_files:
        process_one_json(jf)

if __name__ == "__main__":
    main()
