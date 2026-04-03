import shutil
import subprocess
import sys

# ───────────────── CHECK cmddesc ─────────────────

def check_cmddesc():
    """Vérifie que cmddesc est installé et accessible."""
    if shutil.which("cmddesc") is None:
        print("❌ cmddesc n'est pas installé ou pas dans le PATH.")
        print("👉 Va dans : taskmonitor/external/command_desc/")
        print("👉 Puis installe avec : pip install .")
        sys.exit(1)

    try:
        result = subprocess.run(
            ["cmddesc"],
            input="ls",
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            raise Exception("cmddesc ne répond pas correctement")
    except Exception as e:
        print(f"❌ Erreur cmddesc : {e}")
        sys.exit(1)

    print("✅ cmddesc OK")


# ───────────────── RUN PIPELINE ─────────────────

def run_pipeline():
    print("🚀 Lancement du pipeline describer...\n")

    from processing.describer import main  # on va créer main()

    main()


# ───────────────── MAIN ─────────────────

if __name__ == "__main__":
    check_cmddesc()
    run_pipeline()