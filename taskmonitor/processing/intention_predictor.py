#!/usr/bin/env python3
"""
Prédicteur d'intentions globales pour chaque cluster
"""

import re
import torch
from transformers import T5ForConditionalGeneration, T5TokenizerFast
from pathlib import Path
import json

from taskmonitor.core.config import INTENTION_CONFIG, INTENTION_MAX_INPUT_LENGTH, INTENTION_VERB_MAP_FILE

# ── LOAD VERB MAP ─────────────────────────────────────────
with open(INTENTION_VERB_MAP_FILE, encoding="utf-8") as f:
    VERB_MAP = json.load(f)
VERB_MAP = {k.lower(): v.lower() for k, v in VERB_MAP.items()}

# ── STOP WORDS et verbes communs
STOP_WORDS = {
    "of", "to", "for", "with", "in", "on", "at", "from",
    "by", "about", "as", "into", "after", "before"
}

COMMON_VERBS = {
    "create", "run", "execute", "install", "remove", "update",
    "send", "open", "read", "write", "build", "compile",
    "check", "verify", "record", "display", "launch",
    "render", "provide", "handle", "manage", "analyze",
    "list", "clear", "exit", "play", "search"
}

# ── FORMAT PROMPT ─────────────────────────────────────────
def format_prompt(items):
    items_text = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(items))
    return (
        "Based on the following list of task items, "
        "generate a concise global task intention in one sentence:\n"
        f"{items_text}"
    )

# ── LOAD MODEL ────────────────────────────────────────────
def load_model(model_path: str):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = T5TokenizerFast.from_pretrained(model_path)
    model = T5ForConditionalGeneration.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
    )
    if device == "cpu":
        model.to(device)
    model.eval()
    return model, tokenizer, device

# ── PREDICTION ───────────────────────────────────────────
def predict(model, tokenizer, device, items):
    if not items:
        return "(cluster vide — pas de prediction)"
    prompt = format_prompt(items)
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=INTENTION_MAX_INPUT_LENGTH,
        truncation=True,
    ).to(device)
    with torch.no_grad():
        outputs = model.generate(**inputs, **INTENTION_CONFIG)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# ── CLEAN & DETECT VERB ───────────────────────────────────
def clean_segment(seg):
    seg = seg.lower().strip()
    seg = re.sub(
        r"(command used to|used to|used for|used in|opened with|written in|executed in)",
        "",
        seg
    )
    return seg.strip()

def detect_verb(word):
    if word in VERB_MAP:
        return VERB_MAP[word]
    if word in COMMON_VERBS:
        return word
    return None

# ── EXTRACTION ACTION ─────────────────────────────────────
def extract_action(item):
    parts = [p.strip() for p in item.split(",") if p.strip()]

    INVALID_STARTS = {"text", "data", "file", "application", "plain", "script", "document"}

    # Priorité : segments contenant "used to"
    for part in parts:
        if "used to" in part:
            segment = clean_segment(part)
            words = segment.split()
            if not words: continue
            if words[0] in INVALID_STARTS: continue
            verb = detect_verb(words[0])
            if not verb: continue
            obj_words = []
            for w in words[1:]:
                if w in STOP_WORDS: break
                obj_words.append(w)
            return verb + (" " + " ".join(obj_words) if obj_words else "")

    # Fallback
    for part in reversed(parts):
        segment = clean_segment(part)
        words = segment.split()
        if not words: continue
        if words[0] in INVALID_STARTS: continue
        verb = detect_verb(words[0])
        if not verb: continue
        obj_words = []
        for w in words[1:]:
            if w in STOP_WORDS: break
            obj_words.append(w)
        return verb + (" " + " ".join(obj_words) if obj_words else "")

    return None

# ── GENERATE SIMPLE INTENTION ────────────────────────────
def generate_simple_intention(item: str) -> str:
    item_lower = item.lower()
    obj = item.split(",")[0].strip()
    obj_lower = obj.lower()

    if "file" in item_lower and "opened with" in item_lower:
        match = re.search(r"opened with ([^,]+)", item_lower)
        if match:
            app = match.group(1).strip().title()
            return f"open {obj} with {app}"

    action = extract_action(item)

    INVALID_ACTIONS = {
        "text files", "plain text", "data related", "file",
        "application log", "script", "document"
    }

    if action and action.lower() in INVALID_ACTIONS:
        action = None

    if action:
        words = action.split()
        if len(words) == 1:
            verb = words[0]
            if verb == obj_lower:
                return verb
            return f"{verb} {obj_lower}"
        return action

    if "application" in item_lower:
        if "desktop" in item_lower:
            return f"manage {obj_lower}"
        return f"use {obj_lower}"
    if "file" in item_lower:
        return f"open {obj_lower}"
    if "command" in item_lower:
        return f"run {obj_lower}"

    return obj_lower