from typing import Optional
from .tokenizer import is_quoted
from .constants import (
    TYPE_REGEX,
    ARG_TYPE,
    HTTP_METHODS,
    SERVER,
    GATEWAY,
    TCPDUMP_OPTIONS,
    HYDRA_OPTIONS,
    INTERFACE_CMDS,
    NETWORK_CMDS,
    NON_ARG_TYPES
)

def detect_type(
    token: str,
    main_cmd: Optional[str] = None,
    prev_token: Optional[str] = None,
    index: Optional[int] = None,
) -> str:

    token = token.strip()
    if not token:
        return "arg"

    if index == 0:
        return "cmd"

    # Main command
    if main_cmd and token == main_cmd:
        return "cmd"
    if main_cmd and token.startswith(main_cmd + " "):
        if any(tok.startswith("-") for tok in token.split()[1:]):
            return "cmdopt"
        elif len(token.split()) >= 1:
            return "cmdopt"
    if " " in token and any(tok.startswith("-") for tok in token.split()[1:]):
        return "cmdopt"
    
    prev_last = None
    if prev_token:
        prev_last = prev_token.strip().split()[-1]
    
    # String / JSON / URL
    if is_quoted(token):
        inner = token[1:-1]
        # JSON check
        if TYPE_REGEX["json"].match(inner):
            return "json"
        # URL check
        if TYPE_REGEX["url"].match(inner):
            return "url"
        return "string"
    
    # Python module
    if main_cmd == "python" and prev_token == "-m":
        return "python_module"
    
    # Remote target
    if TYPE_REGEX["remote_target"].match(token):
        return "remote_target"
    
    if TYPE_REGEX["domain"].match(token):
        return "domain"
    
    # IP, IPv6, URL
    for name in ["ip", "ipv6", "url"]:
        if TYPE_REGEX[name].match(token):
            return name
    
     # CIDR (ex: 192.168.1.0/24)
    if TYPE_REGEX["cidr"].match(token):
        return "cidr"

    # Port range (ex: 1-1024)
    if TYPE_REGEX["port_range"].match(token):
        a, b = token.split("-", 1)
        try:
            ai = int(a); bi = int(b)
            if 0 <= ai <= 65535 and 0 <= bi <= 65535:
                return "port_range"
        except Exception:
            pass
    
    # -------------------------------
    # Contextual Detection Port vs Number
    # -------------------------------
    if TYPE_REGEX["port"].match(token):
        num = int(token)

        # If preceded by an explicit port option
        if prev_token in (
            "-p",
            "--port",
            "--listen-port",
            "--connect-port",
            "port",
            "http.server",
            "redis-cli -p",
        ):
            return "port"
        
        # If it is a likely port (in a network command)
        if main_cmd in NETWORK_CMDS and 1 <= num <= 65535:
            return "port"
        
        # Otherwise, it's probably a number
        return "number"

    # General numbers
    if TYPE_REGEX["number"].match(token):
        return "number"
    
    if main_cmd == "tcpdump" and prev_token:
        last = prev_token.split()[-1]
        if last == "port":
            return "port" if TYPE_REGEX["port"].match(token) else "arg"

    # TCPDUMP contextual detection
    if main_cmd == "tcpdump" and prev_token:
        last = prev_token.split()[-1]
        if last in TCPDUMP_OPTIONS:
            return TCPDUMP_OPTIONS[last]
        
    if token.lower() in GATEWAY:
                return "gateway"
    
    if main_cmd == "hydra" and prev_last:
                if prev_last in HYDRA_OPTIONS:
                    return HYDRA_OPTIONS[prev_last]
                
    if token.upper() in HTTP_METHODS:
        return "http_method"
    
    if TYPE_REGEX["domain"].match(token):
        return "domain"

    if main_cmd == "python" and prev_token and prev_token.strip().endswith("-m"):
        return "python_module"
    
    if token.lower() in SERVER:
                return "server"

    if TYPE_REGEX["arg_type"].match(token):
        # But be careful: don't treat things that look like domain/ip/url as arg
        if not any(TYPE_REGEX[t].match(token) for t in NON_ARG_TYPES):
            return "arg"

    # Files, Folders...
    for name in ["folder", "file", "device", "envfile", "script", "archive"]:
        if TYPE_REGEX[name].match(token):
            if TYPE_REGEX[name].match(token) or token == ".":
                return "folder" if token == "." else name
            
            if main_cmd == "host" and TYPE_REGEX["dns_type"].match(token):
                return "dns_type"
            
            if main_cmd == "tcpdump" and prev_token in TCPDUMP_OPTIONS:
                return TCPDUMP_OPTIONS[prev_token]
            
            if main_cmd == "ethtool" and prev_token in INTERFACE_CMDS:
                return "network_interface"

            return name


    if token.startswith("-"):
        return "option"

    return "arg"


def normalize_token(tok: str) -> str:
    return " ".join(tok.strip().split())
