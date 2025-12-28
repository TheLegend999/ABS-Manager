import os
import re
from pathlib import Path
from typing import Optional, Dict
from mutagen.mp4 import MP4
from models import Audiobook


def safe_str(val):
    """Convert any value to string for UI display, empty string if None."""
    if val is None:
        return ""
    if isinstance(val, list):
        return ", ".join(val)
    return str(val)


class LibraryScanner:
    @staticmethod
    def parse_book(path: Path, json_data: Optional[Dict]) -> Optional[Audiobook]:
        title = None
        author = None
        series_str = None
        source = "Tag"

        narrators = None
        year = None
        isbn = None
        asin = None
        description = None

        # 1. Try JSON
        if json_data:
            source = "JSON"
            title = json_data.get("title")
            authors_list = json_data.get("authors", [])
            if authors_list:
                author = authors_list[0]  # Only first author
            series_list = json_data.get("series", [])
            if series_list:
                series_str = series_list[0]

            # Optional ABS metadata
            narrators = json_data.get("narrators")
            year = json_data.get("published_year")
            isbn = json_data.get("isbn")
            asin = json_data.get("asin")
            description = json_data.get("description")

        # 2. Fallback to Tags if JSON missing
        try:
            audio = MP4(path)

            if not title:
                title = audio.tags.get("\xa9nam", [path.stem])[0]
            if not author:
                author = audio.tags.get("\xa9ART", ["Unknown"])[0]
            if not series_str:
                series_str = audio.tags.get("\xa9grp", [None])[0]

            if not narrators:
                narrators_tag = audio.tags.get("----:com.apple.iTunes:Narrators")
                if narrators_tag:
                    narrators = str(narrators_tag[0])
            if not year:
                year_tag = audio.tags.get("\xa9day")
                if year_tag:
                    year = str(year_tag[0])
            if not isbn:
                isbn_tag = audio.tags.get("----:com.apple.iTunes:ISBN")
                if isbn_tag:
                    isbn = str(isbn_tag[0])
            if not asin:
                asin_tag = audio.tags.get("----:com.apple.iTunes:ASIN")
                if asin_tag:
                    asin = str(asin_tag[0])
            if not description:
                desc_tag = audio.tags.get("\xa9cmt")
                if desc_tag:
                    description = str(desc_tag[0])

            if source == "JSON":
                source = "Mixed"
        except Exception:
            pass

        # 3. Parse Series String
        series_name = None
        series_idx = None

        if series_str:
            match = re.search(r"^(.*)\s+#(\d+(\.\d+)?)$", series_str)
            if match:
                series_name = match.group(1).strip()
                series_idx = match.group(2)
            else:
                series_name = series_str
                # Fallback to file number
                file_num_match = re.search(r"(\d+)", path.name)
                if file_num_match:
                    series_idx = file_num_match.group(1)
                    source += " (File #)"

        return Audiobook(
            path=path,
            filename=path.name,
            title=safe_str(title),
            author=safe_str(author),
            series=safe_str(series_name),
            series_index=safe_str(series_idx),
            source=safe_str(source),
            narrators=safe_str(narrators),
            year=safe_str(year),
            isbn=safe_str(isbn),
            asin=safe_str(asin),
            description=safe_str(description)
        )