from typing import Optional
from mutagen.mp4 import MP4
from models import Audiobook


class TagEditor:
    """Handles writing metadata back to the files."""

    @staticmethod
    def update_series_tag(book: Audiobook, series_name: str, series_index: Optional[str]) -> bool:
        try:
            audio = MP4(book.path)

            tag_value = series_name
            if series_index:
                tag_value = f"{series_name} #{series_index}"

            # Special case: Clear the tag if it's a standalone
            if series_name == "Standalone Books":
                if "\xa9grp" in audio.tags:
                    del audio.tags["\xa9grp"]
            else:
                audio.tags["\xa9grp"] = [tag_value]

            audio.save()
            return True
        except Exception as e:
            print(f"Failed to update {book.filename}: {e}")
            return False