import subprocess
import re

NOISE_PREFIXES = (
    "Command '", "Argument '", "String '",
    "Number '", "IP address '", "URL '", "JSON '",
    "File '", "Folder '", "Server '",
)

def run_cmddesc(command: str) -> str:
    result = subprocess.run(
        ["cmddesc"], input=command, capture_output=True, text=True
    )
    return result.stdout

def parse_cmddesc_output(raw_output: str) -> str:
    def is_noise(value: str) -> bool:
        return any(value.startswith(p) for p in NOISE_PREFIXES)

    def extract_value(line: str) -> str:
        return re.sub(r"^(desc_\w+|with sudo privilege):\s*", "", line.strip()).strip()

    sub_commands, current, mode = [], [], None

    for line in raw_output.splitlines():
        s = line.strip()

        if re.match(r"^=== Command \d+", s):
            if current:
                sub_commands.append(" + ".join(current))
            current, mode = [], None

        elif "FULL DESCRIPTION APPLIED" in s:
            mode = "full"

        elif "DESCRIPTION SEQUENTIELLE" in s:
            mode = "sequential"

        elif re.match(r"^(desc_|with sudo)", s):
            value = extract_value(s)
            if not value or is_noise(value):
                continue
            if mode == "full":
                if s.lstrip().startswith("desc_cmd"):
                    current.insert(0, value)
                else:
                    current.append(value)
            elif mode == "sequential":
                current.append(value)

    if current:
        sub_commands.append(" + ".join(current))

    result = " | ".join(sub_commands) if sub_commands else "No description found"

    # Nettoyer les préfixes résiduels de cmddesc
    result = re.sub(r"\bdesc_\w+:\s*", "", result).strip()
    result = re.sub(r"\s*\+\s*-\s*", ", ", result)
    result = re.sub(r"Command\s+'[^']+'\s*\+?\s*", "", result).strip()
    result = re.sub(r"^\s*-\s*", "", result).strip()   # tiret résiduel en début
    result = re.sub(r",\s*,", ",", result).strip()     # double virgule
    result = re.sub(r",\s*$", "", result).strip()      # virgule finale
    result = re.sub(r"\s{2,}", " ", result).strip()

    return result if result else "No description found"

def describe_command(command: str) -> str:
    command = command.strip()
    if not command:
        return ""
    try:
        return parse_cmddesc_output(run_cmddesc(command))
    except Exception as e:
        return f"[ERROR: {e}]"