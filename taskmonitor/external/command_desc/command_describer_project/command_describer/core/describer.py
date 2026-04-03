import sys
from .file_utils import load_all_jsons
from .tokenizer import split_input_by_commands, tokenize_input_to_elements
from .matcher import describe_input_elements, repair_combined_flags_in_command
from pathlib import Path
import importlib.resources as pkg_resources

# JSON_DIR = Path(__file__).resolve().parent.parent / "data" / "dict_json"

# ============== install your package in development mode ==============

# def get_data_path(subpath=""):
#     """Return correct path to data folder (works in dev and frozen PyInstaller binary)."""
#     if getattr(sys, "frozen", False):  # PyInstaller bundle
#         base_path = Path(sys._MEIPASS)
#     else:
#         base_path = Path(__file__).resolve().parent.parent / "data"
#     return base_path / subpath

# # Replace JSON_DIR by
# JSON_DIR = get_data_path("dict_json")

# ============== build package distributions for distribution/release ==============

def get_data_path(subpath=""):
    """
    Return correct path to data folder:
    - works in dev (normal folder)
    - works when installed via pip (inside wheel)
    """
    try:
        # works in pip-installed package
        # .files() gives a Traversable object
        dict_json_path = pkg_resources.files("command_describer").joinpath("data/dict_json")
        if subpath:
            dict_json_path = dict_json_path.joinpath(subpath)
        return dict_json_path
    except Exception:
        # fallback: dev mode
        return Path(__file__).resolve().parent.parent / "data" / "dict_json" / subpath

# JSON_DIR points to the dict_json folder
JSON_DIR = get_data_path("")


class CommandDescriber:
    """Classe façade : orchestre l’analyse et la description d’une commande shell."""

    def __init__(self, json_dir: Path = JSON_DIR):
        self.json_dir = json_dir
        self.db = load_all_jsons(self.json_dir)
        if not self.db:
            print(f"No JSON files loaded from {self.json_dir}")

    def analyze_command(self, user_input: str):
        """Analyse une commande complète et retourne ses descriptions."""

        if not user_input.strip():
            print("Empty input.")
            return
        

        # ----------------------------
        # Check for sudo prefix
        # ----------------------------
        has_sudo = False
        if user_input.startswith("sudo "):
            has_sudo = True
            user_input = user_input[5:].strip()  # remove 'sudo ' from the input


        # Split the input into multiple commands
        commands = split_input_by_commands(user_input)

        # Fix combined flags in each command
        commands = [repair_combined_flags_in_command(c) for c in commands]


        for idx, cmd in enumerate(commands):
            print(f"\n=== Command {idx+1} ===")
            input_elems = tokenize_input_to_elements(cmd)

            print("Element analysis:")
            for i, e in enumerate(input_elems):
                print(f"  el_{i}: {e}")

            results = describe_input_elements(input_elems, self.db)

            if has_sudo and results:
                results[0] = f"with sudo privilege: {results[0]}"

            print("Descriptions found:")
            for r in results:
                print(" ", r)


    def run(self):
        """Boucle interactive (comme ton ancien main())."""
        # while True:
        user_input = input("Enter command: ").strip()
        if not user_input:
            print("Bye.")
                # break
        self.analyze_command(user_input)

