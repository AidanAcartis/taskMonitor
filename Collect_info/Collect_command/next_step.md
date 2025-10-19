OK, j’ai aussi des listes qui contiennent des commandes au lieu de fichiers, par exemple :

{"command": "pgrep -a xwinwrap", "descriptions": ["list PID and full command line", "Argument 'xwinwrap'"]}
{"command": "kill 3323", "descriptions": ["Terminate a program using the default SIGTERM (terminate) signal", "Number '3323'"]}


Je souhaite regrouper tout cela dans un grand dataset ayant la structure suivante :

{
  "id": ...,
  "type": "file" ou "command",
  "heure_ouverture": ...,
  "heure_fermeture": ...,
  "duree": ...,
  "name": "command ou filename",
  "description": ...
}


À partir de ce dataset, je veux entraîner un modèle pour :

Regrouper les données par activité ou domaine.

Générer un thème (plutôt une phrase décrivant l’activité correspondante à chaque cluster).

Je pensais me baser sur les descriptions pour effectuer ce regroupement.

Questions :

Quel modèle devrais-je entraîner pour ce type de tâche ?

Comment devrais-je procéder concrètement ?