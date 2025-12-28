from PyQt6.QtCore import QThread, pyqtSignal
from mutagen.mp4 import MP4, MP4FreeForm
import os
import json
from pathlib import Path
from scanner import LibraryScanner


class ScanWorker(QThread):
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    scan_finished = pyqtSignal(dict)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        self.status_update.emit("Scanning folders...")
        library = {}

        all_files = []
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.lower().endswith((".m4b", ".m4a")):
                    all_files.append(os.path.join(root, file))

        total_files = len(all_files)
        processed = 0

        for file_path in all_files:
            processed += 1
            progress_pct = int((processed / total_files) * 100)
            self.progress_update.emit(progress_pct)

            path_obj = Path(file_path)

            # Load JSON metadata if present
            json_data = None
            parent_dir = os.path.dirname(file_path)
            for j_name in ["metadata.json", "abs_metadata.json"]:
                j_path = os.path.join(parent_dir, j_name)
                if os.path.exists(j_path):
                    try:
                        with open(j_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                        break
                    except:
                        pass

            book = LibraryScanner.parse_book(path_obj, json_data)

            if book:
                author_key = book.author
                if author_key not in library:
                    library[author_key] = {}

                series_key = book.series if book.series else "Standalone Books"
                if series_key not in library[author_key]:
                    library[author_key][series_key] = []

                library[author_key][series_key].append(book)

        self.status_update.emit("Processing complete.")
        self.scan_finished.emit(library)


class TagWorker(QThread):
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    item_updated = pyqtSignal(object, bool)
    finished = pyqtSignal()

    def __init__(self, payload):
        super().__init__()
        self.payload = payload

    def run(self):
        total = len(self.payload)
        for i, (book, series, index) in enumerate(self.payload):
            self.status_update.emit(f"Applying ABS metadata: {book.filename}")
            self.progress_update.emit(int((i / total) * 100))

            try:
                audio = MP4(book.path)

                # Helper to wrap normal text fields as list of strings
                def list_str(val):
                    return [str(val)] if val is not None else [""]

                # Apply standard tags from ABS metadata
                audio.tags["\xa9nam"] = list_str(book.title)
                audio.tags["\xa9ART"] = list_str(book.author)
                audio.tags["aART"] = list_str(book.author)

                if series and series != "Standalone Books":
                    audio.tags["\xa9grp"] = list_str(series)
                    audio.tags["\xa9alb"] = list_str(series)
                else:
                    if "\xa9grp" in audio.tags:
                        del audio.tags["\xa9grp"]
                    if "\xa9alb" in audio.tags:
                        del audio.tags["\xa9alb"]

                # Series index / disk
                if index:
                    try:
                        idx_int = int(float(index))
                        audio.tags["disk"] = [(idx_int, 0)]
                    except ValueError:
                        pass

                # Optional ABS metadata fields
                if getattr(book, "narrators", None):
                    audio.tags["----:com.apple.iTunes:Narrators"] = [MP4FreeForm(book.narrators.encode("utf-8"))]
                if getattr(book, "year", None):
                    audio.tags["\xa9day"] = list_str(book.year)
                if getattr(book, "isbn", None):
                    audio.tags["----:com.apple.iTunes:ISBN"] = [MP4FreeForm(book.isbn.encode("utf-8"))]
                if getattr(book, "asin", None):
                    audio.tags["----:com.apple.iTunes:ASIN"] = [MP4FreeForm(book.asin.encode("utf-8"))]
                if getattr(book, "description", None):
                    audio.tags["\xa9cmt"] = list_str(book.description)

                audio.save()
                self.item_updated.emit(book, True)

            except Exception as e:
                print(f"Failed to update {book.filename}: {e}")
                self.item_updated.emit(book, False)

        self.progress_update.emit(100)
        self.finished.emit()