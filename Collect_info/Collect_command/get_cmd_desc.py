import json
import subprocess

input_file = "100_unique_commands.txt"
output_file = "commands_descriptions_1.jsonl"

with (
    open(input_file, "r", encoding="utf-8") as f_in,
    open(output_file, "w", encoding="utf-8") as f_out
):
    for line in f_in:
        if "Command," not in line:
            continue

        # Extract the command after 'Command,'
        parts = line.strip().split("Command,")
        if len(parts) < 2:
            continue
        command = parts[1].strip()

        # Execute cmddesc
        try:
            process = subprocess.run(
                ["cmddesc"],
                input=f"{command}\n",
                text=True,
                capture_output=True,
                timeout=10
            )
            output = process.stdout

        except subprocess.TimeoutExpired:
            output = "Error: Timeout"
        except Exception as e:
            output = f"Error: {e}"

        # Extract the description
        descriptions = []
        if "Descriptions found:" in output:
            blocks = output.split("Descriptions found:")
            for block in blocks[1:]:
                lines = block.strip().splitlines()
                for l in lines:
                    l = l.strip()
                    if l.startswith("desc_") or l.startswith("desc_cmd"):
                        parts = l.split(":", 1)
                        if len(parts) == 2:
                            desc_text = parts[1].strip()
                            if desc_text:
                                descriptions.append(desc_text)

        # If a description was found
        if not descriptions:
            descriptions = ["No description was found."]

        # Write on the jsonl file
        json_line = json.dumps({
            "command": command,
            "descriptions": descriptions
        }, ensure_ascii=False)
        f_out.write(json_line + "\n")

print(f"Jsonl file created : {output_file}")