import sqlite3
from pathlib import Path
from datetime import datetime

# Dossier pour stocker les DB
DB_DIR = Path.home() / ".taskmonitor" / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)

def get_db_path():
    """Retourne le chemin de la DB du mois courant et crée la DB si nécessaire"""
    now = datetime.now()
    db_file = DB_DIR / f"taskmonitor_{now.year}_{now.month:02d}.db"
    if not db_file.exists():
        create_database(db_file)
    return db_file

def create_database(db_file):
    """Crée les tables nécessaires pour stocker clusters/events/segments/task_items"""
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clusters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_id TEXT,
        global_task_intention TEXT,
        cohesion REAL,
        total_duration REAL,
        active_duration REAL,
        start DATETIME,
        end DATETIME,
        num_events INTEGER
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS task_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_id INTEGER,
        description TEXT,
        total_duration REAL,
        occurrences INTEGER,
        FOREIGN KEY(cluster_id) REFERENCES clusters(id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_id INTEGER,
        start TEXT,
        end TEXT,
        duration REAL,
        FOREIGN KEY(cluster_id) REFERENCES clusters(id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_id INTEGER,
        event_id INTEGER,
        date TEXT,
        start TEXT,
        end TEXT,
        duration REAL,
        event_type TEXT,
        file TEXT,
        app TEXT,
        command TEXT,
        raw TEXT,
        description TEXT,
        FOREIGN KEY(cluster_id) REFERENCES clusters(id)
    )""")

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(get_db_path())

def store_clusters_json(clusters_json):
    """Stocke le JSON final_output dans la DB SQLite sans dupliquer les clusters existants"""
    conn = get_connection()
    cur = conn.cursor()

    for cluster in clusters_json.get("clusters", []):
        # ── Vérifier si le cluster existe déjà ──
        cur.execute("SELECT id FROM clusters WHERE cluster_id = ?", (cluster["cluster_id"],))
        exists = cur.fetchone()
        if exists:
            print(f"Cluster {cluster['cluster_id']} déjà présent, insertion ignorée")
            continue  # passer au cluster suivant

        stats = cluster.get("stats", {})
        # ── Insertion cluster ──
        cur.execute("""
            INSERT INTO clusters (cluster_id, global_task_intention, cohesion, total_duration,
                                  active_duration, start, end, num_events)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                cluster["cluster_id"],
                cluster["global_task_intention"],
                cluster.get("cohesion"),
                stats.get("total_duration"),
                stats.get("active_duration"),
                stats.get("start"),
                stats.get("end"),
                stats.get("num_events")
            ))
        cluster_db_id = cur.lastrowid

        # ── Task items ──
        for item in cluster.get("task_items", []):
            cur.execute("""
                INSERT INTO task_items (cluster_id, description, total_duration, occurrences)
                VALUES (?, ?, ?, ?)""",
                (cluster_db_id, item["description"], item["total_duration"], item["occurrences"])
            )

        # ── Segments ──
        for seg in cluster.get("segments", []):
            cur.execute("""
                INSERT INTO segments (cluster_id, start, end, duration)
                VALUES (?, ?, ?, ?)""",
                (cluster_db_id, seg["start"], seg["end"], seg["duration"])
            )

        # ── Events ──
        for ev in cluster.get("events", []):
            cur.execute("""
                INSERT INTO events (cluster_id, event_id, date, start, end, duration, event_type,
                                    file, app, command, raw, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cluster_db_id,
                    ev.get("event_id"),
                    ev.get("date"),
                    ev.get("start"),
                    ev.get("end"),
                    ev.get("duration"),
                    ev.get("event_type"),
                    ev.get("file"),
                    ev.get("app"),
                    ev.get("command"),
                    ev.get("raw"),
                    ev.get("description")
                )
            )

    conn.commit()
    conn.close()
    print("Backup complete, duplicates automatically ignored")
