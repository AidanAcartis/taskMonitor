Parfait, tout est clair. Voici ma proposition complète avant qu'on commence à coder.

---

**Choix technologiques**

Pour un logiciel desktop Linux avec icône, notifications système, et graphiques riches, la meilleure combinaison est **Python + PyQt6**. PyQt6 te donne une vraie app desktop native Linux (icône dans le tray, notifications, fenêtres), les graphiques avec `pyqtgraph` ou `matplotlib` embarqué, et tout reste en Python comme ton pipeline existant. C'est aussi packagable avec `PyInstaller` pour déploiement sur d'autres machines.Voici maintenant l'architecture de fichiers concrète et la structure du projet :Et voici comment ça fonctionne de bout en bout, du démarrage jusqu'aux graphiques :---

**Réponses à tes questions**

**Quel langage ?** Python avec PyQt6 pour l'UI. C'est le choix le plus cohérent parce que tout ton pipeline est déjà en Python, tu gardes le même environnement conda, et PyQt6 donne une vraie app desktop Linux avec icône, tray, notifications natif via `dbus`.

**Comment structurer ?** Le principe central est la séparation en couches : `core/` ne dépend de rien d'autre, `collectors/` et `processing/` ne connaissent pas l'UI, `gui/` ne fait que appeler l'orchestrateur et afficher les résultats. L'orchestrateur est le seul à connaître l'ordre du pipeline.

**Comment déployer sur une autre machine ?** Deux options selon le cas. Pour une machine Ubuntu similaire, tu fournis un script `setup_env.sh` qui crée le conda env, installe les dépendances, et installe le `.desktop` file. Pour une machine sans Python du tout, tu utilises `PyInstaller` pour créer un exécutable autonome `.AppImage` qui embarque Python et toutes les libs. Les modèles IA ne peuvent pas être embarqués (trop lourds), donc on prévoit un dossier `models/` séparé à copier manuellement, avec un chemin configurable dans `config.py`.

**Conservation des données historiques** : chaque journée sera stockée dans `data/processed/YYYY-MM-DD/` et `data/exports/YYYY-MM-DD/`. L'interface permettra de sélectionner une date passée pour consulter son historique.

---

**Plan de travail proposé**

On va procéder dans cet ordre : d'abord créer la structure de base du projet avec `pyproject.toml` et `core/config.py`, ensuite refactoriser chaque script existant en module propre, puis construire l'orchestrateur, et enfin l'interface PyQt6.

Tu veux qu'on commence maintenant par la création de la structure de fichiers et du `core/` ? Je peux générer tous les fichiers de base du projet directement.