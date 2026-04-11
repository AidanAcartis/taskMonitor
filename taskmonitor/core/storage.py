import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime

DB_DIR = Path.home() / ".taskmonitor" / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)


def get_db_path():
    now = datetime.now()
    db_file = DB_DIR / f"taskmonitor_{now.year}_{now.month:02d}.db"
    if not db_file.exists():
        create_database(db_file)
    return db_file


def create_database(db_file):
    conn = sqlite3.connect(db_file)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date TEXT,
            content_hash TEXT UNIQUE,
            data TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect(get_db_path())


def normalize_for_hash(clusters_json: dict) -> str:
    """Hash based solely on the set of global_task_intentions."""
    intentions = sorted([
        c.get("global_task_intention", "")
        for c in clusters_json.get("clusters", [])
    ])
    return json.dumps(intentions, ensure_ascii=False)


def store_clusters_json(clusters_json: dict):
    serialized = normalize_for_hash(clusters_json)
    content_hash = hashlib.md5(serialized.encode()).hexdigest()

    conn = get_connection()

    existing = conn.execute(
        "SELECT session_date FROM sessions WHERE content_hash = ?",
        (content_hash,)
    ).fetchone()

    if existing:
        print(f"⏭ Content identical to session on {existing[0]}, ignored.")
        conn.close()
        return

    session_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO sessions (session_date, content_hash, data) VALUES (?, ?, ?)",
        (session_date, content_hash, json.dumps(clusters_json, ensure_ascii=False, indent=2))
    )
    conn.commit()
    conn.close()
    print(f"💾 Session recorded : {session_date}")