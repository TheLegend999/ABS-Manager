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

    # New ABS fields
    description: Optional[str] = None
    narrator: Optional[str] = None
    year: Optional[int] = None
    isbn: Optional[str] = None
    asin: Optional[str] = None