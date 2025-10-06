import csv
from openpyxl import Workbook

# Fichiers source et destination
csv_file = "data.csv"
xlsx_file = "data.xlsx"

# Création d’un nouveau classeur Excel
wb = Workbook()
ws = wb.active
ws.title = "Données collectées"

# Lecture du CSV et ajout ligne par ligne
with open(csv_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter=';')
    for row in reader:
        ws.append(row)

# Sauvegarde du fichier .xlsx
wb.save(xlsx_file)

print(f"✅ Fichier Excel généré : {xlsx_file}")
