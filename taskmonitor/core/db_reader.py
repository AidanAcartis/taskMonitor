import json
from collections import defaultdict
from taskmonitor.core.storage import get_connection


def load_all_sessions() -> list[tuple[int, str, dict]]:
    """Retourne [(id, session_date, data), ...] triées par date décroissante."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, session_date, data FROM sessions ORDER BY session_date DESC"
    ).fetchall()
    conn.close()
    return [(row[0], row[1], json.loads(row[2])) for row in rows]


def load_latest_session() -> dict | None:
    """Retourne le data dict de la session la plus récente, ou None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT data FROM sessions ORDER BY session_date DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def load_activity_counts() -> dict[str, int]:
    """
    Retourne un dict 'YYYY-MM-DD' -> count pour le heatmap.
    Chaque cluster dans chaque session compte comme une activité.
    """
    conn = get_connection()
    rows = conn.execute("SELECT data FROM sessions").fetchall()
    conn.close()

    counts: dict[str, int] = defaultdict(int)
    for (raw,) in rows:
        data = json.loads(raw)
        for cluster in data.get("clusters", []):
            start_str = cluster.get("stats", {}).get("start", "")
            if start_str:
                counts[start_str[:10]] += 1

    return dict(counts)

def load_clusters_by_date(date_str: str) -> dict:
    """
    Retourne un dict {'clusters': [...]} avec tous les clusters
    de toutes les sessions dont la date d'activité correspond à date_str (YYYY-MM-DD).
    """
    conn = get_connection()
    rows = conn.execute("SELECT data FROM sessions").fetchall()
    conn.close()

    clusters = []
    for (raw,) in rows:
        data = json.loads(raw)
        for cluster in data.get("clusters", []):
            start_str = cluster.get("stats", {}).get("start", "")
            if start_str[:10] == date_str:
                clusters.append(cluster)

    return {"clusters": clusters}


def load_available_dates() -> list[str]:
    """
    Retourne la liste triée (décroissante) de toutes les dates d'activité
    présentes dans toutes les sessions.
    """
    conn = get_connection()
    rows = conn.execute("SELECT data FROM sessions").fetchall()
    conn.close()

    dates = set()
    for (raw,) in rows:
        data = json.loads(raw)
        for cluster in data.get("clusters", []):
            start_str = cluster.get("stats", {}).get("start", "")
            if start_str:
                dates.add(start_str[:10])

    return sorted(dates, reverse=True)