"""
processing/describer.py
=======================
Génère une description textuelle pour chaque événement de events_normalized.csv.
Utilise le modèle T5 fine-tuné (Gen_Desc_Model) et l'outil cmddesc.
Refactorisation de describe-event2.py.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import pandas as pd
import torch
import torch.nn as nn
from transformers import AutoTokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer

from taskmonitor.core import config, storage
from taskmonitor.core.logger import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────
# CHARGEMENT DES DICTIONNAIRES
# ─────────────────────────────────────────────

def _load_dicts() -> tuple[dict, dict, dict]:
    """Charge FILE_EXTENSION, mime_map et TOOLS depuis les JSON."""
    def _load(path: Path) -> dict:
        if not path.exists():
            log.warning(f"Dictionnaire manquant : {path}")
            return {}
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    return (
        _load(config.DICT_FILE_EXT),
        _load(config.DICT_MIME),
        _load(config.DICT_TOOLS),
    )


# ─────────────────────────────────────────────
# MODÈLE T5 + FUSION LEXICALE
# ─────────────────────────────────────────────

class T5WithFusion(nn.Module):
    def __init__(self, model_name: str = "google/flan-t5-small", lexical_dim: int = 512):
        super().__init__()
        self.t5   = T5ForConditionalGeneration.from_pretrained(model_name)
        self.proj = nn.Linear(lexical_dim, self.t5.config.d_model)

    def forward(self, input_ids=None, attention_mask=None, labels=None,
                lexical_embeds=None, **kwargs):
        inputs_embeds = self.t5.encoder.embed_tokens(input_ids)
        if lexical_embeds is not None:
            lexical_proj  = self.proj(lexical_embeds.float()).to(inputs_embeds.device)
            inputs_embeds = inputs_embeds + lexical_proj.unsqueeze(1)
        return self.t5(
            input_ids=None, attention_mask=attention_mask,
            labels=labels, inputs_embeds=inputs_embeds, **kwargs
        )

    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.t5, name)


# ─────────────────────────────────────────────
# CLASSE PRINCIPALE
# ─────────────────────────────────────────────

class Describer:
    """
    Génère des descriptions pour les événements utilisateur.
    Charge les modèles une seule fois à l'instanciation.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.FILE_EXTENSION, self.MIME_MAP, self.TOOLS = _load_dicts()

        self._tokenizer = None
        self._t5_model  = None
        self._lex_model = None
        self._models_loaded = False

    def _ensure_models(self) -> bool:
        """Charge les modèles si pas encore fait. Retourne False si échec."""
        if self._models_loaded:
            return True

        model_dir = config.MODEL_GEN_DESC
        if not model_dir.exists():
            log.error(f"Modèle Gen_Desc introuvable : {model_dir}")
            return False

        log.info(f"Chargement du modèle Gen_Desc depuis {model_dir}")
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
            model = T5WithFusion(
                model_name="google/flan-t5-small",
                lexical_dim=config.MODEL_LEXICAL_DIM,
            )
            state = torch.load(
                model_dir / "pytorch_model.bin",
                map_location=self.device
            )
            model.load_state_dict(state, strict=False)
            self._t5_model = model.to(self.device).eval()
            self._lex_model = SentenceTransformer("all-MiniLM-L6-v2")
            self._models_loaded = True
            log.info(f"Modèle Gen_Desc chargé (device: {self.device})")
            return True
        except Exception as e:
            log.error(f"Erreur chargement modèle Gen_Desc : {e}")
            return False

    # ── Génération descriptions fichiers ──────

    def _generate_file_descriptions(self, filenames: list[str]) -> list[str]:
        if not self._ensure_models():
            return [""] * len(filenames)

        descriptions = []
        batch_size = config.MODEL_BATCH_SIZE

        for i in range(0, len(filenames), batch_size):
            batch = filenames[i: i + batch_size]
            prompts = [
                f"Describe the specific purpose of the following file.\n\nFilename: {name}\n\nDescription:"
                for name in batch
            ]
            inputs = self._tokenizer(
                prompts, return_tensors="pt",
                padding=True, truncation=True, max_length=128
            ).to(self.device)

            with torch.no_grad():
                outputs = self._t5_model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    **config.INFERENCE_DESC_CONFIG,
                )
            descriptions.extend(
                self._tokenizer.decode(o, skip_special_tokens=True) for o in outputs
            )
        return descriptions

    # ── Description commandes (cmddesc) ───────

    def _describe_command(self, command: str) -> str:
        command = command.strip()
        if not command:
            return ""
        try:
            result = subprocess.run(
                ["cmddesc"], input=command, capture_output=True, text=True, timeout=10
            )
            return self._parse_cmddesc(result.stdout)
        except FileNotFoundError:
            return ""
        except Exception as e:
            return f"[cmddesc error: {e}]"

    @staticmethod
    def _parse_cmddesc(raw: str) -> str:
        """Parse la sortie de cmddesc et retourne une description propre."""
        NOISE = ("Command '", "Argument '", "String '", "Number '",
                 "IP address '", "URL '", "JSON '", "File '", "Folder '",
                 "Server '")
        sub_commands, current, mode = [], [], None

        for line in raw.splitlines():
            s = line.strip()
            if re.match(r"^=== Command \d+", s):
                if current:
                    sub_commands.append(" + ".join(current))
                current, mode = [], None
            elif "FULL DESCRIPTION APPLIED" in s:
                mode = "full"
            elif "DESCRIPTION SEQUENTIELLE" in s:
                mode = "sequential"
            elif re.match(r"^(desc_|with sudo)", s):
                value = re.sub(r"^(desc_\w+|with sudo privilege):\s*", "", s).strip()
                if not value or any(value.startswith(p) for p in NOISE):
                    continue
                if mode == "full":
                    if s.startswith("desc_cmd"):
                        current.insert(0, value)
                    else:
                        current.append(value)
                elif mode == "sequential":
                    current.append(value)

        if current:
            sub_commands.append(" + ".join(current))

        result = " | ".join(sub_commands) if sub_commands else ""
        result = re.sub(r"\bdesc_\w+:\s*", "", result).strip()
        result = re.sub(r"\s*\+\s*-\s*", ", ", result)
        result = re.sub(r"Command\s+'[^']+'\s*\+?\s*", "", result).strip()
        result = re.sub(r"^\s*-\s*", "", result).strip()
        result = re.sub(r",\s*,", ",", result).strip()
        result = re.sub(r",\s*$", "", result).strip()
        result = re.sub(r"\s{2,}", " ", result).strip()
        return result or "No description found"

    # ── Enrichissement par dictionnaires ──────

    def _get_file_type(self, filename: str) -> str:
        ext   = os.path.splitext(filename)[1].lower()
        types = []
        if ext in self.MIME_MAP:
            types.append(self.MIME_MAP[ext].get("comment", ""))
        if ext in self.FILE_EXTENSION:
            types.append(self.FILE_EXTENSION[ext])
        return ", ".join(t for t in types if t) or "file"

    # ── Construction description finale ───────

    def _build_description(self, row: dict, file_desc_map: dict) -> str:
        etype = str(row.get("event_type", "")).strip().lower()

        if etype == "file":
            filename = str(row.get("file", "")).strip()
            app      = str(row.get("app", "")).strip()
            stem     = os.path.splitext(os.path.basename(filename))[0]
            ftype    = self._get_file_type(filename)
            ai_desc  = file_desc_map.get(stem, "")
            if ai_desc:
                ai_desc = re.sub(r"^[Ii]t (likely|probably) (contains?|collects?|is|provides?)\s*", "", ai_desc).strip()

            parts = [f"{filename}, file"]
            if app:
                parts.append(f"opened with {app}")
            if ftype != "file":
                parts.append(f"contains data related to {ftype}")
            if ai_desc:
                parts.append(ai_desc)
            return ", ".join(p for p in parts if p)

        elif etype == "command":
            command  = str(row.get("command", "")).strip()
            cmd_desc = self._describe_command(command)
            if cmd_desc and cmd_desc not in ("", "No description found"):
                cmd_desc_clean = re.sub(r"^-\s*", "", cmd_desc.strip().rstrip(".")).lower()
                return f"{command}, command, executed in terminal, used to {cmd_desc_clean}"
            return f"{command}, command, executed in terminal"

        elif etype == "app":
            app = str(row.get("app", "")).strip()
            raw = str(row.get("raw", "")).strip()
            title = ""
            if raw and " - " in raw:
                parts_raw = raw.split(" - ")
                candidate = " - ".join(parts_raw[:-1]).strip()
                if candidate.lower() != app.lower():
                    title = candidate
            app_desc = self.TOOLS.get(app, "application")
            if title:
                return f"{app}, application, used to browse or use {title}"
            return f"{app}, {app_desc}, used by the user"

        elif etype == "directory":
            directory = str(row.get("directory", "")).strip()
            return f"{directory}, directory, navigated by the user"

        return ""

    # ── Point d'entrée principal ───────────────

    def describe(self, date_str: str) -> pd.DataFrame:
        """
        Lit events_normalized.csv, génère les descriptions, écrit events_described.csv.

        Args:
            date_str: date au format "YYYY-MM-DD"

        Returns:
            DataFrame avec colonne 'description' ajoutée
        """
        df = storage.read_events_normalized(date_str)
        if df.empty:
            log.error(f"events_normalized.csv vide ou absent pour {date_str}")
            return df

        df.columns = df.columns.str.strip().str.lower()

        # Collecter les stems de fichiers pour la génération IA en batch
        stems_to_process: set[str] = set()
        for fname in df[df.event_type.str.lower() == "file"]["file"]:
            if fname:
                stems_to_process.add(os.path.splitext(os.path.basename(fname))[0])

        file_desc_map: dict[str, str] = {}
        if stems_to_process:
            stems_list   = list(stems_to_process)
            descriptions = self._generate_file_descriptions(stems_list)
            file_desc_map = dict(zip(stems_list, descriptions))
            log.info(f"{len(file_desc_map)} descriptions IA générées")

        df["description"] = df.apply(
            lambda r: self._build_description(r.to_dict(), file_desc_map), axis=1
        )

        storage.write_events_described(date_str, df)
        log.info(f"events_described.csv : {len(df)} lignes")
        return df