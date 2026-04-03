import re

# -------------------------
#  Simple detection type
# -------------------------
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
NETWORK_CMDS = {
    "ssh",
    "nc",
    "nmap",
    "telnet",
    "curl",
    "ftp",
}
SERVER = ["nginx", "apache"]
GATEWAY = ["gw"]
TCPDUMP_OPTIONS = {
    "-i": "network_interface",
    "-w": "file"
}
HYDRA_OPTIONS = {
    "-l": "username"
}
NON_ARG_TYPES = ["domain", "ip", "url", "dns_type"]
ARG_TYPE = ["root", "ssh", "port", "verbose", "show", "default", "get"]
INTERFACE_CMDS = ["ethtool", "ip", "ifconfig", "tcpdump"]
TYPE_REGEX = {
    #Foders and Files
    "folder": re.compile(r"^(/|~)[\w\-/]+/?$"),
    "file": re.compile(r"^(?:/[\w\-/]+|\.?/[\w\-/]+|[\w\-.]+)\.[\w]+$"),
    "device": re.compile(r"^/dev/[^\s]+$"),
    "envfile": re.compile(r"^(?:\.|/)?[\w\.-]+\.(?:env|conf|ini)$"),
    "script": re.compile(r"^\./[\w\.-]+\.sh$"),
    "archive": re.compile(r"^[\w\.-]+\.(?:tar|gz|zip|bz2|xz)$"),

    # Network
    "ip": re.compile(
        r"^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
        r"\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
        r"\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
        r"\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)$"
    ),
    "ipv6": re.compile(r"^([0-9a-fA-F]{0,4}:){1,7}[0-9a-fA-F]{0,4}$"),
    "port": re.compile(r"^\d{1,5}$"),
    "url": re.compile(r"^https?://[^\s]+$", re.IGNORECASE),
    "remote_target": re.compile(r"^[\w.-]+@[\w\.-]+(:/[\w\./-]*)?$"),
    "http_method": re.compile(r"^(?:" + "|".join(HTTP_METHODS) + r")$", re.IGNORECASE),
    "server": re.compile(r"^(?:" + "|".join(SERVER) + r")$", re.IGNORECASE),
    "domain": re.compile(
            r"^(?:[a-zA-Z0-9][a-zA-Z0-9-]*\.)+"  # subdomains
            r"(com|net|org|info|biz|name|xyz|online|site|tech|app|"  # Modern gTLDs
            r"fr|us|uk|de|jp|io|"                                      # ccTLD
            r"edu|gov|mil)"                                           # special/sponsored
            r"(?::\d{1,5})?$"                                         # optional port
        ),
    "dns_type": re.compile(r"^(A|AAAA|MX|CNAME|TXT|NS|SOA|PTR|SRV|CAA)$", re.IGNORECASE),
    "port_range": re.compile(r"^\d{1,5}-\d{1,5}$"),
    # simple IPv4 cidr ex: 192.168.1.0/24
    "cidr": re.compile(r"^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
                       r"(?:\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}"
                       r"/(?:[0-9]|[12]\d|3[0-2])$"),
    "arg_type": re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,19}$"),

    # Data
    "json": re.compile(r"^\{.*\}$"),
    "string": re.compile(r"^(['\"]).*\1$"),

    # Numbers and Units
    "number": re.compile(r"^-?\d+(\.\d+)?$"),
}

# -------------------------------
# Dictionary of descriptions
# -------------------------------
TYPE_DESCRIPTION = {
    "file": "File",
    "folder": "Folder",
    "device": "Device",
    "envfile": "Environment file",
    "script": "Script",
    "archive": "Archive",
    "ip": "IP address",
    "ipv6": "IPv6 address",
    "port": "Port number",
    "url": "URL",
    "json": "JSON",
    "string": "String",
    "number": "Number",
    "remote_target": "Remote target",
    "arg": "Argument",
    "server": "Server",
    "http_method": "Http method",
    "domain": "Website / Domain",
    "dns_type": "DNS record type",
    "network_interface": "Network interface",
    "port_range": "Port range",
    "cidr": "Network (CIDR)",
    "gateway": "Gateway",
    "username": "Username",
    "python_module": "Python module"
}