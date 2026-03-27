import json
import re
from collections import Counter

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
INPUT_JSONL  = "activity_data_final.jsonl"
OUTPUT_JSONL = "activity_data_final_v2.jsonl"

# ─────────────────────────────────────────────
# RÈGLES DE REMPLACEMENT
# "and manage" → verbe plus précis selon le contexte
# Format : (pattern_regex, remplacement)
# Appliqué dans l'ordre — le premier match gagne
# ─────────────────────────────────────────────
REPLACEMENT_RULES = [
    # monitor and manage → monitor + verbe précis selon le sujet
    (r"monitor and manage (.*log.*)",            r"monitor and analyze \1"),
    (r"monitor and manage (.*alert.*)",          r"monitor and respond to \1"),
    (r"monitor and manage (.*infrastructure.*)", r"monitor and maintain \1"),
    (r"monitor and manage (.*resource.*)",       r"monitor and optimize \1"),
    (r"monitor and manage (.*performance.*)",    r"monitor and improve \1"),
    (r"monitor and manage (.*security.*)",       r"monitor and enforce \1"),
    (r"monitor and manage (.*network.*)",        r"monitor and troubleshoot \1"),
    (r"monitor and manage (.*service.*)",        r"monitor and maintain \1"),
    (r"monitor and manage (.*pipeline.*)",       r"monitor and maintain \1"),
    (r"monitor and manage (.*data.*)",           r"monitor and process \1"),
    (r"monitor and manage (.*)",                 r"monitor and maintain \1"),

    # configure and manage → configure + verbe précis
    (r"configure and manage (.*auth.*)",         r"configure and secure \1"),
    (r"configure and manage (.*security.*)",     r"configure and enforce \1"),
    (r"configure and manage (.*cache.*)",        r"configure and optimize \1"),
    (r"configure and manage (.*analytics.*)",    r"configure and track \1"),
    (r"configure and manage (.*email.*)",        r"configure and integrate \1"),
    (r"configure and manage (.*environment.*)",  r"configure and secure \1"),
    (r"configure and manage (.*cdn.*)",          r"configure and deploy \1"),
    (r"configure and manage (.*network.*)",      r"configure and maintain \1"),
    (r"configure and manage (.*server.*)",       r"configure and deploy \1"),
    (r"configure and manage (.*database.*)",     r"configure and maintain \1"),
    (r"configure and manage (.*api.*)",          r"configure and expose \1"),
    (r"configure and manage (.*deploy.*)",       r"configure and automate \1"),
    (r"configure and manage (.*storage.*)",      r"configure and maintain \1"),
    (r"configure and manage (.*backup.*)",       r"configure and automate \1"),
    (r"configure and manage (.*log.*)",          r"configure and monitor \1"),
    (r"configure and manage (.*)",               r"set up and configure \1"),

    # develop and manage → develop + verbe précis
    (r"develop and manage (.*frontend.*)",       r"develop and maintain \1"),
    (r"develop and manage (.*backend.*)",        r"develop and deploy \1"),
    (r"develop and manage (.*api.*)",            r"develop and document \1"),
    (r"develop and manage (.*extension.*)",      r"develop and publish \1"),
    (r"develop and manage (.*pipeline.*)",       r"develop and automate \1"),
    (r"develop and manage (.*)",                 r"develop and maintain \1"),

    # implement and manage → implement + verbe précis
    (r"implement and manage (.*auth.*)",         r"implement and enforce \1"),
    (r"implement and manage (.*security.*)",     r"implement and enforce \1"),
    (r"implement and manage (.*cache.*)",        r"implement and optimize \1"),
    (r"implement and manage (.*workflow.*)",     r"implement and automate \1"),
    (r"implement and manage (.*)",               r"implement and maintain \1"),

    # validate and manage → validate + verbe précis
    (r"validate and manage (.*data.*)",          r"validate and process \1"),
    (r"validate and manage (.*config.*)",        r"validate and enforce \1"),
    (r"validate and manage (.*)",                r"validate and maintain \1"),

    # audit and manage → audit + verbe précis
    (r"audit and manage (.*security.*)",         r"audit and enforce \1"),
    (r"audit and manage (.*access.*)",           r"audit and control \1"),
    (r"audit and manage (.*compliance.*)",       r"audit and enforce \1"),
    (r"audit and manage (.*)",                   r"audit and remediate \1"),

    # create and manage → create + verbe précis
    (r"create and manage (.*report.*)",          r"create and distribute \1"),
    (r"create and manage (.*template.*)",        r"create and maintain \1"),
    (r"create and manage (.*content.*)",         r"create and publish \1"),
    (r"create and manage (.*)",                  r"create and maintain \1"),

    # coordinate and manage → simplement reformuler
    (r"coordinate and manage (.*project.*)",     r"coordinate and deliver \1"),
    (r"coordinate and manage (.*team.*)",        r"coordinate and support \1"),
    (r"coordinate and manage (.*)",              r"coordinate and oversee \1"),

    # organize and manage
    (r"organize and manage (.*)",                r"organize and maintain \1"),

    # design and manage
    (r"design and manage (.*)",                  r"design and implement \1"),

    # track and manage
    (r"track and manage (.*)",                   r"track and report \1"),

    # enforce and manage
    (r"enforce and manage (.*)",                 r"enforce and monitor \1"),

    # automate and manage
    (r"automate and manage (.*)",                r"automate and maintain \1"),

    # set up and manage
    (r"set up and manage (.*)",                  r"set up and maintain \1"),

    # deploy and manage
    (r"deploy and manage (.*)",                  r"deploy and maintain \1"),

    # fallback générique — tout autre "X and manage"
    (r"(\w+) and manage (.*)",                   r"\1 and maintain \2"),
]


def rebalance_label(label: str) -> str:
    """Applique les règles de remplacement sur un label."""
    lower = label.lower()
    if " and manage" not in lower:
        return label

    for pattern, replacement in REPLACEMENT_RULES:
        new_label = re.sub(pattern, replacement, lower, flags=re.IGNORECASE)
        if new_label != lower:
            # Remettre la majuscule au premier caractère
            return new_label[0].upper() + new_label[1:]

    return label


# ─────────────────────────────────────────────
# APPLICATION
# ─────────────────────────────────────────────
with open(INPUT_JSONL, "r", encoding="utf-8") as f:
    samples = [json.loads(l) for l in f if l.strip()]

print(f"Dataset chargé : {len(samples)} exemples")

modified = 0
unchanged = 0

for s in samples:
    original = s["global_task_intention"]
    corrected = rebalance_label(original)
    if corrected != original:
        s["global_task_intention"] = corrected
        modified += 1
    else:
        if " and manage" in original.lower():
            unchanged += 1

with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
    for s in samples:
        f.write(json.dumps(s) + "\n")

# ─────────────────────────────────────────────
# RAPPORT
# ─────────────────────────────────────────────
print(f"\n{'=' * 50}")
print(f"RAPPORT DE RÉÉQUILIBRAGE")
print(f"{'=' * 50}")
print(f"  Labels modifiés          : {modified}")
print(f"  Labels 'and manage' non traités : {unchanged}")
print(f"  Fichier de sortie        : {OUTPUT_JSONL}")

# Vérification finale
with open(OUTPUT_JSONL, "r", encoding="utf-8") as f:
    final_samples = [json.loads(l) for l in f if l.strip()]

remaining = sum(
    1 for s in final_samples
    if " and manage" in s["global_task_intention"].lower()
)

from collections import Counter
first_verbs = Counter(
    s["global_task_intention"].split()[0].lower()
    for s in final_samples
)

print(f"\n  'and manage' restants    : {remaining} (était 305)")
print(f"\nTop 10 verbes après correction :")
print(f"  {'Verbe':<20} {'Count':>6} {'%':>6}")
print(f"  {'-'*35}")
total = len(final_samples)
for verb, count in first_verbs.most_common(10):
    pct = count / total * 100
    bar = "█" * int(pct)
    print(f"  {verb:<20} {count:>6}  {pct:>5.1f}%  {bar}")

# Aperçu des 10 premières corrections
print(f"\nAperçu des 10 premières corrections :")
count_shown = 0
with open(INPUT_JSONL, "r", encoding="utf-8") as f:
    originals = {
        json.loads(l)["id"]: json.loads(l)["global_task_intention"]
        for l in f if l.strip()
    }

for s in final_samples:
    orig = originals[s["id"]]
    if orig != s["global_task_intention"]:
        print(f"  Avant  : {orig}")
        print(f"  Après  : {s['global_task_intention']}")
        print()
        count_shown += 1
        if count_shown >= 10:
            break