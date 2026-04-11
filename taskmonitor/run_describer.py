import shutil
import subprocess
import sys

# ───────────────── CHECK cmddesc ─────────────────

def check_cmddesc():
    """Check that cmddesc is installed and accessible."""
    if shutil.which("cmddesc") is None:
        print("❌ cmddesc is not installed or is not in the PATH.")
        print("👉 Go to : taskmonitor/external/command_desc/")
        print("👉 Then install with : pip install .")
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
            raise Exception("cmddesc is not responding correctly")
    except Exception as e:
        print(f"❌ Error cmddesc : {e}")
        sys.exit(1)

    print("✅ cmddesc OK")


# ───────────────── RUN PIPELINE ─────────────────

def run_pipeline():
    print(" Launch of the pipeline describer...\n")

    from taskmonitor.processing.describer import main  # on va créer main()

    main()


# ───────────────── MAIN ─────────────────

if __name__ == "__main__":
    check_cmddesc()
    run_pipeline()