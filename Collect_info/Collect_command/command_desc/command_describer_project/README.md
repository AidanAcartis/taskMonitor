# Linux Command Describer

A CLI tool to describe command-line inputs.

## 1- Installation

There are two main ways to install and use the `command_describer` package: for development or for production/distribution.

---

### Development Installation (Editable Mode)

This method is used while actively developing or testing the package. It allows you to modify the code without reinstalling.

```bash
# Activate this part on describe.py:
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
# Navigate to the project directory

cd command_describer_project

# Install in editable mode
pip install -e .

# Run the CLI
cmddesc

```

**What happens:**

* `pip install -e .` creates a symbolic link in your virtual environment pointing to the source code.
* Any changes in the source code are reflected immediately.
* Useful for development and testing the CLI locally.


### Building and Installing the Package (Production / Distribution)

This method builds distributable files (`.whl` and `.tar.gz`) that can be shared or installed on any machine.

```bash
# Make sure the build module is installed
python -m pip install --upgrade build

# Build the package (creates dist/ folder)
python -m build

# List the generated distribution files
ls dist/
# -> command_describer-0.1.0-py3-none-any.whl
# -> command_describer-0.1.0.tar.gz

# Install the wheel file on the same or another machine
pip install dist/command_describer-0.1.0-py3-none-any.whl

# Run the CLI
cmddesc
```

**What happens:**

* `python -m build` generates a wheel and a source distribution in `dist/`.
* These files can be installed anywhere, without needing the original source folder.
* After installation, the CLI works like any other Python package installed via `pip`.

---

### Summary

| Command            | Purpose                             | When to use                       |
| ------------------ | ----------------------------------- | --------------------------------- |
| `pip install -e .` | Install for development             | Development / local testing       |
| `python -m build`  | Build wheel and source distribution | Production / sharing / publishing |

`Check the MakeFile`

## 2- Structure:

```
command_describer/
│
├── command_describer/          ← 📦 Main package
│   ├── __init__.py
│   ├── main.py                 ← CLI entry point (execution)
│   ├── core/
│   │   ├── tokenizer.py        ← Command tokenization
│   │   ├── matcher.py          ← JSON <-> token matching
│   │   ├── describer.py        ← Building the final description
│   │   ├── file_utils.py       ← JSON I/O, paths, logging
│   │   ├── pattern_expander.py ← Placeholder handling and alternatives
│   │   ├── type_detector.py    ← Argument type detection
│   │   └── constants.py        ← Lists (IP_REGEX, FLAGS, CATEGORIES…)
│   │
│   ├── data/
│   │   ├── dict_json/          ← Existing JSON patterns
│   │   └── config.json         ← Global configuration file
│   
│
├── cmddesc_executable          ← PyInstaller executable (optional)
├── dist/                        ← Distribution files
│
├── Makefile                     ← Build / test / install commands
├── pyproject.toml               ← Package configuration
├── requirements.txt             ← Python dependencies
├── README.md

```

### Files and Functions details:
| File                | Functions / Content                                                                                                                                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| constants.py        | HTTP_METHODS, SERVER, GATEWAY, TCPDUMP_OPTIONS, HYDRA_OPTIONS, ARG_TYPE, INTERFACE_CMDS, TYPE_REGEX, TYPE_DESCRIPTION                                                                                                      |
| tokenizer.py        | safe_shlex_split, is_quoted, looks_like_option, looks_like_subcommand, split_input_by_commands, split_combined_flags, repair_combined_flags_in_command, describe_script_input, normalize_token, tokenize_input_to_elements |
| type_detector.py    | detect_type                                                                                                                                                                                                                |
| file_utils.py       | load_all_jsons, path utilities                                                                                                                                                                                             |
| pattern_expander.py | extract_placeholders, split_top_level_pipes, expand_alternatives, norm_cmd_token_for_match                                                                                                                                 |
| matcher.py          | describe_input_elements                                                                                                                                                                                                    |
| describer.py        | CommandDescriber class, get_data_path, JSON_DIR                                                                                                                                                                            |
| main.py             | main() with CLI loop, input reading, flags repair, command processing and display                                                                                                                                          |


## 3- Code explanation:

The program is a **command-line shell command analyzer and describer**. Its main goal is to take a shell command as input, break it into components, detect their types, and provide human-readable descriptions for each part.

**Key components and workflow:**

1. **Constants & Patterns (`constants.py`)**

   * Defines command categories, options, HTTP methods, network commands, and regex patterns to detect types like files, folders, IP addresses, ports, URLs, scripts, and more.
   * Provides a dictionary `TYPE_DESCRIPTION` for converting detected types into readable labels.

2. **Tokenization (`tokenizer.py`)**

   * Safely splits user input into tokens, handling quotes and separators (`|`, `&&`, `;`, `||`).
   * Splits combined flags (e.g., `-xvz` → `-x -v -z`) while leaving some commands (like `nmap` or `openssl`) intact.
   * Converts input into structured elements (command + subcommands + arguments).

3. **Type Detection (`type_detector.py`)**

   * Detects the type of each token based on regex patterns and context (previous token, main command).
   * Handles files, folders, ports, numbers, URLs, JSON, scripts, Python modules, network targets, and more.

4. **Matching & Description (`matcher.py` & `pattern_expander.py`)**

   * Matches the tokenized command against a JSON-based database of known commands and options.
   * Expands patterns with alternatives (like `{{-v|-verbose}}`) to allow flexible matching.
   * Generates either a **full description** if a complete match is found, or a **sequential description** token by token otherwise.

5. **File Utilities (`file_utils.py`)**

   * Loads all JSON files from the `dict_json` folder into memory as the command reference database.

6. **Main Orchestration (`describer.py`)**

   * `CommandDescriber` class acts as the façade: it orchestrates tokenization, type detection, pattern matching, and description generation.
   * Handles `sudo` commands and multiple commands separated by operators (`&&`, `|`, `;`).
   * Provides an interactive loop via `run()` to continuously analyze user-entered commands.

7. **Entry Point (`main.py`)**

   * Creates a `CommandDescriber` instance and starts the interactive command analysis loop.

---

**In short:**
The program **understands shell commands** by breaking them into elements, **detecting types**, and **matching them against a database of known commands** to produce clear, readable descriptions for each component. It can handle complex command strings, combined flags, scripts, and even multiple piped commands.


