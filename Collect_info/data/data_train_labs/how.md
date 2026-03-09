## My data:
J'ai scraper les descriptions de mon dataset sur chatGPT:

{"id": "10", "filename": "try_script", "extension": "sh", "directory": "all_script", "application": "Visual Studio Code", "description": "This is a shell script (.sh) named try_script located in the all_script directory. It likely serves as a test or experimental script and can be opened with Visual Studio Code."}

{"id": "647", "filename": "default_parameters_template_backup_helper_tool_helper_tool", "extension": "cfg", "directory": "configs", "application": "Visual Studio Code", "description": "The file is a configuration file, as indicated by its .cfg extension, serving as a template for default parameters, as suggested by its name \"default_parameters_template_backup_helper_tool_helper_tool.\" It is located in the \"configs\" directory and can be opened in Visual Studio Code for editing and configuration management."}

{"id": "733", "filename": "user_manual_guide_reference_doc", "extension": "md", "directory": "all_script", "application": "Visual Studio Code", "description": "The file with a .md extension is a markdown document named user_manual_guide_reference_doc. It is located in the all_script directory and is opened using Visual Studio Code, likely containing a reference guide for a user manual."}

{"id": "1296", "filename": "db_setup_initializer_script_helper_tool_script", "extension": "py", "directory": "utils", "application": "PyCharm", "description": "This is a .py file, a Python script, and according to its name db_setup_initializer_script_helper_tool_script, it helps initialize and set up a database. It is located in the utils folder and can be opened with PyCharm."}

{"id": "1808", "filename": "default_parameters", "extension": "cfg", "directory": "configs", "application": "Sublime Text", "description": "The file is a configuration file (.cfg) named default_parameters located in the configs folder. It likely contains default settings or parameters for an application or system, and can be opened and edited in Sublime Text."}

Il semble que chatGPT donne des descriptions completes en parlant un peu plus loin avec des mots
qui ne vient de `filename`.

J'ai 2010 datasets pour fine-tune `Flan-T5-small` mais je ne sais pas si le fine-tune serait capable
d'etendre la description en parlant des champs lexicaux autour du filename.

Le modele obtenu va donner comme resultat la description donc le resultat est comme :

{"id": "2002", "filename": "settings", "extension": "json", "directory": "configs", "application": "Google Chrome", "description": "The file is a JSON (.json) document that likely contains configuration settings for an application or system, such as preferences or options. It is located in the \"configs\" directory and can be opened in Google Chrome, which displays JSON data in a structured and readable format."}

depuis ce genre de input:

{"id": "2002", "filename": "settings", "extension": "json", "directory": "configs", "application": "Google Chrome"}

Alors est-ce que le fine-tune peut reussir ?

## Prompt :
Voici le prompt dont j'ai donne a chatGPT:

prompt_template = """
Describe the following file in 2 sentences maximum. Include: what it is according to the extension ({ext}), what he does according to his name ({fname}), where it is located ({directory}), which application opens it ({app})
"""

Je veux entrainner mon modele a donne notre resultat a partir de ce prompt, les inputs comme
: {ext}, {fname}, {directory} et {app} seront presente dans un seule ligne comme ceci dans un fichier jsonl:

{"id": "2002", "filename": "settings", "extension": "json", "directory": "configs", "application": "Google Chrome"}

- C'est clair et facile pour le directory 
- Pour l'extension, je vais cree une librairie extension + definition et le modele ferait un reference avec
- Le modele se focuse principalement a fournir une description a partir du filename et de combiner le tout pour repondre a prompt_template.

Comment realiser cela vu mon dataset ?