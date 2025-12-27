import os
import re
from pathlib import Path
from typing import Optional, Dict
from mutagen.mp4 import MP4
from models import Audiobook


class LibraryScanner:
    @staticmethod
    def parse_book(path: Path, json_data: Optional[Dict]) -> Optional[Audiobook]:
        title = None
        author = None
        series_str = None
        source = "Tag"

        # 1. Try JSON
        if json_data:
            source = "JSON"
            title = json_data.get("title")
            authors_list = json_data.get("authors", [])
            if authors_list:
                author = ", ".join(authors_list)
            series_list = json_data.get("series", [])
            if series_list:
                series_str = series_list[0]

        # 2. Fallback to Tags
        try:
            audio = MP4(path)

            if not title:
                title = audio.tags.get("\xa9nam", [path.stem])[0]
            if not author:
                author = audio.tags.get("\xa9ART", ["Unknown"])[0]
            if not series_str:
                series_str = audio.tags.get("\xa9grp", [None])[0]

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
            title=title if title else path.stem,
            author=author if author else "Unknown",
            series=series_name,
            series_index=series_idx,
            source=source
        )