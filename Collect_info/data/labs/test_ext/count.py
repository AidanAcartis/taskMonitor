import os

MIME_DIR = "/usr/share/mime"

def count_xml_per_dir(base_dir=MIME_DIR):
    counts = {}
    total = 0
    for entry in os.scandir(base_dir):
        if entry.is_dir():
            xml_files = [f for f in os.listdir(entry.path) if f.endswith(".xml")]
            counts[entry.name] = len(xml_files)
            total += len(xml_files)
    return counts, total


if __name__ == "__main__":
    result, total = count_xml_per_dir()
    for dirname, count in result.items():
        print(f"{dirname}: {count} fichiers XML")
    
    print(f"\nTotal: {total} fichiers XML")
