import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

from taskmonitor.core import config, logger


class OutputAssembler:
    """
    Assemble final structured JSON from:
    - events_described.csv
    - clusters_with_intentions.jsonl
    """

    def __init__(self):
        self.events_path = config.DESCRIBED_EVENTS_FILE
        self.clusters_path = config.INTENTION_OUTPUT_JSONL
        self.output_path = config.EXPORTS_DIR / "final_output.json"

    # ─────────────────────────────────────────────
    # LOADERS
    # ─────────────────────────────────────────────
    def load_events(self):
        df = pd.read_csv(self.events_path).fillna("")
        return df.to_dict("records")

    def load_clusters(self):
        clusters = []
        with open(self.clusters_path, "r") as f:
            for line in f:
                clusters.append(json.loads(line))
        return clusters

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────
    def build_datetime(self, date, time):
        return f"{date} {time}"

    # ─────────────────────────────────────────────
    # MAIN LOGIC
    # ─────────────────────────────────────────────
    def run(self):
        logger.logger.info("[Assembler] Loading data...")

        events = self.load_events()
        clusters = self.load_clusters()

        # Ajouter event_id
        for i, e in enumerate(events):
            e["event_id"] = i

        final_clusters = []

        for cluster in clusters:
            task_items = cluster["task_items"]

            # ─────────────────────────────
            # MATCH EVENTS
            # ─────────────────────────────
            cluster_events = [
                e for e in events
                if e["description"].strip().lower() in
                [t.strip().lower() for t in task_items]
            ]

            if not cluster_events:
                continue

            # ─────────────────────────────
            # SORT EVENTS
            # ─────────────────────────────
            cluster_events = sorted(
                cluster_events,
                key=lambda x: (x["date"], x["start"])
            )

            # ─────────────────────────────
            # STATS
            # ─────────────────────────────
            total_duration = sum(e["duration"] for e in cluster_events)
            num_events = len(cluster_events)

            start_global = min(
                self.build_datetime(e["date"], e["start"])
                for e in cluster_events
            )

            end_global = max(
                self.build_datetime(e["date"], e["end"])
                for e in cluster_events
            )

            # ─────────────────────────────
            # TASK ITEMS AGGREGATION
            # ─────────────────────────────
            agg = defaultdict(lambda: {"total_duration": 0, "occurrences": 0})

            for e in cluster_events:
                desc = e["description"]
                agg[desc]["total_duration"] += e["duration"]
                agg[desc]["occurrences"] += 1

            task_items_struct = [
                {
                    "description": desc,
                    "total_duration": round(v["total_duration"], 3),
                    "occurrences": v["occurrences"]
                }
                for desc, v in agg.items()
            ]

            # ─────────────────────────────
            # CLEAN EVENTS
            # ─────────────────────────────
            cleaned_events = []
            for e in cluster_events:
                cleaned_events.append({
                    "event_id": e["event_id"],
                    "date": e["date"],
                    "start": e["start"],
                    "end": e["end"],
                    "duration": e["duration"],
                    "event_type": e["event_type"],
                    "file": e["file"],
                    "app": e["app"],
                    "command": e["command"],
                    "raw": e["raw"],
                    "description": e["description"]
                })

            # ─────────────────────────────
            # FINAL CLUSTER
            # ─────────────────────────────
            final_clusters.append({
                "cluster_id": cluster["cluster_id"],
                "global_task_intention": cluster["global_task_intention"],
                "cohesion": cluster["cohesion"],

                "stats": {
                    "total_duration": round(total_duration, 3),
                    "num_events": num_events,
                    "start": start_global,
                    "end": end_global
                },

                "task_items": task_items_struct,
                "events": cleaned_events
            })

        # ─────────────────────────────
        # SAVE
        # ─────────────────────────────
        output = {"clusters": final_clusters}

        with open(self.output_path, "w") as f:
            json.dump(output, f, indent=2)

        logger.logger.info(f"[Assembler] Output saved → {self.output_path}")