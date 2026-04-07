import re

def parse_clusters(filepath: str) -> list:
    clusters = []
    current  = None

    header_re = re.compile(
        r"^(Cluster\s+\d+|Other\s+small\s+tasks|Autres\s+petites\s+t[aâ]ches)"
        r"\s*\|\s*(\d+)\s+(?:task|t[aâ]che)\(s\)"
        r"\s*\|\s*coh(?:esion|[eé]sion)\s*=\s*([\d.]+)",
        re.IGNORECASE,
    )

    item_re = re.compile(r"^\s*[•\-\*]\s+(.+)$")

    with open(filepath, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip()

            m = header_re.search(line)
            if m:
                if current:
                    clusters.append(current)

                current = {
                    "cluster_id": m.group(1).strip(),
                    "num_tasks":  int(m.group(2)),
                    "cohesion":   float(m.group(3)),
                    "items":      [],
                }
                continue

            if current:
                m2 = item_re.match(line)
                if m2:
                    current["items"].append(m2.group(1).strip())

    if current:
        clusters.append(current)

    # Expansion des "Other small tasks"
    expanded = []
    for c in clusters:
        if re.search(r"(other\s+small\s+tasks|autres\s+petites\s+t[aâ]ches)", c["cluster_id"], re.IGNORECASE):
            for idx, item in enumerate(c["items"]):
                expanded.append({
                    "cluster_id": f"Other small tasks — singleton {idx + 1}",
                    "num_tasks":  1,
                    "cohesion":   c["cohesion"],
                    "items":      [item],
                    "is_singleton": True,
                })
        else:
            c.setdefault("is_singleton", False)
            expanded.append(c)

    return expanded