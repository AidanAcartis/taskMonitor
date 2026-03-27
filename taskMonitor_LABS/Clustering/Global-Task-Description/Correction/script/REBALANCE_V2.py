import json
import re
from collections import Counter

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
INPUT_JSONL  = "activity_data_final_v2.jsonl"
OUTPUT_JSONL = "activity_data_final_v3.jsonl"

# ─────────────────────────────────────────────
# CHARGEMENT
# ─────────────────────────────────────────────
with open(INPUT_JSONL, "r", encoding="utf-8") as f:
    samples = [json.loads(l) for l in f if l.strip()]

total = len(samples)
print(f"Dataset chargé : {total} exemples\n")

# ─────────────────────────────────────────────
# ANALYSE INITIALE
# ─────────────────────────────────────────────
first_verbs = Counter(
    s["global_task_intention"].split()[0].lower()
    for s in samples
)

print("=" * 55)
print("DISTRIBUTION AVANT CORRECTION")
print("=" * 55)
print(f"  {'Verbe':<22} {'Count':>6} {'%':>6}  {'Barre'}")
print(f"  {'-'*50}")
for verb, count in first_verbs.most_common(25):
    pct = count / total * 100
    bar = "█" * int(pct)
    flag = " ⚠" if pct > 8 else ""
    print(f"  {verb:<22} {count:>6}  {pct:>5.1f}%  {bar}{flag}")

print(f"\n  Verbes uniques : {len(first_verbs)}")
print(f"  Top 3 cumul    : {sum(c for _, c in first_verbs.most_common(3))/total*100:.1f}%")

# ─────────────────────────────────────────────
# RÈGLES DE REMPLACEMENT POUR "manage" EN DÉBUT
# Contexte détecté sur ce qui suit "Manage"
# ─────────────────────────────────────────────
MANAGE_RULES = [
    # Base de données
    (r"manage (.*database.*)",           r"administer \1"),
    (r"manage (.*db.*)",                 r"administer \1"),
    (r"manage (.*sql.*)",                r"administer \1"),
    (r"manage (.*schema.*)",             r"maintain \1"),
    (r"manage (.*migration.*)",          r"execute \1"),
    (r"manage (.*query.*)",              r"optimize \1"),

    # Infrastructure / Cloud
    (r"manage (.*infrastructure.*)",     r"maintain \1"),
    (r"manage (.*cloud.*)",              r"maintain \1"),
    (r"manage (.*server.*)",             r"maintain \1"),
    (r"manage (.*kubernetes.*)",         r"orchestrate \1"),
    (r"manage (.*container.*)",          r"orchestrate \1"),
    (r"manage (.*cluster.*)",            r"orchestrate \1"),
    (r"manage (.*terraform.*)",          r"provision \1"),
    (r"manage (.*aws.*)",                r"maintain \1"),
    (r"manage (.*gcp.*)",                r"maintain \1"),
    (r"manage (.*azure.*)",              r"maintain \1"),
    (r"manage (.*deployment.*)",         r"automate \1"),
    (r"manage (.*pipeline.*)",           r"maintain \1"),

    # Réseau / Sécurité
    (r"manage (.*network.*)",            r"maintain \1"),
    (r"manage (.*firewall.*)",           r"configure \1"),
    (r"manage (.*vpn.*)",                r"configure \1"),
    (r"manage (.*ssl.*)",                r"maintain \1"),
    (r"manage (.*certificate.*)",        r"maintain \1"),
    (r"manage (.*access.*)",             r"control \1"),
    (r"manage (.*permission.*)",         r"control \1"),
    (r"manage (.*role.*)",               r"control \1"),
    (r"manage (.*auth.*)",               r"enforce \1"),
    (r"manage (.*security.*)",           r"enforce \1"),
    (r"manage (.*secret.*)",             r"secure \1"),
    (r"manage (.*credential.*)",         r"secure \1"),
    (r"manage (.*vulnerability.*)",      r"remediate \1"),

    # Stockage / Fichiers
    (r"manage (.*storage.*)",            r"maintain \1"),
    (r"manage (.*file.*)",               r"organize \1"),
    (r"manage (.*backup.*)",             r"automate \1"),
    (r"manage (.*archive.*)",            r"maintain \1"),
    (r"manage (.*disk.*)",               r"maintain \1"),
    (r"manage (.*s3.*)",                 r"maintain \1"),
    (r"manage (.*bucket.*)",             r"maintain \1"),

    # Logs / Monitoring
    (r"manage (.*log.*)",                r"analyze \1"),
    (r"manage (.*metric.*)",             r"track \1"),
    (r"manage (.*alert.*)",              r"respond to \1"),
    (r"manage (.*incident.*)",           r"resolve \1"),
    (r"manage (.*error.*)",              r"diagnose \1"),

    # API / Services
    (r"manage (.*api.*)",                r"maintain \1"),
    (r"manage (.*endpoint.*)",           r"maintain \1"),
    (r"manage (.*service.*)",            r"maintain \1"),
    (r"manage (.*microservice.*)",       r"orchestrate \1"),
    (r"manage (.*webhook.*)",            r"configure \1"),
    (r"manage (.*integration.*)",        r"maintain \1"),

    # CI/CD / DevOps
    (r"manage (.*ci.*)",                 r"automate \1"),
    (r"manage (.*cd.*)",                 r"automate \1"),
    (r"manage (.*workflow.*)",           r"automate \1"),
    (r"manage (.*build.*)",              r"automate \1"),
    (r"manage (.*release.*)",            r"automate \1"),
    (r"manage (.*version.*)",            r"maintain \1"),
    (r"manage (.*git.*)",                r"maintain \1"),
    (r"manage (.*branch.*)",             r"maintain \1"),

    # Code / Projet
    (r"manage (.*code.*)",               r"maintain \1"),
    (r"manage (.*project.*)",            r"coordinate \1"),
    (r"manage (.*task.*)",               r"track \1"),
    (r"manage (.*ticket.*)",             r"track \1"),
    (r"manage (.*sprint.*)",             r"coordinate \1"),
    (r"manage (.*dependency.*)",         r"maintain \1"),
    (r"manage (.*package.*)",            r"maintain \1"),
    (r"manage (.*library.*)",            r"maintain \1"),

    # Data / ML
    (r"manage (.*data.*)",               r"process \1"),
    (r"manage (.*dataset.*)",            r"process \1"),
    (r"manage (.*model.*)",              r"maintain \1"),
    (r"manage (.*experiment.*)",         r"track \1"),
    (r"manage (.*training.*)",           r"orchestrate \1"),
    (r"manage (.*pipeline.*)",           r"maintain \1"),

    # Utilisateurs / Équipe
    (r"manage (.*user.*)",               r"administer \1"),
    (r"manage (.*team.*)",               r"coordinate \1"),
    (r"manage (.*account.*)",            r"administer \1"),
    (r"manage (.*profile.*)",            r"administer \1"),
    (r"manage (.*onboard.*)",            r"coordinate \1"),

    # Contenu / Docs
    (r"manage (.*document.*)",           r"maintain \1"),
    (r"manage (.*content.*)",            r"maintain \1"),
    (r"manage (.*wiki.*)",               r"maintain \1"),
    (r"manage (.*report.*)",             r"generate \1"),
    (r"manage (.*template.*)",           r"maintain \1"),

    # Fallback générique
    (r"manage (.*)",                     r"maintain \1"),
]

# ─────────────────────────────────────────────
# RÈGLES POUR "monitor" (13.5% → viser ~8%)
# Réduire d'environ 170 labels
# ─────────────────────────────────────────────
MONITOR_RULES = [
    (r"monitor (.*log.*)",               r"analyze \1"),
    (r"monitor (.*error.*)",             r"diagnose \1"),
    (r"monitor (.*incident.*)",          r"detect and resolve \1"),
    (r"monitor (.*alert.*)",             r"detect and respond to \1"),
    (r"monitor (.*metric.*)",            r"track \1"),
    (r"monitor (.*performance.*)",       r"measure \1"),
    (r"monitor (.*health.*)",            r"check \1"),
    (r"monitor (.*uptime.*)",            r"track \1"),
    (r"monitor (.*latency.*)",           r"measure \1"),
    (r"monitor (.*traffic.*)",           r"analyze \1"),
    (r"monitor (.*network.*)",           r"analyze \1"),
    (r"monitor (.*security.*)",          r"audit \1"),
    (r"monitor (.*vulnerability.*)",     r"audit \1"),
    (r"monitor (.*compliance.*)",        r"audit \1"),
    (r"monitor (.*cost.*)",              r"track \1"),
    (r"monitor (.*budget.*)",            r"track \1"),
    (r"monitor (.*usage.*)",             r"track \1"),
    (r"monitor (.*resource.*)",          r"track \1"),
    (r"monitor (.*availability.*)",      r"track \1"),
]

# ─────────────────────────────────────────────
# STRATÉGIE DE RÉÉQUILIBRAGE
# Objectif : aucun verbe > 8% du dataset
# manage  : 370 (11.8%) → viser ~200 (6.4%)
# monitor : 422 (13.5%) → viser ~250 (8.0%)
# ─────────────────────────────────────────────
TARGET_MAX_PCT = 0.08  # 8% max par verbe

manage_count  = first_verbs["manage"]
monitor_count = first_verbs["monitor"]
manage_target  = int(total * TARGET_MAX_PCT)
monitor_target = int(total * TARGET_MAX_PCT)
manage_to_fix  = max(0, manage_count  - manage_target)
monitor_to_fix = max(0, monitor_count - monitor_target)

print(f"\n  Manage  : {manage_count} → cible {manage_target} → à corriger : {manage_to_fix}")
print(f"  Monitor : {monitor_count} → cible {monitor_target} → à corriger : {monitor_to_fix}")


def apply_rules(label, rules, budget):
    """Applique les règles jusqu'à épuisement du budget."""
    lower = label.lower()
    for pattern, replacement in rules:
        if budget <= 0:
            break
        new_label = re.sub(r"^" + pattern, replacement, lower, flags=re.IGNORECASE)
        if new_label != lower:
            return new_label[0].upper() + new_label[1:], True
    return label, False


# ─────────────────────────────────────────────
# APPLICATION
# ─────────────────────────────────────────────
manage_fixed  = 0
monitor_fixed = 0

for s in samples:
    label = s["global_task_intention"]
    first_word = label.split()[0].lower()

    if first_word == "manage" and manage_fixed < manage_to_fix:
        new_label, changed = apply_rules(label, MANAGE_RULES, manage_to_fix - manage_fixed)
        if changed:
            s["global_task_intention"] = new_label
            manage_fixed += 1

    elif first_word == "monitor" and monitor_fixed < monitor_to_fix:
        new_label, changed = apply_rules(label, MONITOR_RULES, monitor_to_fix - monitor_fixed)
        if changed:
            s["global_task_intention"] = new_label
            monitor_fixed += 1

# ─────────────────────────────────────────────
# SAUVEGARDE
# ─────────────────────────────────────────────
with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
    for s in samples:
        f.write(json.dumps(s) + "\n")

# ─────────────────────────────────────────────
# RAPPORT FINAL
# ─────────────────────────────────────────────
final_verbs = Counter(
    s["global_task_intention"].split()[0].lower()
    for s in samples
)

print(f"\n{'=' * 55}")
print(f"DISTRIBUTION APRÈS CORRECTION")
print(f"{'=' * 55}")
print(f"  {'Verbe':<22} {'Avant':>6} {'Après':>6} {'%':>6}  {'Barre'}")
print(f"  {'-'*55}")
all_verbs = set(list(first_verbs.keys()) + list(final_verbs.keys()))
for verb, count in sorted(final_verbs.items(), key=lambda x: -x[1])[:25]:
    before = first_verbs.get(verb, 0)
    pct = count / total * 100
    bar = "█" * int(pct)
    diff = f"↓{before-count}" if before > count else (f"↑{count-before}" if count > before else "=")
    print(f"  {verb:<22} {before:>6} {count:>6}  {pct:>5.1f}%  {bar}  {diff}")

print(f"\n  Labels manage  corrigés : {manage_fixed}/{manage_to_fix}")
print(f"  Labels monitor corrigés : {monitor_fixed}/{monitor_to_fix}")
print(f"  Verbes uniques          : {len(final_verbs)}")
print(f"  Top 3 cumul             : {sum(c for _, c in final_verbs.most_common(3))/total*100:.1f}%")
print(f"  Fichier de sortie       : {OUTPUT_JSONL}")

# Aperçu corrections
print(f"\nAperçu corrections 'manage' :")
shown = 0
with open(INPUT_JSONL, "r", encoding="utf-8") as f:
    originals = {json.loads(l)["id"]: json.loads(l)["global_task_intention"] for l in f if l.strip()}
for s in samples:
    orig = originals[s["id"]]
    if orig != s["global_task_intention"] and orig.lower().startswith("manage"):
        print(f"  - {orig}")
        print(f"    → {s['global_task_intention']}")
        shown += 1
        if shown >= 8:
            break