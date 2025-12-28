from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox, QStyle
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor

from models import Audiobook


class LibraryTree(QTreeWidget):
    book_selected = pyqtSignal(Audiobook)
    request_tag_sync = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderLabels(["Hierarchy / Title", "Index", "Source", "Filename"])
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.customContextMenuRequested.connect(self.open_context_menu)
        self.itemSelectionChanged.connect(self.on_selection_changed)

        self.book_item_map = {}
        self.library_data = {}

    def populate(self, library_data):
        self.clear()
        self.book_item_map.clear()
        self.library_data = library_data

        self.setSortingEnabled(False)

        icon_author = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        icon_series = self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        icon_book = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)

        for author in sorted(library_data.keys()):
            author_item = QTreeWidgetItem(self)
            author_item.setText(0, author)
            author_item.setIcon(0, icon_author)
            author_item.setData(0, Qt.ItemDataRole.UserRole, "AUTHOR")
            author_item.setExpanded(True)

            for series in sorted(library_data[author].keys(),
                                 key=lambda x: (x == "Standalone Books", x)):

                series_item = QTreeWidgetItem(author_item)
                series_item.setText(0, series)
                series_item.setIcon(0, icon_series)
                series_item.setData(0, Qt.ItemDataRole.UserRole, "SERIES")
                series_item.setForeground(0, QBrush(QColor("#88c0d0")))

                books = library_data[author][series]
                books.sort(key=lambda b: (float(b.series_index)
                                          if b.series_index else float("inf"), b.title))

                for book in books:
                    item = QTreeWidgetItem(series_item)
                    item.setText(0, book.title)
                    item.setText(1, book.series_index or "-")
                    item.setText(2, book.source)
                    item.setText(3, book.filename)
                    item.setIcon(0, icon_book)
                    item.setData(0, Qt.ItemDataRole.UserRole, book)

                    self.book_item_map[book.path] = item

        self.setSortingEnabled(True)

    def on_selection_changed(self):
        items = self.selectedItems()
        if not items:
            return

        data = items[0].data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, Audiobook):
            self.book_selected.emit(data)

    def open_context_menu(self, position):
        item = self.itemAt(position)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        if data in ("AUTHOR", "SERIES"):
            label = item.text(0)
            action = menu.addAction(f"Sync tags for {label}")
            action.triggered.connect(lambda: self.prepare_tag_sync(item))

        if not menu.isEmpty():
            menu.exec(self.viewport().mapToGlobal(position))

    def prepare_tag_sync(self, root_item):
        payload = []

        def collect(item):
            for i in range(item.childCount()):
                child = item.child(i)
                data = child.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(data, Audiobook):
                    payload.append((data, child.parent().text(0), data.series_index))
                else:
                    collect(child)

        collect(root_item)

        if not payload:
            return

        confirm = QMessageBox.question(
            self, "Confirm",
            f"Update tags for {len(payload)} files?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.request_tag_sync.emit(payload)