from pathlib import Path
import os

#File source
BASE_DIR = Path(__file__).parent

file1 = BASE_DIR / "../COLLECT_FILE_DATA/COLLECT_FILE_LOGS/data_file.txt"
file2 = BASE_DIR / "../COLLECT_COMMAND_LOGS/data_command.txt"
output_file = BASE_DIR / "../PROCESSING/DATA_COLLECT/data_collect.txt"

# Store formatted line
lines=[]

#file1 traitment
with file1.open(encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 6:
            date = parts[0]
            time_open = parts[1]
            time_close = parts[2]
            duration = parts[3]
            type_ = parts[4]
            name = " ".join(parts[5:])
            lines.append(f"{date}\t{time_open}\t{time_close}\t{duration}\t{type_}\t{name}")


#file2 traitment
with file2.open(encoding="utf-8") as f:
    for line in f:
        parts = [x.strip() for x in line.strip().split(",")]
        if len(parts) >= 6:
            date = parts[0]
            time_open = parts[1]
            time_close = parts[2]
            duration = parts[3]
            type_ = parts[4]
            name = " ".join(parts[5:])
            lines.append(f"{date}\t{time_open}\t{time_close}\t{duration}\t{type_}\t{name}")

#THe final file in TSV
with output_file.open("w", encoding="utf-8") as f:
    for line in lines:
        f.write(line + "\n")

print(f"the TSV file is generated : {output_file.resolve()}")



