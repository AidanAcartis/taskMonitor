Je veux creer un dictionnaire de cette forme :
```
{
        '.js'     : 'text/javascript',
        '.mjs'    : 'text/javascript',
        '.json'   : 'application/json',
        '.webmanifest': 'application/manifest+json',
        '.doc'    : 'application/msword',
        '.dot'    : 'application/msword',
        '.wiz'    : 'application/msword',
        '.nq'     : 'application/n-quads',
        '.nt'     : 'application/n-triples',
```
Voici mon idee:
- J'ai ce dossier `/usr/share/mime`:
```bash
(myenv) aidan@aidan-Lenovo-N50-70:/usr/share/mime$ ls
aliases      chemical       globs   image  message     multipart   text       version    x-epoc
application  font           globs2  inode  mime.cache  packages    treemagic  video      XMLnamespaces
audio        generic-icons  icons   magic  model       subclasses  types      x-content
(myenv) aidan@aidan-Lenovo-N50-70:/usr/share/mime$ ls -l | grep "^d"
drwxr-xr-x 2 root root  28672 Sep  3 11:47 application
drwxr-xr-x 2 root root   4096 Sep  3 11:47 audio
drwxr-xr-x 2 root root   4096 Sep  3 11:47 chemical
drwxr-xr-x 2 root root   4096 Sep  3 11:47 font
drwxr-xr-x 2 root root   4096 Sep  3 11:47 image
drwxr-xr-x 2 root root   4096 Sep  3 11:47 inode
drwxr-xr-x 2 root root   4096 Sep  3 11:47 message
drwxr-xr-x 2 root root   4096 Sep  3 11:47 model
drwxr-xr-x 2 root root   4096 Sep  3 11:47 multipart
drwxr-xr-x 2 root root   4096 Sep  3 11:46 packages
drwxr-xr-x 2 root root   4096 Sep  3 11:47 text
drwxr-xr-x 2 root root   4096 Sep  3 11:47 video
drwxr-xr-x 2 root root   4096 Sep  3 11:47 x-content
drwxr-xr-x 2 root root   4096 Sep  3 11:47 x-epoc
(myenv) aidan@aidan-Lenovo-N50-70:/usr/share/mime$ 

```
Avec je n'ai affiche que les directory.
Dans chaque directory, il y a des fichiers `xml`. comme ceci par exemple:
```bash
(myenv) aidan@aidan-Lenovo-N50-70:/usr/share/mime/text$ ls
cache-manifest.xml               x-basic.xml                         x-idl.xml               x-python3.xml
calendar.xml                     x-bibtex.xml                        x-imelody.xml           x-python.xml

```
Et voici a quoi ressemble le fichier `xml`:
Par exemple, `julia.xml` dans le directory `text`:
```bash
<?xml version="1.0" encoding="utf-8"?>
<mime-type xmlns="http://www.freedesktop.org/standards/shared-mime-info" type="text/julia">
  <!--Created automatically by update-mime-database. DO NOT EDIT!-->
  <comment>Julia source code</comment>
  <comment xml:lang="uk">початковий код Julia</comment>
  <comment xml:lang="sv">Julia-källkod</comment>
  <comment xml:lang="ru">Исходный код Julia</comment>
  <comment xml:lang="pl">Kod źródłowy Julia</comment>
  <comment xml:lang="ja">Julia算譜</comment>
  <comment xml:lang="it">Codice sorgente Julia</comment>
  <comment xml:lang="gl">Código fonte en Julia</comment>
  <comment xml:lang="eu">Julia iturburu-kodea</comment>
  <comment xml:lang="es">código fuente en Julia</comment>
  <comment xml:lang="de">Julia-Quelltext</comment>
  <comment xml:lang="be">зыходны код Julia</comment>
  <sub-class-of type="text/plain"/>
  <glob pattern="*.jl"/>
</mime-type>

```
Je dois prendre dans les fichiers xml:
- Ce commentaire `<comment>Julia source code</comment>` donc le seul comment sans `xml:lang=`.
- Le contenu de ce type `type="text/julia"` => `text/julia` ici `<mime-type xmlns="http://www.freedesktop.org/standards/shared-mime-info" type="text/julia">`, dans la balise d'ouverture de `<mime-type></mime-type>`
- et tous les valeurs `pattern=""` de tous les balises <glob /> : `<glob pattern="*.jl"/>`, c'est-a-dire
ceci `.jl` ici. DOnc, s'il y en a plusieurs :
```
  <glob pattern="*.html" weight="80"/>
  <glob pattern="*.htm" weight="80"/>
```
On les prend tous, => '.html, .html'

Donc , on obtient comme element dans le dictionnaire:
{extension} + {type} + {comment}

Je veux boucler cela sur toutes les directory presents dans `/usr/share/mime`:
```bash
(myenv) aidan@aidan-Lenovo-N50-70:/usr/share/mime$ ls -l | grep "^d"
drwxr-xr-x 2 root root  28672 Sep  3 11:47 application
drwxr-xr-x 2 root root   4096 Sep  3 11:47 audio
drwxr-xr-x 2 root root   4096 Sep  3 11:47 chemical
drwxr-xr-x 2 root root   4096 Sep  3 11:47 font
drwxr-xr-x 2 root root   4096 Sep  3 11:47 image
drwxr-xr-x 2 root root   4096 Sep  3 11:47 inode
drwxr-xr-x 2 root root   4096 Sep  3 11:47 message
drwxr-xr-x 2 root root   4096 Sep  3 11:47 model
drwxr-xr-x 2 root root   4096 Sep  3 11:47 multipart
drwxr-xr-x 2 root root   4096 Sep  3 11:46 packages
drwxr-xr-x 2 root root   4096 Sep  3 11:47 text
drwxr-xr-x 2 root root   4096 Sep  3 11:47 video
drwxr-xr-x 2 root root   4096 Sep  3 11:47 x-content
drwxr-xr-x 2 root root   4096 Sep  3 11:47 x-epoc

```
et a absolument toutes les fichiers .xml dans chacun de ces directory.

Parfait 👍 tu as bien compris la structure de `/usr/share/mime`.
On peut écrire un script Python qui :

1. Parcourt tous les sous-dossiers dans `/usr/share/mime`
2. Ouvre chaque fichier `.xml`
3. Récupère :

   * le `type` dans `<mime-type ... type="...">`
   * le premier `<comment>` sans attribut `xml:lang`
   * toutes les extensions dans les balises `<glob pattern="..."/>`
4. Construit un dictionnaire `{extension: {"type": ..., "comment": ...}}`

Voici un script complet :

```python
import os
import xml.etree.ElementTree as ET

MIME_DIR = "/usr/share/mime"

def parse_mime_xml(file_path):
    """Extrait type, comment et extensions depuis un fichier XML MIME"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        mime_type = root.attrib.get("type")
        if not mime_type:
            return []

        # premier commentaire sans attribut xml:lang
        comment = None
        for c in root.findall("{http://www.freedesktop.org/standards/shared-mime-info}comment"):
            if not c.attrib:  # sans xml:lang
                comment = c.text
                break

        # toutes les extensions dans glob
        extensions = []
        for glob in root.findall("{http://www.freedesktop.org/standards/shared-mime-info}glob"):
            pattern = glob.attrib.get("pattern")
            if pattern and pattern.startswith("*."):
                extensions.append(pattern[1:])  # enlève * → .ext

        # crée un dictionnaire pour chaque extension
        results = []
        for ext in extensions:
            results.append((ext, {"type": mime_type, "comment": comment}))
        return results

    except Exception as e:
        print(f"Erreur parsing {file_path}: {e}")
        return []


def build_mime_dict():
    mime_dict = {}
    for root, dirs, files in os.walk(MIME_DIR):
        for f in files:
            if f.endswith(".xml"):
                file_path = os.path.join(root, f)
                for ext, data in parse_mime_xml(file_path):
                    mime_dict[ext] = data
    return mime_dict


if __name__ == "__main__":
    mime_map = build_mime_dict()


    # Sauvegarde en JSON
    with open("mime_map.json", "w", encoding="utf-8") as f:
        json.dump(mime_map, f, indent=4, ensure_ascii=False)

    # Exemple d'affichage de quelques entrées
    for i, (ext, data) in enumerate(mime_map.items()):
        print(f"{ext} -> {data['type']} ({data['comment']})")
        if i > 20:  # afficher seulement les 20 premiers
            break

    print(f"\nNombre total d'extensions trouvées : {len(mime_map)}")
```

---

✅ Exemple de sortie (avec ton `julia.xml`) :

```
.jl -> text/julia (Julia source code)
```

✅ Et pour un HTML :

```
.html -> text/html (HTML document)
.htm -> text/html (HTML document)
```

---

👉 Tu veux que je l’adapte pour **générer directement un dictionnaire Python formaté comme ton exemple** :

```python
{
    ".jl": "text/julia",
    ".html": "text/html",
    ...
}
```

ou tu préfères garder le format enrichi avec `{"type": ..., "comment": ...}` ?
