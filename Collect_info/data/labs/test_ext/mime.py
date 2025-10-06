import mimetypes

def get_extension_definition(extension):
    mime_type, _ = mimetypes.guess_type("file" + extension)
    if mime_type:
        return mime_type
    else:
        return "Extension inconnue"

# Exemple d'utilisation
extension = input("Entrez l'extension (ex: .png) : ")
definition = get_extension_definition(extension)
print(f"L'extension {extension} correspond à : {definition}")

