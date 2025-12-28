from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QFormLayout, QSpinBox, QPushButton, QMessageBox
import json


class JSONMetadataPanel(QWidget):
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

        self.btn_apply = QPushButton("Apply Changes to JSON")
        self.btn_apply.clicked.connect(self.apply_changes)
        layout.addWidget(self.btn_apply)

    def load_book(self, book):
        self.book = book
        data = getattr(book, "json_data", {})  # stored JSON

        def first_or_default(val, default=""):
            if isinstance(val, list):
                return val[0] if val else default
            return val if val is not None else default

        self.title.setText(first_or_default(data.get("title"), book.title))
        self.author.setText(first_or_default(data.get("authors"), book.author))
        self.series.setText(first_or_default(data.get("series"), book.series or ""))
        self.narrators.setText(first_or_default(data.get("narrators"), ""))
        year_val = data.get("year") or data.get("published_year") or 0
        try:
            self.year.setValue(int(year_val))
        except (TypeError, ValueError):
            self.year.setValue(0)
        self.isbn.setText(first_or_default(data.get("isbn"), ""))
        self.asin.setText(first_or_default(data.get("asin"), ""))
        self.description.setPlainText(first_or_default(data.get("description"), ""))

    def apply_changes(self):
        if not self.book or not self.book.json_data:
            QMessageBox.warning(self, "No JSON", "No JSON metadata available to update.")
            return

        data = self.book.json_data
        data["title"] = self.title.text()
        data["authors"] = [self.author.text()]
        data["series"] = [self.series.text()]
        data["narrators"] = [self.narrators.text()]
        data["year"] = self.year.value()
        data["isbn"] = self.isbn.text()
        data["asin"] = self.asin.text()
        data["description"] = self.description.toPlainText()

        # Save back to JSON file
        try:
            json_file = self.book.path.parent / "metadata.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "Success", "JSON metadata updated successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save JSON: {e}")