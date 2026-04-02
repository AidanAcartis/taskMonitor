from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class WindowEvent:
    timestamp: datetime
    event_type: str   # "OPENED" ou "CLOSED"
    raw_lines: List[str]


@dataclass
class FileEvent:
    timestamp: datetime
    file_path: str
    event_type: str


@dataclass
class CommandEvent:
    timestamp: datetime
    command: str