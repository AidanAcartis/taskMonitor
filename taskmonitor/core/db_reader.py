import json
from collections import defaultdict
from taskmonitor.core.storage import get_connection
from datetime import datetime, timedelta


def load_all_sessions() -> list[tuple[int, str, dict]]:
    """Returns [(id, session_date, data), ...] sorted by descending date."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, session_date, data FROM sessions ORDER BY session_date DESC"
    ).fetchall()
    conn.close()
    return [(row[0], row[1], json.loads(row[2])) for row in rows]


def load_latest_session() -> dict | None:
    """Returns the data dict of the most recent session, or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT data FROM sessions ORDER BY session_date DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def load_activity_counts() -> dict[str, int]:
    """
    Returns a dict 'YYYY-MM-DD' -> count for the heatmap.
    Each cluster in each session counts as an activity.
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
    Returns a dict {'clusters': [...]} with all clusters
    from all sessions whose activity date matches date_str (YYYY-MM-DD).
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
    Returns the sorted (descending) list of all activity dates
    present in all sessions.
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

    # ── Software development ──────────────────────────────────────────────────
    "development": [
        "visual studio code", "vscode", "code .", "vim", "neovim", "emacs",
        "sublime text", "jetbrains", "intellij", "pycharm", "webstorm",
        "android studio", "xcode", "eclipse", "netbeans",
        "terminal", "bash", "zsh", "fish", "sh ", "shell",
        "git ", "github", "gitlab", "bitbucket", "git commit", "git push",
        "git pull", "git merge", "git clone", "git status",
        "python", "javascript", "typescript", "java", "kotlin", "swift",
        "rust", "go ", "golang", "c++", "c#", "php", "ruby", "scala",
        "docker", "kubernetes", "kubectl", "helm", "compose",
        "npm ", "yarn ", "pip ", "cargo ", "gradle", "maven",
        "makefile", "cmake", "webpack", "vite", "babel",
        "postgresql", "mysql", "sqlite", "mongodb", "redis",
        "api", "rest", "graphql", "swagger", "postman", "insomnia",
        "localhost", "127.0.0.1", "flask", "django", "fastapi",
        "react", "vue", "angular", "next.js", "nuxt",
        "stack overflow", "stackoverflow", "github.com",
    ],

    # ── Cybersecurity / Hacking ───────────────────────────────────────────────
    "security": [
        "burp suite", "nmap", "metasploit", "wireshark", "aircrack",
        "john the ripper", "hashcat", "hydra", "sqlmap", "nikto",
        "gobuster", "dirb", "ffuf", "wfuzz", "dirsearch",
        "kali", "parrot os", "blackarch",
        "tryhackme", "hackthebox", "ctf", "capture the flag",
        "reverse shell", "payload", "exploit", "privilege escalation",
        "buffer overflow", "xss", "sql injection", "csrf",
        "pen test", "penetration", "vulnerability", "cve",
        "shodan", "censys", "recon-ng", "maltego",
        "netcat", "nc ", "socat", "tcpdump", "ettercap",
        "ghidra", "ida pro", "radare2", "binary ninja", "gdb",
        "devsecops", "owasp", "ethical hack", "red team", "blue team",
    ],

    # ── System administration / DevOps ────────────────────────────────────────
    "sysadmin": [
        "nginx", "apache", "caddy", "haproxy",
        "ansible", "terraform", "puppet", "chef", "vagrant",
        "systemctl", "journalctl", "crontab", "daemon",
        "ssh ", "sftp", "rsync", "scp ",
        "iptables", "ufw", "firewall",
        "cpu usage", "ram", "disk usage", "htop", "top ", "iotop",
        "mount ", "fdisk", "lsblk", "df ", "du ",
        "backup", "snapshot", "raid",
        "aws", "azure", "gcp", "google cloud", "digitalocean", "linode",
        "prometheus", "grafana", "elasticsearch", "kibana", "logstash",
        "ci/cd", "jenkins", "github actions", "gitlab ci", "circleci",
    ],

    # ── Data science / AI / ML ────────────────────────────────────────────────
    "data_science": [
        "jupyter", "notebook", "pandas", "numpy", "scipy",
        "matplotlib", "seaborn", "plotly", "bokeh",
        "scikit", "sklearn", "tensorflow", "pytorch", "keras",
        "huggingface", "transformers", "llm", "gpt", "bert", "t5",
        "kaggle", "colab", "google colab",
        "dataset", "training", "fine-tuning", "inference",
        "clustering", "classification", "regression", "neural",
        "embedding", "tokenizer", "model",
        "r studio", "rstudio", "tableau", "power bi",
        "sql ", "dbt ", "airflow", "spark", "hadoop",
    ],

    # ── Configuration / Setup ─────────────────────────────────────────────────
    "configuration": [
        "config", "settings", "setup", "install", "uninstall",
        "apt ", "apt-get", "dpkg", "snap ", "flatpak",
        "brew ", "pacman", "yum ", "dnf ",
        "dotfiles", ".bashrc", ".zshrc", ".vimrc", ".gitconfig",
        "environment variable", "export ", "path=",
        "driver", "firmware", "bios", "grub",
        "virtualbox", "vmware", "qemu", "libvirt",
        "wine ", "lutris", "proton",
    ],

    # ── Study / Learning ──────────────────────────────────────────────────────
    "study": [
        "study", "learn", "learning", "course", "tutorial",
        "lecture", "lesson", "class", "module", "chapter",
        "book", "ebook", "pdf", "textbook",
        "coursera", "udemy", "edx", "pluralsight", "linkedin learning",
        "mit opencourseware", "khan academy", "freecodecamp",
        "documentation", "docs.", "devdocs", "mdn",
        "research", "paper", "arxiv", "scholar",
        "anki", "flashcard", "quizlet",
        "exam", "quiz", "certification", "cisco", "comptia",
    ],

    # ── Communication / Collaboration ─────────────────────────────────────────
    "communication": [
        "slack", "discord", "teams", "zoom", "meet",
        "gmail", "outlook", "thunderbird", "mail",
        "telegram", "whatsapp", "signal", "messenger",
        "notion", "confluence", "jira", "trello", "asana",
        "linear", "clickup", "monday",
        "mattermost", "rocketchat",
    ],

    # ── Social networks ───────────────────────────────────────────────────────
    "social": [
        "twitter", "x.com", "facebook", "instagram", "linkedin",
        "reddit", "tiktok", "snapchat", "pinterest", "tumblr",
        "mastodon", "bluesky", "threads",
        "twitch", "kick.com",
        "hacker news", "news.ycombinator",
    ],

    # ── Multimedia / Entertainment ────────────────────────────────────────────
    "entertainment": [
        "youtube", "netflix", "spotify", "twitch", "prime video",
        "disney+", "hulu", "crunchyroll", "hianime", "aniwatch",
        "vlc", "mpv", "kodi",
        "music", "playlist", "podcast", "soundcloud",
        "lyrics", "song", "album", "artist",
        "movie", "series", "episode", "anime", "manga",
        "stream", "watch ",
    ],

    # ── Gaming ────────────────────────────────────────────────────────────────
    "gaming": [
        "steam", "epic games", "gog ", "itch.io",
        "minecraft", "valorant", "league of legends", "dota",
        "fortnite", "apex legends", "overwatch", "csgo", "cs2",
        "game", "gaming", "gamepad", "controller",
        "unity", "unreal engine", "godot",
        "emulator", "retroarch", "pcsx2",
        "lutris", "proton", "wine game",
    ],

    # ── Creative / Design ─────────────────────────────────────────────────────
    "creative": [
        "gimp", "inkscape", "krita", "blender", "kdenlive",
        "photoshop", "illustrator", "premiere", "after effects",
        "figma", "sketch", "canva", "adobe xd",
        "audacity", "ardour", "lmms", "reaper",
        "obs studio", "obs ", "recording", "streaming setup",
        "3d model", "render", "animation",
        "writing", "novel", "screenplay", "blog post",
    ],

    # ── Finance / Productivity ────────────────────────────────────────────────
    "productivity": [
        "libreoffice", "excel", "word", "powerpoint",
        "google docs", "google sheets", "google slides",
        "obsidian", "logseq", "roam", "onenote", "evernote",
        "calendar", "agenda", "todo", "task",
        "budget", "finance", "accounting", "invoice",
        "crypto", "bitcoin", "ethereum", "binance", "coinbase",
        "trading", "stock", "investment",
    ],

    # ── Web browsing (generic) ────────────────────────────────────────────────
    "browsing": [
        "google chrome", "firefox", "brave", "edge", "safari",
        "new tab", "history", "bookmark",
        "google.com", "bing.com", "duckduckgo",
        "wikipedia", "wikimedia",
    ],

    "other": [],  # fallback
}

def _assign_domain(description: str) -> str:
    desc = description.lower()
    for domain, keywords in DOMAIN_MAP.items():
        if any(kw in desc for kw in keywords):
            return domain
    return "other"


def _all_clusters() -> list[dict]:
    """Returns all clusters from all sessions."""
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
    Aggregates all sessions.
    Returns {hour (0-23): total duration in hours}.
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
    Returns {date: {domain: duration}} for all sessions.
    Used for the line chart with multiple curves by domain.
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
    Aggregates by week (Monday of the week as key 'YYYY-WW').
    Returns {week: {domain: duration}}.
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
    """Aggregates by month (YYYY-MM). Returns {month: {domain: duration}}."""
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
    """Aggregates by year (YYYY). Returns {year: {domain: duration}}."""
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
    Returns [(session_date, {domain: duration}), ...] sorted by date.
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