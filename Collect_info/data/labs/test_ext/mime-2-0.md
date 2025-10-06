Je dois recree le module mimetypes. Plus precisement `mimetypes.guess_type("file" + extension)` la fonction `guess_type`. 
Voici les importattions dans `mimetypes.py`:

- `import`:
```py
import os
import sys
import posixpath
import urllib.parse

try:
    from _winapi import _mimetypes_read_windows_registry
except ImportError:
    _mimetypes_read_windows_registry = None

try:
    import winreg as _winreg
except ImportError:
    _winreg = None
```
Explique moi le role de chacun.
- `variables`:
```py
__all__ = [
    "knownfiles", "inited", "MimeTypes",
    "guess_type", "guess_all_extensions", "guess_extension",
    "add_type", "init", "read_mime_types",
    "suffix_map", "encodings_map", "types_map", "common_types"
]

knownfiles = [
    "/etc/mime.types",
    "/etc/httpd/mime.types",                    # Mac OS X
    "/etc/httpd/conf/mime.types",               # Apache
    "/etc/apache/mime.types",                   # Apache 1
    "/etc/apache2/mime.types",                  # Apache 2
    "/usr/local/etc/httpd/conf/mime.types",
    "/usr/local/lib/netscape/mime.types",
    "/usr/local/etc/httpd/conf/mime.types",     # Apache 1.2
    "/usr/local/etc/mime.types",                # Apache 1.3
    ]
# Tous ces fichiers .types sont faux a part '"/etc/mime.types"' qui contient le dictionnaie de tous les extensions + types.
inited = False
_db = None
```
Explique moi le role de chacun.

- Voici la `classe` dans le code:
```py

class MimeTypes:
    """MIME-types datastore.

    This datastore can handle information from mime.types-style files
    and supports basic determination of MIME type from a filename or
    URL, and can guess a reasonable extension given a MIME type.
    """
```
- Les `fonctions` dans `class MimeTypes`:
```py
 def __init__(self, filenames=(), strict=True):
        if not inited:
            init()
        self.encodings_map = _encodings_map_default.copy()
        self.suffix_map = _suffix_map_default.copy()
        self.types_map = ({}, {}) # dict for (non-strict, strict)
        self.types_map_inv = ({}, {})
        for (ext, type) in _types_map_default.items():
            self.add_type(type, ext, True)
        for (ext, type) in _common_types_default.items():
            self.add_type(type, ext, False)
        for name in filenames:
            self.read(name, strict)

def add_type(self, type, ext, strict=True):
        self.types_map[strict][ext] = type
        exts = self.types_map_inv[strict].setdefault(type, [])
        if ext not in exts:
            exts.append(ext)

def guess_type(self, url, strict=True):
        url = os.fspath(url)
        p = urllib.parse.urlparse(url)
        if p.scheme and len(p.scheme) > 1:
            scheme = p.scheme
            url = p.path
        else:
            scheme = None
            url = os.path.splitdrive(url)[1]
        if scheme == 'data':
            comma = url.find(',')
            if comma < 0:
                # bad data URL
                return None, None
            semi = url.find(';', 0, comma)
            if semi >= 0:
                type = url[:semi]
            else:
                type = url[:comma]
            if '=' in type or '/' not in type:
                type = 'text/plain'
            return type, None           # never compressed, so encoding is None
        base, ext = posixpath.splitext(url)
        while (ext_lower := ext.lower()) in self.suffix_map:
            base, ext = posixpath.splitext(base + self.suffix_map[ext_lower])
        # encodings_map is case sensitive
        if ext in self.encodings_map:
            encoding = self.encodings_map[ext]
            base, ext = posixpath.splitext(base)
        else:
            encoding = None
        ext = ext.lower()
        types_map = self.types_map[True]
        if ext in types_map:
            return types_map[ext], encoding
        elif strict:
            return None, encoding
        types_map = self.types_map[False]
        if ext in types_map:
            return types_map[ext], encoding
        else:
            return None, encoding

def guess_all_extensions(self, type, strict=True):
        type = type.lower()
        extensions = list(self.types_map_inv[True].get(type, []))
        if not strict:
            for ext in self.types_map_inv[False].get(type, []):
                if ext not in extensions:
                    extensions.append(ext)
        return extensions

def guess_extension(self, type, strict=True):
        extensions = self.guess_all_extensions(type, strict)
        if not extensions:
            return None
        return extensions[0]

def read(self, filename, strict=True):
        with open(filename, encoding='utf-8') as fp:
            self.readfp(fp, strict)

def readfp(self, fp, strict=True):
        while 1:
            line = fp.readline()
            if not line:
                break
            words = line.split()
            for i in range(len(words)):
                if words[i][0] == '#':
                    del words[i:]
                    break
            if not words:
                continue
            type, suffixes = words[0], words[1:]
            for suff in suffixes:
                self.add_type(type, '.' + suff, strict)

def read_windows_registry(self, strict=True):
        if not _mimetypes_read_windows_registry and not _winreg:
            return

        add_type = self.add_type
        if strict:
            add_type = lambda type, ext: self.add_type(type, ext, True)

        # Accelerated function if it is available
        if _mimetypes_read_windows_registry:
            _mimetypes_read_windows_registry(add_type)
        elif _winreg:
            self._read_windows_registry(add_type)

@classmethod
def _read_windows_registry(cls, add_type):
        def enum_types(mimedb):
            i = 0
            while True:
                try:
                    ctype = _winreg.EnumKey(mimedb, i)
                except OSError:
                    break
                else:
                    if '\0' not in ctype:
                        yield ctype
                i += 1

        with _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, '') as hkcr:
            for subkeyname in enum_types(hkcr):
                try:
                    with _winreg.OpenKey(hkcr, subkeyname) as subkey:
                        # Only check file extensions
                        if not subkeyname.startswith("."):
                            continue
                        # raises OSError if no 'Content Type' value
                        mimetype, datatype = _winreg.QueryValueEx(
                            subkey, 'Content Type')
                        if datatype != _winreg.REG_SZ:
                            continue
                        add_type(mimetype, subkeyname)
                except OSError:
                    continue
```
Explique moi le role de chaque fonction mais pour mon projet, je n'ai besoin de celui qui definisse l'extension.

- L'appel des fonctions :
```py
def guess_type(url, strict=True):
    if _db is None:
        init()
    return _db.guess_type(url, strict)

def guess_all_extensions(type, strict=True):
    if _db is None:
        init()
    return _db.guess_all_extensions(type, strict)

def guess_extension(type, strict=True):
    if _db is None:
        init()
    return _db.guess_extension(type, strict)

def add_type(type, ext, strict=True):
    if _db is None:
        init()
    return _db.add_type(type, ext, strict)

def init(files=None):
    global suffix_map, types_map, encodings_map, common_types
    global inited, _db
    inited = True    # so that MimeTypes.__init__() doesn't call us again

    if files is None or _db is None:
        db = MimeTypes()
        # Quick return if not supported
        db.read_windows_registry()

        if files is None:
            files = knownfiles
        else:
            files = knownfiles + list(files)
    else:
        db = _db

    for file in files:
        if os.path.isfile(file):
            db.read(file)
    encodings_map = db.encodings_map
    suffix_map = db.suffix_map
    types_map = db.types_map[True]
    common_types = db.types_map[False]
    # Make the DB a global variable now that it is fully initialized
    _db = db

def read_mime_types(file):
    try:
        f = open(file, encoding='utf-8')
    except OSError:
        return None
    with f:
        db = MimeTypes()
        db.readfp(f, True)
        return db.types_map[True]


def _default_mime_types():
    global suffix_map, _suffix_map_default
    global encodings_map, _encodings_map_default
    global types_map, _types_map_default
    global common_types, _common_types_default

    suffix_map = _suffix_map_default = {
        '.svgz': '.svg.gz',
        # Il y en a d'autres dans le vrai fichier `mimetypes.py`
        }

    encodings_map = _encodings_map_default = {
        '.gz': 'gzip',
        # Il y en a d'autres dans le vrai fichier `mimetypes.py`
        }

    # Before adding new types, make sure they are either registered with IANA,
    # at http://www.iana.org/assignments/media-types
    # or extensions, i.e. using the x- prefix

    # If you add to these, please keep them sorted by mime type.
    # Make sure the entry with the preferred file extension for a particular mime type
    # appears before any others of the same mimetype.
    types_map = _types_map_default = {
        '.js'     : 'application/javascript',
        '.movie'  : 'video/x-sgi-movie'
        # Il y en a d'autres dans le vrai fichier `mimetypes.py`
        }

    # These are non-standard types, commonly found in the wild.  They will
    # only match if strict=0 flag is given to the API methods.

    # Please sort these too
    common_types = _common_types_default = {
        '.rtf' : 'application/rtf',
        # Il y en a d'autres dans le vrai fichier `mimetypes.py`
        }


_default_mime_types()
```
- Voici la fonction `main()`:
```py
def _main():
    import getopt

    USAGE = """\
Usage: mimetypes.py [options] type

Options:
    --help / -h       -- print this message and exit
    --lenient / -l    -- additionally search of some common, but non-standard
                         types.
    --extension / -e  -- guess extension instead of type

More than one type argument may be given.
"""

    def usage(code, msg=''):
        print(USAGE)
        if msg: print(msg)
        sys.exit(code)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hle',
                                   ['help', 'lenient', 'extension'])
    except getopt.error as msg:
        usage(1, msg)

    strict = 1
    extension = 0
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-l', '--lenient'):
            strict = 0
        elif opt in ('-e', '--extension'):
            extension = 1
    for gtype in args:
        if extension:
            guess = guess_extension(gtype, strict)
            if not guess: print("I don't know anything about type", gtype)
            else: print(guess)
        else:
            guess, encoding = guess_type(gtype, strict)
            if not guess: print("I don't know anything about type", gtype)
            else: print('type:', guess, 'encoding:', encoding)


if __name__ == '__main__':
    _main()

```
Explique comment ca fonctionne ?
Puis aider-moi a gerer mon propre code, dans mon cas, je veux un code avec une fonction qui donne le type de l'extension entre en input:
Les correspondances se trouvent dans `mime_map.json`:
```jsonl
{
    ".axv": {
        "type": "video/annodex",
        "comment": "Annodex video"
    },
    ".m1u": {
        "type": "video/vnd.mpegurl",
        "comment": "Video playlist"
    },
``` 

