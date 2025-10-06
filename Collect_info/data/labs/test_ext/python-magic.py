import magic

def get_file_type(file_path):
    mime_type = magic.Magic(mime=True)
    return mime_type.from_file(file_path)

file_path = input("Entrez le chemin du fichier : ")
file_type = get_file_type(file_path)
print(f"Le type MIME du fichier est : {file_type}")
