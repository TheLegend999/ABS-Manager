from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Audiobook:
    path: Path
    filename: str
    title: str
    author: str
    series: Optional[str]
    series_index: Optional[str]
    source: str