import subprocess
import sys
import time

from taskmonitor.collectors.window_monitor import WindowMonitor
from taskmonitor.collectors.command_collector import CommandCollector
from taskmonitor.collectors.log_extractor import LogExtractor
from taskmonitor.collectors.file_collector import FileCollector
from taskmonitor.collectors.collect_data import DataCollector
from taskmonitor.processing.parser import EventParser
from taskmonitor.processing.assembler import OutputAssembler
from taskmonitor.core.storage import store_clusters_json


# ─────────────────────────────────────────────
# MONITORING MODE
# ─────────────────────────────────────────────
def run_monitoring():
    print("\n[MODE] MONITORING\n")

    wm = WindowMonitor()
    wm.start()

    try:
        while True:
            print("📥 Collecting command's logs...")
            CommandCollector().run()

            # fréquence (ex: toutes les 30 sec)
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n🛑 Stopping requested")
        wm.stop()


# ─────────────────────────────────────────────
# PROCESSING MODE
# ─────────────────────────────────────────────
def run_processing():
    print("\n[MODE] PROCESSING\n")

    # # 1. Extraction logs
    # LogExtractor().run()

    # 2. File collection
    FileCollector().run()

    # 3. Merge data
    DataCollector().run()

    # 4. Parser
    EventParser().run()

    # 5. Describer (external pipeline)
    run_step("taskmonitor.run_describer")

    # 6. Clustering
    run_step("taskmonitor.run_clusterer")

    # 7. Intention
    run_step("taskmonitor.run_predict_intention")

    # 8. Assemble final output
    OutputAssembler().run()

    final_output = OutputAssembler().get_final_output()  # méthode à ajouter pour récupérer le JSON
    store_clusters_json(final_output)
    print("💾 Data stored in SQLite successfully")

    print("\nPROCESSING COMPLETED")


# ─────────────────────────────────────────────
# RUN STEP (safe subprocess)
# ─────────────────────────────────────────────
def run_step(module):
    print(f"\n➡️ {module}")

    result = subprocess.run(
        ["python3", "-m", module]
    )

    if result.returncode != 0:
        print(f"❌ Error in {module}")
        sys.exit(1)


# ─────────────────────────────────────────────
# ALL-IN-ONE MODE
# ─────────────────────────────────────────────
def run_all():
    print("\n[MODE] ALL-IN-ONE\n")

    # lancer monitoring en background
    monitor_process = subprocess.Popen(
        ["python3", "-m", "taskmonitor.orchestrator", "monitor"]
    )

    # attendre un peu pour générer des logs
    time.sleep(10)

    # lancer processing
    run_processing()

    # arrêter monitoring
    monitor_process.terminate()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python -m taskmonitor.orchestrator [monitor|process|all]")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "monitor":
        run_monitoring()

    elif mode == "process":
        run_processing()

    elif mode == "all":
        run_all()

    else:
        print("Mode inconnu")


if __name__ == "__main__":
    main()