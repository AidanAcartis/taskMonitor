#!/usr/bin/env python3
import os
import json
import subprocess
import re
from glob import glob
import shutil

JSON_DIR = "./dict_json"
BACKUP_DIR = "./dict_json_backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

def extract_subcommands(cmd):
    """
    Retourne une liste (subcmd, description) depuis `cmd --help` via awk-like filtrage.
    """
    try:
        result = subprocess.run(
            f"{cmd} --help | awk '/^[[:space:]]+[a-z0-9_-]+[[:space:]]/{{cmd=$1; $1=\"\"; print cmd \"|\" $0}}'",
            shell=True, capture_output=True, text=True, timeout=4
        )
        if result.returncode != 0:
            return []
    except Exception:
        return []

    lines = result.stdout.strip().splitlines()
    entries = []
    for line in lines:
        if "|" in line:
            sub, desc = line.split("|", 1)
            sub = sub.strip()
            desc = desc.strip()
            if sub and desc:
                entries.append((sub, desc))
    return entries

def enrich_json_with_help(json_path):
    """Analyse un fichier JSON et ajoute les sous-commandes manquantes."""
    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"❌ Erreur parsing {json_path}: {e}")
            return

    total_added = 0
    for cmd_main in list(data.keys()):
        # ignore les groupes TLDR non exécutables
        if not re.match(r"^[a-z0-9._-]+$", cmd_main):
            continue

        print(f"🔍 Vérification de la commande: {cmd_main}")

        subcommands = extract_subcommands(cmd_main)
        if not subcommands:
            print(f"⚙️  Aucune sous-commande trouvée pour {cmd_main}")
            continue

        existing_cmds = {e.get("cmd", "").split()[1] for e in data.get(cmd_main, []) if "cmd" in e and len(e["cmd"].split()) > 1}

        for sub, desc in subcommands:
            if sub not in existing_cmds:
                entry = {
                    "description": desc,
                    "cmd": f"{cmd_main} {sub}"
                }
                data.setdefault(cmd_main, []).append(entry)
                total_added += 1

        print(f"✅ {total_added} nouvelles sous-commandes ajoutées pour {cmd_main}")

    # sauvegarde du fichier mis à jour
    shutil.copy(json_path, os.path.join(BACKUP_DIR, os.path.basename(json_path)))
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    json_files = glob(os.path.join(JSON_DIR, "*.json"))
    if not json_files:
        print(f"Aucun fichier JSON trouvé dans {JSON_DIR}")
        return

    for jf in json_files:
        print(f"\n📂 Fichier: {jf}")
        enrich_json_with_help(jf)

if __name__ == "__main__":
    main()
