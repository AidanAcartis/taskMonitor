#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ajoute un champ "id" EN PREMIER dans chaque ligne JSONL.

INPUT  : data1.jsonl
OUTPUT : data1_with_id.jsonl
"""

import json

INPUT_FILE = "activity_data_semantic_clean.jsonl"
OUTPUT_FILE = "DATA_V4_ABSTRACTION.jsonl"


def process_file(input_file, output_file):
    current_id = 0

    with open(input_file, "r", encoding="utf-8") as fin, \
         open(output_file, "w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            data = json.loads(line)

            # reconstruire proprement
            new_data = {
                "id": str(current_id),
                "task_items": data.get("task_items", []),
                "semantic_features": {
                    "actions": data.get("semantic_features", {}).get("actions", []),
                    "objects": data.get("semantic_features", {}).get("objects", [])
                },
                "global_task_intention": data.get("global_task_intention", "")
            }

            fout.write(json.dumps(new_data, ensure_ascii=False) + "\n")
            current_id += 1

    print("✅ Done →", output_file)

if __name__ == "__main__":
    process_file(INPUT_FILE, OUTPUT_FILE)