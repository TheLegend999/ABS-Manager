from PyQt6.QtCore import QThread, pyqtSignal
from mutagen.mp4 import MP4
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

            # Check for JSON
            json_data = None
            parent_dir = os.path.dirname(file_path)
            potential_jsons = ["metadata.json", "abs_metadata.json"]
            for j_name in potential_jsons:
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
                if book.author not in library:
                    library[book.author] = {}

                # If series is None, group into "Standalone Books"
                # If series exists (from Tag), it uses that Tag Name.
                series_key = book.series if book.series else "Standalone Books"

                if series_key not in library[book.author]:
                    library[book.author][series_key] = []

                library[book.author][series_key].append(book)

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

            self.status_update.emit(f"Updating: {book.filename}")
            self.progress_update.emit(int((i / total) * 100))

            try:
                audio = MP4(book.path)

                audio.tags["\xa9nam"] = book.title
                audio.tags["\xa9ART"] = book.author
                audio.tags["aART"] = book.author

                if series and series != "Standalone Books":
                    audio.tags["\xa9grp"] = series  # Grouping
                    audio.tags["\xa9alb"] = series  # Album
                else:
                    if "\xa9grp" in audio.tags: del audio.tags["\xa9grp"]
                    if "\xa9alb" in audio.tags: del audio.tags["\xa9alb"]

                if index:
                    try:
                        idx_int = int(float(index))
                        audio.tags["disk"] = [(idx_int, 0)]
                    except ValueError:
                        pass

                audio.save()
                self.item_updated.emit(book, True)

            except Exception as e:
                print(f"Error saving {book.filename}: {e}")
                self.item_updated.emit(book, False)

        self.progress_update.emit(100)
        self.finished.emit()