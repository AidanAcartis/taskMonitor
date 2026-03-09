# Regroupement de fichiers et de commandes pour l’analyse d’activités

J’ai également des listes qui contiennent **des commandes système**, et pas uniquement des fichiers.  
Par exemple :

```json
{"command": "pgrep -a xwinwrap", "descriptions": ["list PID and full command line", "Argument 'xwinwrap'"]}
{"command": "kill 3323", "descriptions": ["Terminate a program using the default SIGTERM (terminate) signal", "Number '3323'"]}
````

Mon objectif est de **regrouper toutes ces informations dans un dataset unique**, avec une structure homogène, quel que soit le type d’élément (fichier ou commande).

---

## Structure cible du dataset

Je souhaite obtenir un dataset ayant la forme suivante :

```json
{
  "id": "...",
  "type": "file" ou "command",
  "heure_ouverture": "...",
  "heure_fermeture": "...",
  "duree": "...",
  "name": "nom du fichier ou commande exécutée",
  "description": "description textuelle de l’action"
}
```

Cette structure me permet :

* d’unifier les fichiers et les commandes,
* de conserver le contexte temporel,
* de m’appuyer sur une description textuelle exploitable par un modèle.

---

## Objectifs du modèle

À partir de ce dataset, je veux entraîner un modèle capable de :

1. **Regrouper les données par activité ou par domaine**
   Exemple : développement logiciel, administration système, navigation web, gestion de processus.

2. **Générer un thème pour chaque groupe**, sous forme d’une phrase décrivant l’activité globale correspondant au cluster.

L’idée n’est pas de décrire chaque action individuellement, mais de **résumer un ensemble d’actions cohérentes**.

---

## Approche générale envisagée

Je compte me baser principalement sur le champ `description`, car :

* il est présent aussi bien pour les fichiers que pour les commandes,
* il capture l’intention de l’action plutôt que son implémentation brute,
* il est directement exploitable par des modèles de langage.

---

## Choix du modèle

Pour ce type de tâche, je distingue deux étapes :

### 1. Regroupement par activité (clustering)

Je n’entraîne pas directement un modèle supervisé.
Je procède plutôt ainsi :

* utiliser un **modèle de sentence embeddings** pour transformer les descriptions en vecteurs,
* appliquer un **algorithme de clustering** pour regrouper les actions similaires.

Modèles adaptés pour les embeddings :

* Sentence-BERT (`all-MiniLM-L6-v2`, `all-mpnet-base-v2`)
* modèles équivalents multilingues si nécessaire

Algorithmes de clustering adaptés :

* HDBSCAN (robuste, pas besoin de fixer le nombre de clusters)
* DBSCAN ou KMeans (moins flexibles)

---

### 2. Génération du thème par cluster

Une fois les clusters obtenus, j’entraîne un **modèle génératif texte-à-texte** pour produire une phrase décrivant l’activité du cluster.

Modèle recommandé :

* Flan-T5 (small ou base selon les ressources)

Entrée du modèle :

* la liste ou la concaténation des descriptions d’un cluster

Sortie du modèle :

* une phrase synthétique décrivant l’activité globale

Exemple attendu :

> “Debug, monitor, and manage running system processes and applications”

---

## Procédure concrète

1. Normaliser les données (fichiers et commandes) dans une structure commune.
2. Générer des embeddings à partir du champ `description`.
3. Appliquer un clustering non supervisé pour regrouper les actions.
4. Construire un dataset de clusters (liste de descriptions par cluster).
5. Entraîner ou fine-tuner un modèle Flan-T5 pour générer un thème par cluster.
6. Associer chaque cluster à son thème généré.

---

## Résultat attendu

À la fin du pipeline :

* chaque action (fichier ou commande) appartient à un cluster,
* chaque cluster est associé à une phrase décrivant l’activité correspondante,
* le système est extensible à de nouveaux types d’actions sans changer la structure.

---

