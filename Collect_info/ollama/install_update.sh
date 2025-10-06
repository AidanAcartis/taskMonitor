#!/bin/sh
set -eu

red="$( (/usr/bin/tput bold || :; /usr/bin/tput setaf 1 || :) 2>&-)"
plain="$( (/usr/bin/tput sgr0 || :) 2>&-)"
status() { echo ">>> $*" >&2; }
error() { echo "${red}ERROR:${plain} $*"; exit 1; }

ARCH=$(uname -m)
case "$ARCH" in
    x86_64) ARCH="amd64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) error "Unsupported architecture: $ARCH" ;;
esac

BINDIR="/usr/local/bin"
INSTALL_DIR="/usr/local/lib/ollama"

# Vérifie que le fichier existe
TGZ_FILE="./ollama-linux-${ARCH}.tgz"
[ -f "$TGZ_FILE" ] || error "Fichier $TGZ_FILE non trouvé dans le dossier courant."

# Droits root requis
SUDO=
[ "$(id -u)" -ne 0 ] && SUDO=sudo

# Nettoyage ancienne version
if [ -d "$INSTALL_DIR" ]; then
    status "Suppression ancienne installation à $INSTALL_DIR"
    $SUDO rm -rf "$INSTALL_DIR"
fi

status "Création des dossiers nécessaires"
$SUDO install -d -m 755 "$INSTALL_DIR" "$BINDIR"

status "Décompression de $TGZ_FILE vers $INSTALL_DIR"
$SUDO tar -xzf "$TGZ_FILE" -C /usr/local

# Lien symbolique
if [ ! -f "$BINDIR/ollama" ]; then
    status "Création d'un lien vers ollama dans $BINDIR"
    $SUDO ln -sf /usr/local/ollama "$BINDIR/ollama"
fi

status "Installation terminée. Teste avec la commande : ollama"
