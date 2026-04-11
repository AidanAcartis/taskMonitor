import json
from collections import defaultdict
from taskmonitor.core.storage import get_connection
from datetime import datetime, timedelta


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


# ── Fonctions pour line chart ─────────────────────────────────────────────────

DOMAIN_MAP = {
    "work":          ["visual studio code", "terminal", "code .", "ls ", "git ",
                      "python", "data_command", "config.py", "documents"],
    "leisure":       ["youtube", "google chrome", "new tab", "music", "video",
                      "2002 teen fashion", "chinchilla"],
    "security":      ["burp suite", "nmap", "metasploit", "wireshark",
                      "tryhackme", "ethical hack", "devsecops"],
    "configuration": ["config", "settings", "setup", "install", "apt", "pip "],
    "study":         ["study", "learn", "course", "tutorial", "lecture", "book"],
}

def _assign_domain(description: str) -> str:
    desc = description.lower()
    for domain, keywords in DOMAIN_MAP.items():
        if any(kw in desc for kw in keywords):
            return domain
    return "other"


def _all_clusters() -> list[dict]:
    """Retourne tous les clusters de toutes les sessions."""
    conn = get_connection()
    rows = conn.execute("SELECT data FROM sessions").fetchall()
    conn.close()
    clusters = []
    for (raw,) in rows:
        data = json.loads(raw)
        clusters.extend(data.get("clusters", []))
    return clusters


def load_hourly_activity() -> dict[int, float]:
    """
    Agrège toutes les sessions.
    Retourne {heure (0-23): durée totale en heures}.
    """
    totals: dict[int, float] = defaultdict(float)
    for cluster in _all_clusters():
        start_str = cluster.get("stats", {}).get("start", "")
        duration  = cluster.get("stats", {}).get("total_duration", 0)
        if start_str:
            try:
                hour = int(start_str[11:13])
                totals[hour] += duration
            except (ValueError, IndexError):
                pass
    return dict(totals)


def load_domain_by_date() -> dict[str, dict[str, float]]:
    """
    Retourne {date: {domain: durée}} pour toutes les sessions.
    Utilisé pour le line chart multi-courbes par domaine.
    """
    result: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for cluster in _all_clusters():
        start_str = cluster.get("stats", {}).get("start", "")
        date_str  = start_str[:10] if start_str else None
        if not date_str:
            continue
        for item in cluster.get("task_items", []):
            domain   = _assign_domain(item.get("description", ""))
            duration = item.get("total_duration", 0)
            result[date_str][domain] += duration
    return {k: dict(v) for k, v in sorted(result.items())}


def load_domain_by_week() -> dict[str, dict[str, float]]:
    """
    Agrège par semaine (lundi de la semaine comme clé 'YYYY-WW').
    Retourne {semaine: {domain: durée}}.
    """
    result: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for cluster in _all_clusters():
        start_str = cluster.get("stats", {}).get("start", "")
        if not start_str:
            continue
        try:
            d = datetime.strptime(start_str[:10], "%Y-%m-%d")
            week_key = d.strftime("%Y-W%W")
        except ValueError:
            continue
        for item in cluster.get("task_items", []):
            domain   = _assign_domain(item.get("description", ""))
            duration = item.get("total_duration", 0)
            result[week_key][domain] += duration
    return {k: dict(v) for k, v in sorted(result.items())}


def load_domain_by_month() -> dict[str, dict[str, float]]:
    """Agrège par mois (YYYY-MM). Retourne {mois: {domain: durée}}."""
    result: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for cluster in _all_clusters():
        start_str = cluster.get("stats", {}).get("start", "")
        if not start_str:
            continue
        month_key = start_str[:7]
        for item in cluster.get("task_items", []):
            domain   = _assign_domain(item.get("description", ""))
            duration = item.get("total_duration", 0)
            result[month_key][domain] += duration
    return {k: dict(v) for k, v in sorted(result.items())}


def load_domain_by_year() -> dict[str, dict[str, float]]:
    """Agrège par année (YYYY). Retourne {année: {domain: durée}}."""
    result: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for cluster in _all_clusters():
        start_str = cluster.get("stats", {}).get("start", "")
        if not start_str:
            continue
        year_key = start_str[:4]
        for item in cluster.get("task_items", []):
            domain   = _assign_domain(item.get("description", ""))
            duration = item.get("total_duration", 0)
            result[year_key][domain] += duration
    return {k: dict(v) for k, v in sorted(result.items())}


def load_domain_by_session() -> list[tuple[str, dict[str, float]]]:
    """
    Retourne [(session_date, {domain: durée}), ...] triées par date.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT session_date, data FROM sessions ORDER BY session_date ASC"
    ).fetchall()
    conn.close()

    result = []
    for session_date, raw in rows:
        data    = json.loads(raw)
        domains: dict[str, float] = defaultdict(float)
        for cluster in data.get("clusters", []):
            for item in cluster.get("task_items", []):
                domain   = _assign_domain(item.get("description", ""))
                duration = item.get("total_duration", 0)
                domains[domain] += duration
        result.append((session_date, dict(domains)))
    return result