# Critères de rédaction des listes de tâches

## Niveau méso / global (pas micro)

Chaque ligne doit décrire une activité complète ou un ensemble cohérent d’actions observables, et non une action ponctuelle isolée.

Exemple acceptable :  
- *Use the web and online tools to search for information, watch instructional videos, and plan activities*

Exemple à éviter :  
- *Browsed the web to search for cooking recipes*

---

## Précis sans entrer dans les détails techniques internes

La description ne doit pas détailler précisément les éléments techniques utilisés (structure interne, boutons exacts, couleurs, en-têtes, etc.).

L’objectif est de pouvoir déduire l’activité à partir des traces observables sur l’ordinateur (fichiers ouverts, commandes exécutées, logiciels utilisés), sans supposer les choix précis effectués par l’utilisateur.

---

## Activité observable à partir d’actions réelles

Chaque tâche doit être identifiable à partir de traces concrètes laissées sur la machine : fichiers modifiés, dossiers parcourus, commandes lancées, applications utilisées.

Exemple :  
- *Debug, test, and troubleshoot code across multiple environments*

Il doit être possible de regrouper plusieurs actions unitaires sous une seule description d’activité.

---

## Utilisation de verbes à l’infinitif

Toutes les descriptions doivent être formulées à l’infinitif afin d’assurer l’uniformité et la cohérence du dataset.

Exemple :  
- *Manage installed software by adding, updating, or removing applications*

---

## Absence de “or” dans les formulations

Chaque activité doit décrire une action concrète et unique, et non une alternative ou un choix possible entre plusieurs options.

---

## Regrouper les micro-actions en une activité cohérente

Une tâche doit englober plusieurs actions élémentaires liées par un même objectif ou un même contexte.

Par exemple, la modification de plusieurs fichiers, l’exécution de commandes et le redémarrage d’un service peuvent être regroupés sous :  
- *Debug, test, and troubleshoot code across multiple environments*

---

## Adapté à l’entraînement du modèle Flan-T5

Chaque tâche doit pouvoir être synthétisée en une description que le modèle peut apprendre à générer à partir d’un ensemble de fichiers ouverts, de commandes exécutées et d’applications utilisées.

L’objectif est de permettre au modèle de généraliser correctement à partir de clusters d’actions observables.
