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
    date: str
    start_time: str
    end_time: str
    duration_min: float
    entry_type: str
    title: str


@dataclass
class CommandEvent:
    timestamp: datetime
    command: str