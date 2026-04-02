# Tester FileCollector
from taskmonitor.collectors.file_collector import FileCollector
from taskmonitor.core import config
from pathlib import Path

# Vérifier que les dossiers existent déjà
config.OPEN_CLOSED_DIR.mkdir(parents=True, exist_ok=True)
config.DATA_FILE_DIR.mkdir(parents=True, exist_ok=True)

# Instanciation et lancement
collector = FileCollector()
collector.run()

# Vérification des fichiers générés
print("=== Vérification des fichiers ===")
opened_exists = config.OPENED_FILE.exists()
closed_exists = config.CLOSED_FILE.exists()
collected_exists = config.COLLECTED_FILE.exists()
data_file_exists = config.DATA_FILE_TXT.exists()

print(f"Opened_file.txt : {'OK' if opened_exists else 'MANQUANT'}")
print(f"Closed_file.txt : {'OK' if closed_exists else 'MANQUANT'}")
print(f"collected_file.txt : {'OK' if collected_exists else 'MANQUANT'}")
print(f"data_file.txt : {'OK' if data_file_exists else 'MANQUANT'}")