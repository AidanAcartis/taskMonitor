#!/usr/bin/env python3
import re

# -------------------------------
# 🔹 Dictionnaire de regex pour détecter les types
# -------------------------------
TYPE_REGEX = {
    # Chemins et fichiers
    "folder": re.compile(r"^(/|~)[\w\-/\.]+/?$"),
    "file": re.compile(r"^(?:[\w\-.]+|\./[\w\-.]+)$"),
    "device": re.compile(r"^/dev/[^\s]+$"),
    "envfile": re.compile(r"^(?:\.|/)?[\w\.-]+\.(?:env|conf|ini)$"),
    "script": re.compile(r"^\./[\w\.-]+\.sh$"),
    "archive": re.compile(r"^[\w\.-]+\.(?:tar|gz|zip|bz2|xz)$"),

    # Réseau
    "ip": re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$"),
    "ipv6": re.compile(r"^([0-9a-fA-F]{0,4}:){1,7}[0-9a-fA-F]{0,4}$"),
    "port": re.compile(r"^\d{1,5}$"),
    "url": re.compile(r"^https?://[^\s]+$", re.IGNORECASE),

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
    "arg": "Argument",
}

# -------------------------------
# 🔹 Fonction de détection
# -------------------------------
def detect_type(token: str) -> str:
    token = token.strip()

    # Enlever guillemets extérieurs pour JSON
    if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
        inner = token[1:-1]
        if TYPE_REGEX["json"].match(inner):
            return "json"
        token = inner

    # Priorité aux types spécifiques
    for name in ["ip", "ipv6", "port", "number", "url", "json", "string"]:
        if TYPE_REGEX[name].match(token):
            return name

    # Ensuite les autres types (fichier, dossier, etc.)
    for name in ["folder", "file", "device", "envfile", "script", "archive"]:
        if TYPE_REGEX[name].match(token):
            return name

    # Par défaut, c'est un argument
    return "arg"



# -------------------------------
# 🔹 Programme principal
# -------------------------------
if __name__ == "__main__":
    while True:
        user_input = input("\nEnter element to detect (or 'exit' to quit): ").strip()
        if user_input.lower() == "exit":
            break

        elem_type = detect_type(user_input)
        desc = TYPE_DESCRIPTION.get(elem_type, "Unknown type")
        print(f"Element: '{user_input}' -> Type: {elem_type} -> Description: {desc}")
