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

# 2- Files and Functions details:
| File                 | Functions / Content                                                                                                                                                                                                                                |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **constants.py**        | `HTTP_METHODS`, `SERVER`, `GATEWAY`, `TCPDUMP_OPTIONS`, `HYDRA_OPTIONS`, `ARG_TYPE`, `INTERFACE_CMDS`, `TYPE_REGEX`, `TYPE_DESCRIPTION`                                                                                                            |
| **tokenizer.py**        | `safe_shlex_split`, `is_quoted`, `looks_like_option`, `looks_like_subcommand`, `split_input_by_commands`, `split_combined_flags`, `repair_combined_flags_in_command`, `describe_script_input`, `normalize_token`, **`tokenize_input_to_elements`** |
| **type_detector.py**    | **`detect_type`**                                                                                                                                                                                                                                  |
| **file_utils.py**       | **`load_all_jsons`**                                                                                                                                                                                                                               |
| **pattern_expander.py** | `extract_placeholders`, `split_top_level_pipes`, `expand_alternatives`, `norm_cmd_token_for_match`                                                                                                                                                 |
| **describer.py**        | **`describe_input_elements`**                                                                                                                                                                                                                      |
| **main.py**             | `main()` (with input reading logic, sudo split, flags repair, loop over commands and display)                                                                                                                                   |
