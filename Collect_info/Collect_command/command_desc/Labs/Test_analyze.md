J'ai un dosssier `dict_json` contenant les fichiers suivant :
```bash
idan@aidan-Lenovo-N50-70:~/Documents/Projects/Vis/Collect_info/Collect_command/command_desc/dict_json$ ls
android.json    common.json   linux.json   openbsd.json  sunos.json
cisco-ios.json  freebsd.json  netbsd.json  osx.json      windows.json
```
chaque fichier contient des commandes avec sa description:
    "description": "specify the DIRECTORY in which to create the links",
      "cmds": [
        "ln -t <path>",
        "ln --target-directory=DIRECTORY <path>"
      ]
    },
    {
      "description": "treat LINK_NAME as a normal file always",
      "cmds": [
        "ln -T <path>",
        "ln --no-target-directory <path>"
      ]
    },
    {
      "description": "print name of each linked file --help        display this help and exit --version     output version information and exit",
      "cmds": [
        "ln -v <path>",
        "ln --verbose <path>"
      ]
    },
    {
      "description": "like --backup but does not accept an argument",
      "cmd": "ln -b"
    },
    {
      "description": "(note: will probably fail due to",
      "cmd": "ln directories"
    },
    {
      "description": "restrictions, even for the superuser)",
      "cmd": "ln system"
    },
    {
      "description": "is a symbolic link to a directory",
      "cmd": "ln it"
    },
    {
      "description": "links",
      "cmd": "ln the"
    },
    {
      "description": "display this help and exit",
      "cmd": "ln --help"
    },
    {
      "description": "output version information and exit",
      "cmd": "ln --version"
    }
  ],
  "ls": [
    {
      "description": "List files one per line",
      "cmd": "ls -1"
    },
    {
      "description": "List all files, including hidden files",
      "cmd": "ls {{[-a|--all]}}"
    },
    {
      "description": "List files with a trailing symbol to indicate file type (directory/, symbolic_link@, executable*, ...)",
      "cmd": "ls {{[-F|--classify]}}"
    },
    {
      "description": "List all files in [l]ong format (permissions, ownership, size, and modification date)",
      "cmd": "ls {{[-la|-l --all]}}"
    },
    {
      "description": "List files in [l]ong format with size displayed using human-readable units (KiB, MiB, GiB)",
      "cmd": "ls {{[-lh|-l --human-readable]}}"
    },
    {
      "description": "List files in [l]ong format, sorted by [S]ize (descending) recursively",
      "cmd": "ls {{[-lSR|-lS --recursive]}}"

Je veux creer un programme qui prend en entre une commande, le programme va chercher dans les fichiers json le cmd qui correspond a l'input et renvoie la description.
Voici comment le faire:
1- Le programme prend la commande et specifie la commande principale(ls, cd, git, node, nmap,...)
2- Puis il doit detecter rapidement ou se trouve cette commande dans les fichiers(la section des ls, cd, git, node, nmap, ...)
3- On decompose l'input en la composition des commandes et fichiers, nom, nombre, ip, .... Exemple:
input: `ls -l /home/user -a`
decomposition:
el_1: `ls -l`
el_2: `/home/user`
el_3: `ls -a`
4 - On prend aussi tous les enfants (cmd) de la commande principale et on les decompose, exemple:
  "ls": [
    {
      "description": "List files one per line",
      "cmd": "ls -1" => un element 
    },
    {
      "description": "List all files, including hidden files",
      "cmd": "ls {{[-a|--all]}}" => ["ls -a" ou ls -all]
    },

  "curl": [
    {
      "description": "Make an HTTP GET request and dump the contents in `stdout`",
      "cmd": "curl {{https://example.com}}" => un element
    },
    {
      "description": "Make an HTTP GET request, follow any `3xx` redirects, and dump the reply headers and contents to `stdout`",
      "cmd": "curl {{[-L|--location]}} {{[-D|--dump-header]}} - {{https://example.com}}"

      => ["curl -L ou curl --location", "curl -D ou curl --dump-header", "- https://example.com"] 3 elements
    },
5- Maintenant, On check sur tous elements de tous les cmd enfants de la commande principale(on enleve ceux qui ne sont pas des commandes dans les elements):
  - Si le nombre d'element du cmd = 1 et qu'il est present dans l'input, on prend sa description correspondant et on stocke dans desc_1.
  - Si c'est > 1, on check les elements de l'input dans les elements du cmd, a chaque fois qu'on trouve une presence on donne un score
  - Si le score atteint 100% on prend la description correspondate et on le renvoie comme output, sinon on renvoie les desc_i dans l'ordre comme output.

  POur les el_i de l'input, si l'element n'est pas une commande, alors on le determine:
  /home/user: directory 'home/user'
  server.js: file server.js
  192.188.88.1: IP 192.188.88.1
  433: port 433
  3: number 3
  ...
  => on les stocke dans desc_i