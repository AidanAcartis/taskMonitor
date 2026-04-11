import json
import pandas as pd
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from taskmonitor.core import config, logger


class OutputAssembler:
    def __init__(self):
        self.events_path = config.DESCRIBED_EVENTS_FILE
        self.clusters_path = config.INTENTION_OUTPUT_JSONL
        self.output_path = config.EXPORTS_DIR / "final_output.json"
        self.final_output = None

    # ─────────────────────────────
    # LOADERS
    # ─────────────────────────────
    def load_events(self):
        df = pd.read_csv(self.events_path).fillna("")
        return df.to_dict("records")

    def load_clusters(self):
        clusters = []
        with open(self.clusters_path, "r") as f:
            for line in f:
                clusters.append(json.loads(line))
        return clusters
    
    # ← nouvelle méthode
    def get_final_output(self):
        if self.final_output is None:
            # si run() n'a pas été exécuté, charge depuis fichier
            with open(self.output_path, "r") as f:
                self.final_output = json.load(f)
        return self.final_output

    # ─────────────────────────────
    # HELPERS
    # ─────────────────────────────
    def normalize(self, text):
        return str(text).strip().lower()

    def to_datetime(self, date, time):
        return datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")

    # Matching robuste (clé de la correction)
    def match_event(self, event_desc, task_items_norm):
        for t in task_items_norm:
            if event_desc in t or t in event_desc:
                return True
        return False

    # ─────────────────────────────
    # SEGMENTS
    # ─────────────────────────────
    def build_segments(self, events, gap_threshold=60):
        segments = []
        if not events:
            return segments

        current_segment = {
            "start": self.to_datetime(events[0]["date"], events[0]["start"]),
            "end": self.to_datetime(events[0]["date"], events[0]["end"]),
            "duration": events[0]["duration"]
        }

        for prev, curr in zip(events, events[1:]):
            prev_end = self.to_datetime(prev["date"], prev["end"])
            curr_start = self.to_datetime(curr["date"], curr["start"])
            curr_end = self.to_datetime(curr["date"], curr["end"])

            gap = (curr_start - prev_end).total_seconds()

            if gap > gap_threshold:
                segments.append({
                    "start": current_segment["start"].strftime("%Y-%m-%d %H:%M:%S"),
                    "end": current_segment["end"].strftime("%Y-%m-%d %H:%M:%S"),
                    "duration": round(current_segment["duration"], 3)
                })

                current_segment = {
                    "start": curr_start,
                    "end": curr_end,
                    "duration": curr["duration"]
                }
            else:
                current_segment["end"] = curr_end
                current_segment["duration"] += curr["duration"]

        segments.append({
            "start": current_segment["start"].strftime("%Y-%m-%d %H:%M:%S"),
            "end": current_segment["end"].strftime("%Y-%m-%d %H:%M:%S"),
            "duration": round(current_segment["duration"], 3)
        })

        return segments

    # ─────────────────────────────
    # MAIN
    # ─────────────────────────────
    def run(self):
        logger.logger.info("[Assembler] Loading data...")

        events = self.load_events()
        clusters = self.load_clusters()

        # enrich events
        for i, e in enumerate(events):
            e["event_id"] = i
            e["description_norm"] = self.normalize(e["description"])
            e["duration"] = float(e["duration"])

        final_clusters = []

        for cluster in clusters:
            task_items = cluster["task_items"]
            task_items_norm = [self.normalize(t) for t in task_items]

            # ─────────────────────────────
            # MATCH EVENTS (ROBUST)
            # ─────────────────────────────
            cluster_events = [
                e for e in events
                if self.match_event(e["description_norm"], task_items_norm)
            ]

            # fallback (important pour stabilité pipeline)
            if not cluster_events:
                logger.logger.warning(f"[Assembler] No match for {cluster['cluster_id']}, fallback activated")
                continue

            # ─────────────────────────────
            # SORT
            # ─────────────────────────────
            cluster_events = sorted(
                cluster_events,
                key=lambda x: (x["date"], x["start"])
            )

            # ─────────────────────────────
            # TIME
            # ─────────────────────────────
            start_dt = min(self.to_datetime(e["date"], e["start"]) for e in cluster_events)
            end_dt = max(self.to_datetime(e["date"], e["end"]) for e in cluster_events)

            total_duration = sum(e["duration"] for e in cluster_events)
            num_events = len(cluster_events)

            # segments
            segments = self.build_segments(cluster_events)

            # time_span corrigé (basé sur segments)
            time_span = (end_dt - start_dt).total_seconds() / 3600

            # ─────────────────────────────
            # TASK ITEMS
            # ─────────────────────────────
            agg = defaultdict(lambda: {
                "total_duration": 0,
                "occurrences": 0
            })

            for e in cluster_events:
                desc = e["description"]
                agg[desc]["total_duration"] += e["duration"]
                agg[desc]["occurrences"] += 1

            task_items_struct = sorted(
                [
                    {
                        "description": desc,
                        "total_duration": round(v["total_duration"], 3),
                        "occurrences": v["occurrences"]
                    }
                    for desc, v in agg.items()
                ],
                key=lambda x: x["total_duration"],
                reverse=True
            )

            # ─────────────────────────────
            # CLEAN EVENTS
            # ─────────────────────────────
            cleaned_events = [
                {
                    "event_id": e["event_id"],
                    "date": e["date"],
                    "start": e["start"],
                    "end": e["end"],
                    "duration": round(e["duration"], 3),
                    "event_type": e["event_type"],
                    "file": e["file"],
                    "app": e["app"],
                    "command": e["command"],
                    "raw": e["raw"],
                    "description": e["description"]
                }
                for e in cluster_events
            ]

            # ─────────────────────────────
            # FINAL CLUSTER
            # ─────────────────────────────
            final_clusters.append({
                "cluster_id": cluster["cluster_id"],
                "global_task_intention": cluster["global_task_intention"],
                "cohesion": cluster["cohesion"],

                "stats": {
                    "total_duration": round(total_duration, 3),
                    "active_duration": round(total_duration, 3),
                    "time_span": round(time_span, 3),  # FIXED
                    "num_events": num_events,
                    "start": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "end": end_dt.strftime("%Y-%m-%d %H:%M:%S")
                },

                "segments": segments,
                "task_items": task_items_struct,
                "events": cleaned_events
            })

        # ─────────────────────────────
        # SORT FINAL
        # ─────────────────────────────
        final_clusters = sorted(
            final_clusters,
            key=lambda c: c["stats"]["start"]
        )

        # ─────────────────────────────
        # SAVE
        # ─────────────────────────────
        output = {"clusters": final_clusters}

        with open(self.output_path, "w") as f:
            json.dump(output, f, indent=2)

        logger.logger.info(f"[Assembler] Output saved → {self.output_path}")