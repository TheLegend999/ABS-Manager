from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from ui.json_metadata_panel import JSONMetadataPanel
from ui.m4b_metadata_panel import M4BMetadataPanel


class MetadataTabs(QWidget):
    def __init__(self):
        super().__init__()
        self.book = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # JSON metadata panel
        self.json_panel = JSONMetadataPanel()
        self.tabs.addTab(self.json_panel, "JSON Metadata")

        # M4B metadata panel
        self.m4b_panel = M4BMetadataPanel()
        self.tabs.addTab(self.m4b_panel, "M4B Metadata")

    def load_book(self, book):
        """Load a book into both metadata panels."""
        self.book = book
        if not book:
            return

        # Load JSON metadata panel
        self.json_panel.load_book(book)

        # Load M4B metadata panel
        self.m4b_panel.load_book(book)