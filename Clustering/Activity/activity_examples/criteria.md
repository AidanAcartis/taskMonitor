Critères pour les listes de tâches

Niveau méso/global, pas micro

Chaque ligne doit décrire une activité complète ou un cluster d’actions observables, pas une seule action ponctuelle.

Exemple : “Use the web and online tools to search for information, watch instructional videos, and plan activities” ✅

À éviter : “Browsed the web to search for cooking recipes” ❌

Précis mais pas trop détaillé sur la structure interne

Ne pas décrire ce qu’il a exactement fait dans le détail technique (pas de header, footer, boutons exacts, couleurs…)

L’idée : on peut déduire l’activité à partir des fichiers ouverts, commandes exécutées, ou logiciels utilisés, mais pas deviner ses choix précis.

Observable à partir d’actions réelles

La tâche doit être visible via les traces sur l’ordinateur : fichiers ouverts, dossiers modifiés, commandes lancées, applications utilisées.

Exemple : “Debug, test, and troubleshoot code across multiple environments”

On doit pouvoir regrouper un cluster d’actions singulières sous cette description.

Verbes à l’infinitif

Pour uniformité et clarté dans le dataset.

Exemple : “Manage installed software by adding, updating, or removing applications”

Pas d’“or” dans la formulation

Chaque activité doit être une description unique d’actions concrètes, pas une liste de possibilités ou alternatives.

Regrouper plusieurs micro-actions en une seule activité cohérente

Une activité doit englober plusieurs actions singulières reliées par un même objectif ou contexte.

Exemple : plusieurs fichiers modifiés, commandes lancées, serveur redémarré → “Debug, test, and troubleshoot code across multiple environments”

Applicable pour ton modèle Flan-T5

La tâche doit être synthétisable en une description que le modèle peut apprendre à générer à partir d’un cluster de fichiers, commandes et applications.