"""
processing/intention_predictor.py
==================================
Génère une "global task intention" pour chaque cluster.
Refactorisation de PREDICT_CLUSTERS_INTENTION.py.
"""

import json
import re
from pathlib import Path

import torch
from transformers import T5ForConditionalGeneration, T5TokenizerFast

from taskmonitor.core import config, storage
from taskmonitor.core.models import Cluster
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


class IntentionPredictor:
    """Génère une intention globale de tâche pour chaque cluster."""

    def __init__(self):
        self._model     = None
        self._tokenizer = None
        self._device    = None
        self._verb_map: dict[str, str] = {}

    def _ensure_model(self) -> bool:
        if self._model is not None:
            return True

        model_dir = config.MODEL_INTENTION
        if not model_dir.exists():
            log.error(f"Modèle intention introuvable : {model_dir}")
            return False

        verb_map_path = config.DICT_VERB_MAP
        if verb_map_path.exists():
            with verb_map_path.open(encoding="utf-8") as f:
                self._verb_map = {k.lower(): v.lower() for k, v in json.load(f).items()}

        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        log.info(f"Chargement modèle intention : {model_dir}")
        self._tokenizer = T5TokenizerFast.from_pretrained(str(model_dir))
        self._model = T5ForConditionalGeneration.from_pretrained(
            str(model_dir),
            torch_dtype=torch.bfloat16 if self._device == "cuda" else torch.float32,
            device_map="auto" if self._device == "cuda" else None,
        )
        if self._device == "cpu":
            self._model.to(self._device)
        self._model.eval()
        log.info(f"Modèle intention chargé (device: {self._device})")
        return True

    def _predict(self, items: list[str]) -> str:
        if not items:
            return "(cluster vide)"
        items_text = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(items))
        prompt = (
            "Based on the following list of task items, "
            "generate a concise global task intention in one sentence:\n"
            f"{items_text}"
        )
        inputs = self._tokenizer(
            prompt, return_tensors="pt",
            max_length=448, truncation=True
        ).to(self._device)

        with torch.no_grad():
            outputs = self._model.generate(**inputs, **config.INFERENCE_INTENTION_CONFIG)
        return self._tokenizer.decode(outputs[0], skip_special_tokens=True)

    def _simple_intention(self, item: str) -> str:
        """Pour les singletons : génère une intention simple sans modèle."""
        COMMON_VERBS = {
            "create", "run", "execute", "install", "remove", "update",
            "send", "open", "read", "write", "build", "compile",
            "check", "verify", "record", "display", "launch",
            "render", "provide", "handle", "manage", "analyze",
            "list", "clear", "exit", "play", "search", "activate",
        }
        STOP_WORDS = {"of", "to", "for", "with", "in", "on", "at", "from",
                      "by", "about", "as", "into", "after", "before"}

        obj = item.split(",")[0].strip()
        item_lower = item.lower()

        if "file" in item_lower and "opened with" in item_lower:
            m = re.search(r"opened with ([^,]+)", item_lower)
            if m:
                return f"open {obj} with {m.group(1).strip().title()}"

        # Chercher un verbe dans "used to <verb> ..."
        for part in item.split(","):
            if "used to" in part.lower():
                segment = re.sub(
                    r"(command used to|used to|used for|opened with|executed in)", "",
                    part.lower()
                ).strip()
                words = segment.split()
                if words:
                    verb = words[0]
                    if verb in self._verb_map:
                        verb = self._verb_map[verb]
                    if verb in COMMON_VERBS:
                        obj_words = []
                        for w in words[1:]:
                            if w in STOP_WORDS:
                                break
                            obj_words.append(w)
                        return verb + (" " + " ".join(obj_words) if obj_words else "")

        if "application" in item_lower:
            return f"use {obj.lower()}"
        if "file" in item_lower:
            return f"open {obj.lower()}"
        if "command" in item_lower:
            return f"run {obj.lower()}"
        return obj.lower()

    def predict(self, date_str: str) -> list[Cluster]:
        """
        Lit clusters_output.txt, génère les intentions, sauvegarde et retourne les clusters.

        Args:
            date_str: date au format "YYYY-MM-DD"

        Returns:
            Liste de Cluster avec intentions remplies
        """
        clusters_txt = storage.read_clusters_output(date_str)
        if not clusters_txt:
            log.error(f"clusters_output.txt absent pour {date_str}")
            return []

        clusters = self._parse_clusters(clusters_txt)
        if not clusters:
            log.warning("Aucun cluster trouvé dans le rapport")
            return []

        # Charger le modèle seulement si nécessaire (clusters non-singleton)
        has_multi = any(not c.is_singleton for c in clusters)
        if has_multi and not self._ensure_model():
            log.error("Modèle intention non disponible")
            for c in clusters:
                c.intention = self._simple_intention(c.items[0]) if c.items else ""
            storage.write_intentions(date_str, clusters)
            return clusters

        for i, c in enumerate(clusters):
            if c.is_singleton:
                c.intention = self._simple_intention(c.items[0]) if c.items else ""
            else:
                c.intention = self._predict(c.items)
            log.info(f"[{i+1}/{len(clusters)}] {c.label} → {c.intention}")

        storage.write_intentions(date_str, clusters)
        log.info(f"Intentions sauvegardées pour {date_str}")
        return clusters

    @staticmethod
    def _parse_clusters(text: str) -> list[Cluster]:
        """Parse clusters_output.txt → liste de Cluster."""
        clusters: list[Cluster] = []
        current: Cluster | None = None
        cid = 0

        header_re = re.compile(
            r"^(Cluster\s+\d+|Autres\s+petites\s+t[aâ]ches)"
            r"\s*\|\s*(\d+)\s+t[aâ]che\(s\)"
            r"\s*\|\s*coh[eé]sion\s*=\s*([\d.]+)",
            re.IGNORECASE,
        )
        item_re = re.compile(r"^\s*[•\-\*]\s+(.+)$")

        for line in text.splitlines():
            m = header_re.search(line)
            if m:
                if current:
                    clusters.append(current)
                current = Cluster(
                    cluster_id=cid,
                    label=m.group(1).strip(),
                    num_tasks=int(m.group(2)),
                    cohesion=float(m.group(3)),
                )
                cid += 1
                continue
            if current:
                m2 = item_re.match(line)
                if m2:
                    current.items.append(m2.group(1).strip())

        if current:
            clusters.append(current)

        # Éclater les "Autres petites tâches" en singletons
        expanded: list[Cluster] = []
        for c in clusters:
            if re.search(r"autres\s+petites\s+t[aâ]ches", c.label, re.IGNORECASE):
                for idx, item in enumerate(c.items):
                    expanded.append(Cluster(
                        cluster_id=cid,
                        label=f"Autres petites tâches — singleton {idx + 1}",
                        num_tasks=1,
                        cohesion=c.cohesion,
                        items=[item],
                        is_singleton=True,
                    ))
                    cid += 1
            else:
                expanded.append(c)

        return expanded