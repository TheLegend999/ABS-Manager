from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QFormLayout, QSpinBox, QPushButton, QMessageBox
from mutagen.mp4 import MP4, MP4FreeForm


class M4BMetadataPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.book = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.title = QLineEdit()
        self.author = QLineEdit()
        self.series = QLineEdit()
        self.narrators = QLineEdit()
        self.year = QSpinBox()
        self.year.setRange(0, 2100)
        self.isbn = QLineEdit()
        self.asin = QLineEdit()
        self.description = QTextEdit()
        self.description.setFixedHeight(80)

        form_layout.addRow(QLabel("Title:"), self.title)
        form_layout.addRow(QLabel("Author:"), self.author)
        form_layout.addRow(QLabel("Series:"), self.series)
        form_layout.addRow(QLabel("Narrators:"), self.narrators)
        form_layout.addRow(QLabel("Year:"), self.year)
        form_layout.addRow(QLabel("ISBN:"), self.isbn)
        form_layout.addRow(QLabel("ASIN:"), self.asin)
        form_layout.addRow(QLabel("Description:"), self.description)

        layout.addLayout(form_layout)

        self.btn_apply = QPushButton("Apply Changes to M4B")
        self.btn_apply.clicked.connect(self.apply_changes)
        layout.addWidget(self.btn_apply)

    def load_book(self, book):
        self.book = book
        tags = getattr(book, "m4b_tags", {}) or {}

        def first_or_default(val, default=""):
            if isinstance(val, list):
                return val[0] if val else default
            return val if val is not None else default

        try:
            self.title.setText(first_or_default(tags.get("\xa9nam", book.title)))
            self.author.setText(first_or_default(tags.get("\xa9ART", book.author)))
            self.series.setText(first_or_default(tags.get("\xa9grp", book.series or "")))
            self.narrators.setText(first_or_default(tags.get("----:com.apple.iTunes:Narrators", "")))
            year_val = first_or_default(tags.get("\xa9day", 0))
            try:
                self.year.setValue(int(year_val))
            except (TypeError, ValueError):
                self.year.setValue(0)
            self.isbn.setText(first_or_default(tags.get("----:com.apple.iTunes:ISBN", "")))
            self.asin.setText(first_or_default(tags.get("----:com.apple.iTunes:ASIN", "")))
            self.description.setPlainText(first_or_default(tags.get("\xa9cmt", "")))
        except Exception:
            self.title.setText(book.title)
            self.author.setText(book.author)
            self.series.setText(book.series or "")
            self.narrators.setText("")
            self.year.setValue(0)
            self.isbn.setText("")
            self.asin.setText("")
            self.description.setPlainText("")

    def apply_changes(self):
        if not self.book:
            QMessageBox.warning(self, "No Book", "No book loaded to update.")
            return

        try:
            audio = MP4(self.book.path)

            # Normal text tags (string lists)
            def list_str(val):
                return [str(val)] if val is not None else [""]

            audio.tags["\xa9nam"] = list_str(self.title.text())
            audio.tags["\xa9ART"] = list_str(self.author.text())
            audio.tags["aART"] = list_str(self.author.text())
            audio.tags["\xa9grp"] = list_str(self.series.text())
            audio.tags["\xa9alb"] = list_str(self.series.text())
            audio.tags["\xa9day"] = list_str(self.year.value())
            audio.tags["\xa9cmt"] = list_str(self.description.toPlainText())

            # Freeform tags need MP4FreeForm wrapper
            audio.tags["----:com.apple.iTunes:Narrators"] = [MP4FreeForm(self.narrators.text())]
            audio.tags["----:com.apple.iTunes:ISBN"] = [MP4FreeForm(self.isbn.text())]
            audio.tags["----:com.apple.iTunes:ASIN"] = [MP4FreeForm(self.asin.text())]

            audio.save()
            QMessageBox.information(self, "Success", "M4B metadata updated successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save M4B tags: {e}")