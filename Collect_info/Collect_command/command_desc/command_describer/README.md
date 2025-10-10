# 1- Structure:

```
command_describer/
│
├── command_describer/          ← 📦 Package principal
│   ├── __init__.py
│   ├── main.py                 ← Point d’entrée CLI (exécution)
│   ├── core/
│   │   ├── tokenizer.py        ← Tokenisation des commandes
│   │   ├── matcher.py          ← Matching JSON <-> tokens
│   │   ├── describer.py        ← Construction de la description finale
│   │   ├── file_utils.py       ← Lecture/écriture JSON, chemins, logs
│   │   └── constants.py        ← Listes (IP_REGEX, FLAGS, CATEGORIES…)
│   │
│   ├── data/
│   │   ├── dict_json/          ← Tes JSON existants (patterns)
│   │   └── config.json         ← Fichier de configuration globale
│   │
│   └── ml/
│       ├── model.py            ← Ton modèle ML s’il y en a un
│       └── preprocessing.py    ← Traitement de texte pour le modèle
│
├── tests/                      ← ✅ Tests unitaires
│   ├── test_tokenizer.py
│   ├── test_matcher.py
│   └── test_integration.py
│
├── setup.py                    ← Script d’installation (`pip install .`)
├── pyproject.toml              ← (optionnel, si tu veux Poetry)
├── requirements.txt            ← Dépendances Python
├── README.md
└── Makefile                    ← Pour les commandes build/test/install
```