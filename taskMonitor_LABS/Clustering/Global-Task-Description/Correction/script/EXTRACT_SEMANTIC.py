#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transform activity dataset into semantic abstraction format
et nettoyer les objets génériques seuls.

INPUT  : activity_data_final_v3.jsonl
OUTPUT : activity_data_semantic_clean.jsonl
"""

import json
import re
from pathlib import Path

# ─────────────────────────────────────────────
# LOAD DICTIONARIES
# ─────────────────────────────────────────────
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

MIME_MAP       = load_json("./DICT/mime_map.json")
FILE_EXT_MAP   = load_json("./DICT/FILE_EXTENSION.json")
TOOLS_MAP      = load_json("./DICT/TOOLS.json")

TOOLS_MAP = {k.lower(): v for k, v in TOOLS_MAP.items()}

VERB_MAP = load_json("./DICT/VERB_MAP_EXTENDED.json")
VERB_MAP = {k.lower(): v.lower() for k, v in VERB_MAP.items()}

# ─────────────────────────────────────────────
# UTILS
# ─────────────────────────────────────────────
STOP_WORDS = {
    "of", "to", "for", "with", "in", "on", "at", "from",
    "by", "about", "as", "into", "after", "before"
}

COMMON_VERBS = {
    "create", "run", "execute", "install", "remove", "update",
    "send", "open", "read", "write", "build", "compile",
    "check", "verify", "record", "display", "launch",
    "render", "provide", "handle", "manage", "analyze"
}

GENERIC_OBJECTS = {
    "app", "application", "command", "command line",
    "command tool", "tool", "software", "program"
}

def clean_text(text):
    return text.lower().strip()

def clean_segment(seg):
    seg = seg.lower().strip()
    seg = re.sub(r"(command used to|used to|used for|used in|opened with|written in|executed in)", "", seg)
    return seg.strip()

def detect_verb(word):
    if word in VERB_MAP:
        return VERB_MAP[word]
    if word in COMMON_VERBS:
        return word
    return None

def extract_action(item):
    parts = [p.strip() for p in item.split(",") if p.strip()]
    for part in reversed(parts):
        segment = clean_segment(part)
        words = segment.split()
        if not words:
            continue
        verb = detect_verb(words[0])
        if not verb:
            continue
        obj_words = []
        for w in words[1:]:
            if w in STOP_WORDS:
                break
            obj_words.append(w)
        action = verb
        if obj_words:
            action += " " + " ".join(obj_words)
        return action
    return None

def filter_generic_objects(objects):
    objects_set = set(objects)
    if objects_set and objects_set.issubset(GENERIC_OBJECTS):
        return []
    return objects

def extract_objects(item):
    objects = set()
    item_lower = item.lower()
    item_clean = re.sub(r"\b\w+\.\w+\b", "", item_lower)

    # Tools
    for tool_key, tool_name in TOOLS_MAP.items():
        tool_name_lower = tool_name.lower()
        if re.search(rf"\b{re.escape(tool_key)}\b", item_lower):
            if tool_name_lower in GENERIC_OBJECTS:
                words = item_lower.split()
                if any(tool_key != w for w in words):
                    objects.add(tool_name_lower)
            else:
                objects.add(tool_name_lower)

    # File extensions
    extensions = re.findall(r"\.\w+", item_lower)
    for ext in extensions:
        file_type = None
        if ext in FILE_EXT_MAP:
            file_type = FILE_EXT_MAP[ext]
        elif ext in MIME_MAP:
            entry = MIME_MAP[ext]
            if isinstance(entry, dict):
                file_type = entry.get("comment")
            else:
                file_type = str(entry)
        if file_type:
            objects.add(file_type.lower())

    # Special files
    linux_special_files = {
        "/etc/hosts": "hostname mapping",
        "/etc/passwd": "user accounts",
        "/etc/shadow": "user passwords",
        "/etc/group": "user groups",
        "/etc/fstab": "filesystem table",
        "/etc/resolv.conf": "dns configuration",
        "/etc/hostname": "system hostname",
        "/etc/motd": "login message",
        "/etc/profile": "system profile",
        "/etc/bashrc": "bash config",
        "/var/log/syslog": "system log",
        "/var/log/messages": "system messages",
        "/var/log/auth.log": "authentication log",
        "/var/log/kern.log": "kernel log",
        "/var/log/dpkg.log": "package log",
        "/var/log/apt/history.log": "apt history",
        "/var/log/boot.log": "boot log",
        "/etc/cron.d": "cron jobs",
        "/etc/crontab": "cron schedule",
        "/etc/ssh/sshd_config": "ssh configuration",
        "/etc/network/interfaces": "network config",
        "/etc/nginx/nginx.conf": "nginx configuration",
        "/etc/apache2/apache2.conf": "apache configuration",
        "/dev/null": "null device",
        "/dev/zero": "zero device",
        "/proc/cpuinfo": "cpu info",
        "/proc/meminfo": "memory info",
        "/proc/uptime": "uptime info",
    }
    for path, name in linux_special_files.items():
        if path in item_lower:
            objects.add(name)

    return list(objects)

# ─────────────────────────────────────────────
# MAIN TRANSFORM + CLEAN GENERIC OBJECTS
# ─────────────────────────────────────────────
def transform_dataset(input_path, output_path):
    results = []

    with open(input_path, encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            actions = set()
            objects = set()

            for item in data["task_items"]:
                action = extract_action(item)
                if action:
                    actions.add(action)

                objs = extract_objects(item)
                for obj in objs:
                    objects.add(obj)

            # Nettoyer les objets génériques seuls
            objects = filter_generic_objects(list(objects))

            new_entry = {
                "task_items": data["task_items"],
                "semantic_features": {
                    "actions": sorted(actions),
                    "objects": sorted(objects),
                },
                "global_task_intention": data["global_task_intention"],
            }

            results.append(new_entry)

    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Done. Saved to {output_path}")


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    INPUT  = "activity_data_final_v3.jsonl"
    OUTPUT = "activity_data_semantic_clean.jsonl"

    if not Path(INPUT).exists():
        print(f"❌ File not found: {INPUT}")
    else:
        transform_dataset(INPUT, OUTPUT)