import sqlite3
import os
import subprocess
from datetime import datetime
import time

DB_PATH = "activities.sqlite"

def install_dependencies():
    """Installe les outils nécessaires."""
    tools = ["sqlite3", "auditd", "lsof", "ps"]

    for tool in tools:
        if subprocess.run(f"command -v {tool}", shell=True, capture_output=True).returncode != 0:
            print(f"Installation de {tool}...")
            os.system(f"sudo apt install -y {tool}")

    if subprocess.run("sudo systemctl is-active --quiet auditd", shell=True).returncode != 0:
        print("Activation et démarrage d'auditd...")
        os.system("sudo systemctl enable auditd && sudo systemctl start auditd")

def configure_auditd():
    """Configure auditd pour enregistrer les commandes exécutées."""
    audit_rule = '-a always,exit -F arch=b64 -S execve -k command_exec'
    audit_file = "/etc/audit/rules.d/audit.rules"

    with open(audit_file, "r") as f:
        if audit_rule in f.read():
            print("auditd est déjà configuré.")
            return

    print("Ajout de la règle auditd...")
    os.system(f'echo "{audit_rule}" | sudo tee -a {audit_file}')
    os.system("sudo service auditd restart")

def init_db():
    """Initialise la base de données."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activites (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Type TEXT,
            Nom TEXT,
            Heure_Ouverture TEXT,
            Heure_Fermeture TEXT,
            Jour TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_opened_files():
    """Récupère les fichiers ouverts."""
    result = subprocess.run("lsof -u $(whoami) -d 0-65535", shell=True, capture_output=True, text=True)
    files = []
    for line in result.stdout.split("\n")[1:]:
        parts = line.split()
        if len(parts) > 8:
            files.append((parts[8], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    return files

def get_closed_files(prev_files):
    """Détecte les fichiers fermés en comparant avant/après."""
    current_files = get_opened_files()
    closed_files = []

    for prev in prev_files:
        if prev not in current_files:
            closed_files.append((prev[0], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    return closed_files

def get_executed_commands():
    """Récupère les commandes exécutées depuis 00:00."""
    result = subprocess.run("ausearch -k command_exec --start today", shell=True, capture_output=True, text=True)
    commands = []
    for line in result.stdout.split("\n"):
        if "exe=" in line:
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cmd = line.split("exe=")[-1].split()[0]
            commands.append((cmd, time_str))
    return commands

def get_running_programs():
    """Récupère les programmes en cours d'exécution."""
    result = subprocess.run("ps -eo pid,cmd,lstart", shell=True, capture_output=True, text=True)
    programs = []
    for line in result.stdout.split("\n")[1:]:
        parts = line.split()
        if len(parts) > 4:
            programs.append((" ".join(parts[1:-4]), " ".join(parts[-4:])))
    return programs

def get_web_history():
    """Récupère l'historique des sites ouverts aujourd'hui."""
    query = '''SELECT url, datetime(last_visit_date/1000000, 'unixepoch') FROM moz_places 
               WHERE last_visit_date >= strftime('%s','now','start of day')*1000000;'''
    result = subprocess.run(f"sqlite3 ~/.mozilla/firefox/*.default-release/places.sqlite \"{query}\"",
                            shell=True, capture_output=True, text=True)
    sites = []
    for line in result.stdout.split("\n"):
        parts = line.split("|")
        if len(parts) == 2:
            sites.append((parts[0], parts[1]))
    return sites

def insert_data(data, type_act):
    """Insère les données collectées dans la base."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.now().strftime("%A")
    
    for nom, heure in data:
        cursor.execute("INSERT INTO activites (Type, Nom, Heure_Ouverture, Jour) VALUES (?, ?, ?, ?)", 
                       (type_act, nom, heure, today))
    
    conn.commit()
    conn.close()

def main():
    #install_dependencies()
    configure_auditd()
    init_db()
    
    prev_files = get_opened_files()
    insert_data(prev_files, "Fichier")
    insert_data(get_executed_commands(), "Commande")
    insert_data(get_running_programs(), "Programme")
    insert_data(get_web_history(), "Site")

    time.sleep(5)
    
    closed_files = get_closed_files(prev_files)
    insert_data(closed_files, "Fichier_Fermé")

if __name__ == "__main__":
    main()
