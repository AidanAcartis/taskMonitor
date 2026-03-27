import json
import re
from collections import Counter

# ─────────────────────────────────────────────
# CHARGEMENT
# ─────────────────────────────────────────────
PATH = "activity_data_final_v3.jsonl"

with open(PATH, "r", encoding="utf-8") as f:
    samples = [json.loads(l) for l in f if l.strip()]

labels = [s["global_task_intention"] for s in samples]
print(f"Total exemples : {len(labels)}\n")


# ─────────────────────────────────────────────
# 1. DISTRIBUTION DES VERBES (premier mot)
# ─────────────────────────────────────────────
first_verbs = Counter(l.split()[0].lower() for l in labels)

print("=" * 50)
print("TOP 20 VERBES (premier mot du label)")
print("=" * 50)
total = len(labels)
for verb, count in first_verbs.most_common(20):
    pct = count / total * 100
    bar = "█" * int(pct)
    print(f"  {verb:<20} {count:>5}  {pct:>5.1f}%  {bar}")


# ─────────────────────────────────────────────
# 2. FOCUS SUR "MANAGE"
# ─────────────────────────────────────────────
manage_labels = [l for l in labels if l.lower().startswith("manage")]
and_manage_labels = [l for l in labels if " and manage" in l.lower()]

print(f"\n{'=' * 50}")
print(f"FOCUS MANAGE")
print(f"{'=' * 50}")
print(f"  Labels commençant par 'Manage'  : {len(manage_labels)} ({len(manage_labels)/total*100:.1f}%)")
print(f"  Labels contenant 'and manage'   : {len(and_manage_labels)} ({len(and_manage_labels)/total*100:.1f}%)")

print(f"\n  Exemples 'and manage' :")
for l in and_manage_labels[:10]:
    print(f"    - {l}")
if len(and_manage_labels) > 10:
    print(f"    ... et {len(and_manage_labels) - 10} autres")


# ─────────────────────────────────────────────
# 3. DÉTECTION X AND X (mot répété)
# ─────────────────────────────────────────────
print(f"\n{'=' * 50}")
print(f"DÉTECTION X AND X")
print(f"{'=' * 50}")

def has_x_and_x(text):
    words = text.lower().split()
    for i in range(len(words) - 2):
        if words[i] == words[i + 2] and words[i + 1] == "and":
            return True, words[i]
    return False, None

xandx_found = []
for l in labels:
    found, word = has_x_and_x(l)
    if found:
        xandx_found.append((l, word))

if xandx_found:
    print(f"  Labels avec X and X : {len(xandx_found)}")
    for label, word in xandx_found[:10]:
        print(f"    [{word}] → {label}")
else:
    print("  Aucun label avec X and X trouvé.")


# ─────────────────────────────────────────────
# 4. DIVERSITÉ GLOBALE DES VERBES
# ─────────────────────────────────────────────
print(f"\n{'=' * 50}")
print(f"DIVERSITÉ GLOBALE")
print(f"{'=' * 50}")
print(f"  Verbes uniques (1er mot)        : {len(first_verbs)}")
print(f"  Top 5 représentent              : {sum(c for _, c in first_verbs.most_common(5))/total*100:.1f}% du dataset")
print(f"  Verbes avec 1 seul exemple      : {sum(1 for _, c in first_verbs.items() if c == 1)}")

# Ratio de dominance — si le top verbe > 20% c'est un déséquilibre
top_verb, top_count = first_verbs.most_common(1)[0]
if top_count / total > 0.20:
    print(f"\n  ⚠️  '{top_verb}' domine à {top_count/total*100:.1f}% — déséquilibre détecté")
    print(f"     Recommandation : diversifier les labels commençant par '{top_verb}'")
else:
    print(f"\n  Distribution équilibrée — pas de verbe dominant > 20%")