maintenant, j'ai besoin de regrouper les taches dans la description qui se rapprochent pour identifier un grand tache que l'user a fait. Pour cela , j'ai entrainne un modele pour le clustering , je presenterai ici les preprocessing et l'entrainnement du modele ainsi que le test d'inference afin d'utiliser le modele correctement : PREPROCESS : "

def normalize_task(text):
    """
    Nettoyage minimal d'un task_item ou global_task
    """
    # enlever les guillemets et les backslashes
    text = text.replace('\\"', '').replace('"', '')
    # passer en minuscules et strip
    text = text.lower().strip()
    return text


", "

structured_dataset = []

for entry in dataset:
  task_items = entry["task_items"]

  # Niveau A : petits tasks unitaires
  small_tasks = [normalize_task(t) for t in task_items]

  # Niveau B : bloc global
  global_block = " ".join(small_tasks)

  # Ajouter au dataset structuré
  structured_dataset.append({
      "id": entry["id"],
      "small_tasks": small_tasks,
      "global_block": global_block,
      "global_task_description": normalize_task(entry["global_task_description"])
  })

", "

from sentence_transformers import InputExample

train_examples = []

for obj in structured_dataset:
    small_tasks = obj["small_tasks"]   # déjà normalisés
    global_block = obj["global_block"]

    # 1️ POSITIFS : petit task ↔ bloc global
    for task in small_tasks:
        train_examples.append(
            InputExample(texts=[task, global_block])
        )

    # 2️ POSITIFS : task ↔ task (même global_task)
    for i in range(len(small_tasks)):
        for j in range(i + 1, len(small_tasks)):
            train_examples.append(
                InputExample(texts=[small_tasks[i], small_tasks[j]])
            )

    # 3️ POSITIFS : bloc ↔ sous-bloc (data augmentation)
    if len(small_tasks) > 1:
        subset = small_tasks[:int(len(small_tasks) * 0.7)]
        train_examples.append(
            InputExample(texts=[" ".join(subset), global_block])
        )

print(f"Nombre total d'exemples : {len(train_examples)}")


", "

import os
import pickle

save_dir = "/content/drive/MyDrive/global_task_model"
os.makedirs(save_dir, exist_ok=True)

save_path = os.path.join(save_dir, "train_examples.pkl")

with open(save_path, "wb") as f:
    pickle.dump(train_examples, f)

print(f" train_examples sauvegardé dans {save_path}")


", "

from sentence_transformers import SentenceTransformer, losses
from torch.utils.data import DataLoader
import math

", "

BASE_DIR = "/content/drive/MyDrive/global_task_model"

CHECKPOINT_DIR = f"{BASE_DIR}/checkpoints"
FINAL_MODEL_DIR = f"{BASE_DIR}/final_model"

import os
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(FINAL_MODEL_DIR, exist_ok=True)

", "

model_name = "all-MiniLM-L6-v2"
model = SentenceTransformer(model_name)

", "

train_batch_size = 8

train_dataloader = DataLoader(
    train_examples,
    shuffle=True,
    batch_size=train_batch_size
)

", "

train_loss = losses.MultipleNegativesRankingLoss(model)

", "

num_epochs = 3
warmup_steps = math.ceil(len(train_dataloader) * num_epochs * 0.1)  # 10% warmup

", "

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=num_epochs,
    warmup_steps=warmup_steps,
    show_progress_bar=True,
    checkpoint_path=CHECKPOINT_DIR,
    checkpoint_save_steps=2000,
    checkpoint_save_total_limit=3
)

", EVALUATION ET TEST :"

from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "/content/drive/MyDrive/global_task_model/final_model"
)

model.eval()


", "

import numpy as np
from sentence_transformers import util

def intra_global_similarity(model, structured_dataset):
    results = []

    for obj in structured_dataset:
        tasks = obj["small_tasks"]
        if len(tasks) < 2:
            continue

        emb = model.encode(tasks, convert_to_tensor=True)
        sims = util.cos_sim(emb, emb).cpu().numpy()

        # enlever diagonale
        values = sims[np.triu_indices(len(tasks), k=1)]

        results.append({
            "id": obj["id"],
            "mean": float(values.mean()),
            "min": float(values.min()),
            "max": float(values.max()),
            "std": float(values.std())
        })

    return results

", "

def inter_global_overlap(model, obj_a, obj_b):
    emb_a = model.encode(obj_a["small_tasks"], convert_to_tensor=True)
    emb_b = model.encode(obj_b["small_tasks"], convert_to_tensor=True)

    sims = util.cos_sim(emb_a, emb_b).cpu().numpy()
    return sims.mean(), sims.max()


", "

def retrieval_accuracy(model, structured_dataset, k=1):
    global_blocks = [o["global_block"] for o in structured_dataset]
    global_ids = [o["id"] for o in structured_dataset]

    global_emb = model.encode(global_blocks, convert_to_tensor=True)

    correct = 0
    total = 0

    for obj in structured_dataset:
        for task in obj["small_tasks"]:
            q = model.encode(task, convert_to_tensor=True)
            sims = util.cos_sim(q, global_emb)[0]
            topk = sims.topk(k).indices.tolist()

            if global_ids.index(obj["id"]) in topk:
                correct += 1
            total += 1

    return correct / total


", "

from sentence_transformers import SentenceTransformer

base = SentenceTransformer("all-MiniLM-L6-v2")

acc_base = retrieval_accuracy(base, structured_dataset)
acc_finetuned = retrieval_accuracy(model, structured_dataset)

print("Base:", acc_base)
print("Fine-tuned:", acc_finetuned)


", "

from itertools import combinations


# -----------------------------
#  Calcul et affichage des mesures
# -----------------------------
# Intra-global similarity
intra_results = intra_global_similarity(model, structured_dataset)
print(" Intra-global similarity:")
for r in intra_results:
    print(f"ID {r['id']}: mean={r['mean']:.3f}, min={r['min']:.3f}, max={r['max']:.3f}, std={r['std']:.3f}")

# Inter-global overlap
print("\n Inter-global overlap:")
for obj_a, obj_b in combinations(structured_dataset, 2):
    mean_sim, max_sim = inter_global_overlap(model, obj_a, obj_b)
    print(f"{obj_a['id']} vs {obj_b['id']}: mean={mean_sim:.3f}, max={max_sim:.3f}")

# Retrieval accuracy
acc = retrieval_accuracy(model, structured_dataset)
print(f"\n Retrieval accuracy: {acc:.3f}")

", INFERENCE :"

tasks = [
    "steam, application, launched Steam and logged in",
    "steam://rungameid/570, URL, Steam, launched Dota 2 via Steam game ID",
    "dota2.log, LOG file, /home/user/.steam/steam/logs, Cat, reviewed Dota 2 launch logs",
    "dota2_screenshots.zip, ZIP file, /home/user/Videos/Dota2, Archive Manager, compressed game screenshots",
    "dota2_match_2026-01-18.dem, DEM replay file, /home/user/Videos/Dota2/Replays, Game client, watched match replay",

    "steam://rungameid/730, URL, Steam, launched CS:GO",
    "csgo_config.cfg, CFG file, /home/user/.steam/steam/steamapps/common/Counter-Strike Global Offensive/csgo/cfg, VS Code, edited game settings (crosshair, sensitivity)",
    "obs, application, started recording CS:GO gameplay",
    "obs_recording_01.mkv, MKV file, /home/user/Videos/CSGO, VLC, played recorded gameplay",

    "lutris, application, launched a Windows game through Wine",
    "winecfg, command, configured Wine settings for game compatibility",
    "protontricks, command, applied compatibility fixes to Steam game",

    "steam_screenshot_001.png, PNG file, /home/user/.steam/steam/userdata/123456789/screenshots, Image Viewer, viewed screenshot",
    "steam_screenshot_002.png, PNG file, /home/user/.steam/steam/userdata/123456789/screenshots, Image Viewer, viewed screenshot",
    "game_updates.txt, TXT file, /home/user/Downloads, Gedit, read patch notes for latest update",

    "discord, application, joined a gaming voice channel",
    "discord_chat_log.txt, TXT file, /home/user/Documents/DiscordLogs, Gedit, read chat messages",
    "twitch.tv, web page, Firefox, watched a live gaming stream",
    "https://store.steampowered.com/app/570/Dota_2/, web page, Firefox, checked Dota 2 store page"
]


", "

import random

random.seed(42)
random.shuffle(tasks)


", "

from sentence_transformers import util

embeddings = model.encode(
    tasks,
    convert_to_tensor=True,
    normalize_embeddings=True
)


", "

import numpy as np

sim = util.cos_sim(embeddings, embeddings).cpu().numpy()
dist = 1 - sim
dist = np.clip(dist, 0, None)  # CRUCIAL (corrige l’erreur silhouette)


", "

from sklearn.metrics import silhouette_score
from collections import defaultdict

def cluster_cohesion(dist, labels):
    clusters = defaultdict(list)
    for i, c in enumerate(labels):
        clusters[c].append(i)

    cohesions = {}
    for c, idxs in clusters.items():
        if len(idxs) < 2:
            cohesions[c] = 0.0
            continue
        sub = dist[np.ix_(idxs, idxs)]
        cohesions[c] = sub.mean()

    return cohesions


", "

from sklearn.cluster import AgglomerativeClustering

thresholds = np.arange(0.45, 0.85, 0.01)

best = {
    "th": None,
    "silhouette": -1,
    "labels": None,
    "cohesion": None
}

for th in thresholds:
    clustering = AgglomerativeClustering(
        n_clusters=None,
        metric="precomputed",
        linkage="average",
        distance_threshold=th
    )

    labels = clustering.fit_predict(dist)
    n_clusters = len(set(labels))

    # Rejets intelligents
    if n_clusters <= 1 or n_clusters > len(tasks) // 2:
        continue

    sil = silhouette_score(dist, labels, metric="precomputed")
    cohesion = cluster_cohesion(dist, labels)

    if sil > best["silhouette"]:
        best.update({
            "th": th,
            "silhouette": sil,
            "labels": labels,
            "cohesion": cohesion
        })


", "

print("\n=== Cohésion par cluster ===")

cluster_cohesions = []

for c, items in groups.items():
    idxs = [tasks.index(t) for t in items]

    # on ignore les singletons
    if len(idxs) > 1:
        d = dist[np.ix_(idxs, idxs)]
        cohesion = d[np.triu_indices_from(d, 1)].mean()
        cluster_cohesions.append(cohesion)
        print(f"Cluster {c} | cohésion = {cohesion:.3f}")

#Moyenne des cohésions (clusters de taille ≥ 2 uniquement)
mean_cohesion = np.mean(cluster_cohesions) if cluster_cohesions else 0.0

print("\n=== Cohésion moyenne (clusters ≥ 2) ===")
print(f"Cohésion moyenne = {mean_cohesion:.3f}")


", "

def recluster_subset(tasks_subset, dist_matrix_subset, thresholds=np.arange(0.45, 0.85, 0.01)):
    n = len(tasks_subset)

    # Cas 1 élément → impossible à diviser
    if n < 2:
        return {0: tasks_subset}, None, 0.0

    # Cas EXACTEMENT 2 éléments → division forcée
    if n == 2:
        return {0: [tasks_subset[0]], 1: [tasks_subset[1]]}, None, 0.0

    # Cas EXACTEMENT 3 éléments → division forcée en 2 clusters (2+1)
    if n == 3:
        return {0: [tasks_subset[0], tasks_subset[1]], 1: [tasks_subset[2]]}, None, 0.0

    # Cas général n >= 4
    results = {2: {"sil": -1, "th": None, "labels": None},
               3: {"sil": -1, "th": None, "labels": None}}

    for th in thresholds:
        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric="precomputed",
            linkage="average",
            distance_threshold=th
        )
        labels = clustering.fit_predict(dist_matrix_subset)
        n_clusters = len(set(labels))
        if n_clusters not in (2,3):
            continue
        try:
            sil = silhouette_score(dist_matrix_subset, labels, metric="precomputed")
        except ValueError:
            sil = 0.0
        if sil > results[n_clusters]["sil"] or (np.isclose(sil, results[n_clusters]["sil"]) and (results[n_clusters]["th"] is None or th > results[n_clusters]["th"])):
            results[n_clusters].update({"sil": sil, "th": th, "labels": labels})

    # Choisir 3 clusters si silhouette >= 2 clusters
    chosen_k = 3 if results[3]["sil"] >= results[2]["sil"] else 2
    chosen = results[chosen_k]

    if chosen["labels"] is None:
        # Si aucun résultat, forcer division 2 clusters (cas par défaut)
        return {0: tasks_subset[:n//2], 1: tasks_subset[n//2:]}, None, 0.0

    new_groups = defaultdict(list)
    for i, lbl in enumerate(chosen["labels"]):
        new_groups[lbl].append(tasks_subset[i])
    return new_groups, chosen["th"], chosen["sil"]


", "

from collections import defaultdict
import numpy as np
from sklearn.cluster import AgglomerativeClustering

best_threshold_global = best["th"]

clustering = AgglomerativeClustering(
    n_clusters=None,
    metric="precomputed",
    linkage="average",
    distance_threshold=best_threshold_global
)
labels = clustering.fit_predict(dist)
n_clusters = len(set(labels))
print("th:", th, "n_clusters:", n_clusters, "labels:", labels)

groups = defaultdict(list)
for task, lbl in zip(tasks, labels):
    groups[lbl].append(task)

COHESION_THRESHOLD = 0.39
final_groups = {}
new_label_counter = 0

clusters_to_check = list(groups.values())

while clusters_to_check:
    current = clusters_to_check.pop(0)
    n = len(current)

    # Cas 1 élément → terminal
    if n < 2:
        final_groups[new_label_counter] = current
        new_label_counter += 1
        continue

    idxs = [tasks.index(t) for t in current]
    sub_dist = dist[np.ix_(idxs, idxs)]
    mean_cohesion = sub_dist[np.triu_indices_from(sub_dist, 1)].mean()

    if mean_cohesion > COHESION_THRESHOLD:
        new_sub_groups, sub_th, sub_sil = recluster_subset(current, sub_dist)

        # Si aucune vraie division
        if len(new_sub_groups) == 1:
            final_groups[new_label_counter] = current
            new_label_counter += 1
        else:
            for sub_items in new_sub_groups.values():
                clusters_to_check.append(sub_items)
    else:
        final_groups[new_label_counter] = current
        new_label_counter += 1


", "

# --- Affichage final des clusters après reclustering itératif ---
print("\n=== Clusters finaux après reclustering itératif ===")
for c, items in final_groups.items():
    print(f"\nCluster {c} | {len(items)} tâches")
    for t in items:
        print(" -", t)


", "

from sklearn.metrics import silhouette_score
import numpy as np

# Construire les labels finaux pour silhouette
final_labels = np.zeros(len(tasks), dtype=int)
for c, items in final_groups.items():
    for t in items:
        idx = tasks.index(t)
        final_labels[idx] = c

sil_final = silhouette_score(dist, final_labels, metric="precomputed")
print("Silhouette score final après reclustering:", round(sil_final, 3))


", "

print("\n=== Cohésion finale par cluster ===")

final_cluster_cohesions = []

for c, items in final_groups.items():
    idxs = [tasks.index(t) for t in items]

    if len(idxs) < 2:
        mean_d = 0.0
    else:
        d = dist[np.ix_(idxs, idxs)]
        mean_d = d[np.triu_indices_from(d, 1)].mean()
        final_cluster_cohesions.append(mean_d)

    print(f"Cluster {c} | cohésion = {mean_d:.3f}")

# Moyenne des cohésions (clusters de taille ≥ 2 uniquement)
mean_final_cohesion = (
    np.mean(final_cluster_cohesions)
    if final_cluster_cohesions else 0.0
)

print("\n=== Cohésion moyenne finale (clusters ≥ 2) ===")
print(f"Cohésion moyenne finale = {mean_final_cohesion:.3f}")


", "

# --- Extraction des singletons ---
singletons = []
non_singleton_groups = {}

for cid, items in final_groups.items():
    if len(items) == 1:
        singletons.append(items[0])
    else:
        non_singleton_groups[cid] = items

print(f"{len(singletons)} singletons extraits sur {len(tasks)} tâches")


", "

SINGLETON_RATIO_THRESHOLD = 0.2

if len(singletons) / len(tasks) < SINGLETON_RATIO_THRESHOLD:
    print("Pas assez de singletons → pas de reclustering global")
    new_tasks = []
else:
    new_tasks = singletons
    print("Reclustering global des singletons activé")


", "

from sentence_transformers import util
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from collections import defaultdict
import numpy as np

if new_tasks:
    # Embeddings
    new_embeddings = model.encode(
        new_tasks,
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    new_sim = util.cos_sim(new_embeddings, new_embeddings).cpu().numpy()
    new_dist = 1 - new_sim
    new_dist = np.clip(new_dist, 0, None)

    # Recherche du meilleur threshold
    best_singleton = {
        "th": None,
        "silhouette": -1,
        "labels": None
    }

    for th in thresholds:
        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric="precomputed",
            linkage="average",
            distance_threshold=th
        )

        labels = clustering.fit_predict(new_dist)
        n_clusters = len(set(labels))


        if n_clusters <= 1 or n_clusters > len(new_tasks) // 2:
            continue

        sil = silhouette_score(new_dist, labels, metric="precomputed")

        if sil > best_singleton["silhouette"]:
            best_singleton.update({
                "th": th,
                "silhouette": sil,
                "labels": labels
            })

    # Construction des nouveaux clusters issus des singletons
    singleton_clusters = defaultdict(list)

    singleton_clusters = defaultdict(list)

    if best_singleton["labels"] is None:
        # Aucun reclustering valide → on garde les singletons tels quels
        for t in new_tasks:
            singleton_clusters[len(singleton_clusters)] = [t]
    else:
        for task, lbl in zip(new_tasks, best_singleton["labels"]):
            singleton_clusters[lbl].append(task)
else:
    singleton_clusters = {}


", "

# --- Fusion finale ---
final_merged_groups = {}
cid = 0

# Clusters non-singletons
for items in non_singleton_groups.values():
    final_merged_groups[cid] = items
    cid += 1

# Nouveaux clusters issus des singletons
for items in singleton_clusters.values():
    final_merged_groups[cid] = items
    cid += 1


", "

print("\n=== Clusters finaux après reclustering des singletons ===")
for c, items in final_merged_groups.items():
    print(f"\nCluster {c} | {len(items)} tâches")
    for t in items:
        print(" -", t)


", "

# --- Reconstruction des labels finaux ---
task_to_index = {t: i for i, t in enumerate(tasks)}

labels_final = np.full(len(tasks), -1, dtype=int)

for cid, items in final_merged_groups.items():
    for t in items:
        labels_final[task_to_index[t]] = cid

# Sécurité
assert np.all(labels_final != -1)


", "

from sklearn.metrics import silhouette_score

# Compter les clusters non-singletons
cluster_sizes = {}
for cid in labels_final:
    cluster_sizes[cid] = cluster_sizes.get(cid, 0) + 1

valid_clusters = [cid for cid, sz in cluster_sizes.items() if sz >= 2]

if len(valid_clusters) >= 2:
    sil_final = silhouette_score(dist, labels_final, metric="precomputed")
else:
    sil_final = None

print("Silhouette finale :", sil_final)


", "

from collections import defaultdict

def cluster_cohesion(dist, labels):
    clusters = defaultdict(list)
    for i, c in enumerate(labels):
        clusters[c].append(i)

    cohesions = {}
    for c, idxs in clusters.items():
        if len(idxs) < 2:
            cohesions[c] = 0.0
            continue
        sub = dist[np.ix_(idxs, idxs)]
        cohesions[c] = sub[np.triu_indices_from(sub, 1)].mean()

    return cohesions


cohesions_final = cluster_cohesion(dist, labels_final)

print("\nCohésion par cluster :")
for cid, coh in cohesions_final.items():
    print(f"Cluster {cid} | cohésion = {coh:.3f}")

# Cohésion moyenne (clusters >= 2)
valid_cohesions = [c for cid, c in cohesions_final.items()
                   if sum(labels_final == cid) >= 2]

mean_cohesion_final = np.mean(valid_cohesions) if valid_cohesions else None

print("\nCohésion moyenne finale :", mean_cohesion_final)


", "

from collections import defaultdict
import numpy as np
from sklearn.cluster import AgglomerativeClustering

COHESION_THRESHOLD = 0.65

", "

def compute_cohesion(sub_dist):
    n = sub_dist.shape[0]
    if n < 2:
        return 0.0
    return sub_dist[np.triu_indices_from(sub_dist, 1)].mean()


", "

def best_split_by_k(tasks_subset, dist_matrix_subset):
    n = len(tasks_subset)

    for k in range(2, n + 1):
        clustering = AgglomerativeClustering(
            n_clusters=k,
            metric="precomputed",
            linkage="average"
        )
        labels = clustering.fit_predict(dist_matrix_subset)

        total_cohesion = 0.0
        for lbl in set(labels):
            idxs = np.where(labels == lbl)[0]
            sub_d = dist_matrix_subset[np.ix_(idxs, idxs)]
            total_cohesion += compute_cohesion(sub_d)

        avg_cohesion = total_cohesion / k

        print(f"  -> k={k} | avg_cohesion={avg_cohesion:.3f}")

        # VALIDATION : on accepte le premier k qui passe le seuil
        if avg_cohesion <= 0.5:
            print(f"  => split VALIDÉ: k={k} | avg_cohesion={avg_cohesion:.3f}\n")
            return {
                "k": k,
                "labels": labels,
                "avg_cohesion": avg_cohesion
            }

    # si aucun k n'est valide
    print("  => aucun split valide (avg_cohesion > 0.5 pour tous les k)\n")
    return {"k": None, "labels": None, "avg_cohesion": None}


", "

from collections import defaultdict

# reconstruction clusters depuis labels_final
clusters_from_labels = defaultdict(list)
for idx, c in enumerate(labels_final):
    clusters_from_labels[c].append(tasks[idx])


", "

clusters_to_recluster = []
clusters_kept = {}

for cid, items in clusters_from_labels.items():
    idxs = [tasks.index(t) for t in items]
    if len(idxs) < 2:
        clusters_kept[cid] = items
        continue
    sub_dist = dist[np.ix_(idxs, idxs)]
    coh = compute_cohesion(sub_dist)

    if coh > COHESION_THRESHOLD:  # 0.7
        clusters_to_recluster.append((cid, items))
    else:
        clusters_kept[cid] = items


", "

final_reclustered = {}
new_cid = 0
assigned_tasks = set()

# 1) Reclustering des clusters à traiter
for cid, items in clusters_to_recluster:
    print(f"\n--- Reclustering du cluster {cid} (taille={len(items)}) ---")
    clusters_to_check = [items]

    while clusters_to_check:
        current = clusters_to_check.pop(0)
        idxs = [tasks.index(t) for t in current]
        sub_dist = dist[np.ix_(idxs, idxs)]
        mean_cohesion = compute_cohesion(sub_dist)

        print(f"\nCluster actuel (taille={len(current)}) - cohésion = {mean_cohesion:.3f}")
        for t in current:
            print("  -", t)

        if mean_cohesion > 0.5:
            best_split = best_split_by_k(current, sub_dist)

            if best_split["labels"] is None:
                print(" -> Pas de division utile. On garde ce cluster.")
                final_reclustered[new_cid] = current
                new_cid += 1
                assigned_tasks.update(current)

            else:
                new_groups = defaultdict(list)
                for i, lbl in enumerate(best_split["labels"]):
                    new_groups[lbl].append(current[i])

                print(f" -> Division en {len(new_groups)} sous-clusters (avg cohésion = {best_split['avg_cohesion']:.3f})")

                for sub_items in new_groups.values():
                    idxs2 = [tasks.index(t) for t in sub_items]
                    sub_dist2 = dist[np.ix_(idxs2, idxs2)]
                    coh2 = compute_cohesion(sub_dist2)

                    print(f"    Sous-cluster (taille={len(sub_items)}) - cohésion = {coh2:.3f}")
                    for t in sub_items:
                        print("      -", t)

                    # IMPORTANT : pas de double ajout
                    if coh2 > 0.5:
                        print("      -> cohésion > 0.5 : on reclusterise encore")
                        clusters_to_check.append(sub_items)
                    else:
                        print("      -> cohésion <= 0.5 : cluster final")
                        final_reclustered[new_cid] = sub_items
                        new_cid += 1
                        assigned_tasks.update(sub_items)

        else:
            print(" -> cohésion <= 0.7 : cluster final")
            final_reclustered[new_cid] = current
            new_cid += 1
            assigned_tasks.update(current)

# 2) Ajouter les clusters non-reclusterisés (kept)
for cid, items in clusters_kept.items():
    # Ajout uniquement si aucun élément n'a déjà été assigné
    if not any(t in assigned_tasks for t in items):
        final_reclustered[new_cid] = items
        new_cid += 1
        assigned_tasks.update(items)


", "

print("\n=== Clusters finaux ===")
for c, items in final_reclustered.items():
    print(f"\nCluster {c} | {len(items)} tâches")
    for t in items:
        print(" -", t)

", "

from sklearn.metrics import silhouette_score
import numpy as np

# 1) Reconstruction des labels globaux
labels_final = np.full(len(tasks), -1)

for cid, items in final_reclustered.items():
    for t in items:
        labels_final[tasks.index(t)] = cid

# Vérification
n_clusters_final = len(set(labels_final))
print(f"\nNombre final de clusters = {n_clusters_final}")

", "


# 2) Silhouette score global (si valide)
if n_clusters_final > 1 and n_clusters_final < len(tasks):
    sil_final = silhouette_score(dist, labels_final, metric="precomputed")
else:
    sil_final = 0.0

print(f"Silhouette finale = {sil_final:.3f}")


", "


# 3) Cohésion par cluster + moyenne
print("\n=== Cohésion par cluster ===")

cluster_cohesions = []

for c, items in final_reclustered.items():
    idxs = [tasks.index(t) for t in items]

    if len(idxs) < 2:
        coh = 0.0
    else:
        d = dist[np.ix_(idxs, idxs)]
        coh = compute_cohesion(d)
        cluster_cohesions.append(coh)

    print(f"Cluster {c} | cohésion = {coh:.3f}")

# Moyenne des cohésions (clusters de taille ≥ 2 uniquement)
mean_cohesion_final = (
    np.mean(cluster_cohesions)
    if cluster_cohesions else 0.0
)

print("\n=== Métriques finales ===")
print(f"Cohésion moyenne finale = {mean_cohesion_final:.3f}")
print(f"Silhouette finale       = {sil_final:.3f}")

". Il y a plusieurs etapes dans l'inference pour arriver au dernier resultat 