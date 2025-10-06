* Si le type est `file-directory-app` , alors le modèle doit:
- transformer en phrase le nom du fichier 
- Dire dans quel directory il se trouve
- Dire dans quel App il est ouvert
##### => Problème:
- Le modèle parle de ses limites et des choses qu'on ne lui demande pas dans le prompt
- Parfois, la phrase qu'il donne n'a rien à voir avec le nom du fichier
- La transformation en phrase est erronée il faut l'optimiser ou changer de modèle plus performant
- Un fichier mal nommé devient plus difficile à deviner
- Ceci `Google Calendar - Week of July 20, 2025 - Google Chrome` est un exemple de `file-directory-app` mais `Week of July 20, 2025` n'est pas un directory alors que 
- Mais le modèle PHI reconnaît bien les commandes linux et les noms communs