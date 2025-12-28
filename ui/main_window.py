from typing import Optional, List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QTreeWidget, QTreeWidgetItem, QLabel, QHeaderView,
    QProgressBar, QApplication, QGroupBox, QFormLayout, QMenu, QAction
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QBrush, QColor, QFont

from models import Audiobook
from workers import ScanWorker, TagWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audiobook Metadata Manager")
        self.resize(1400, 750)

        self.settings = QSettings("AudiobookManager", "MainApp")

        self.library_data = {}
        self.scan_worker: Optional[ScanWorker] = None
        self.tag_worker: Optional[TagWorker] = None
        self.book_item_map = {}
        self.selected_books: List[QTreeWidgetItem] = []

        self._apply_theme()
        self._init_ui()

    def _apply_theme(self):
        font = QFont("Segoe UI", 10)
        if not font.exactMatch():
            font = QFont("Roboto", 10)
        QApplication.setFont(font)

        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #242424; color: #eeeeee; }
            QTreeWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #1b1b1b;
                alternate-background-color: #323232;
                selection-background-color: transparent;
                selection-color: #ffffff;
            }
            QTreeWidget::item { padding: 4px; border-bottom: 1px solid #282828; }
            QHeaderView::section {
                background-color: #303030; color: #bbbbbb; padding: 6px; border: none; font-weight: bold;
            }
            QPushButton {
                background-color: #3a3a3a; color: #ffffff; border: 1px solid #1b1b1b;
                padding: 8px 16px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #444444; }
            QProgressBar {
                border: 1px solid #1b1b1b; background-color: #1e1e1e; border-radius: 4px; color: white;
            }
            QProgressBar::chunk { background-color: #3584e4; }
            QStatusBar { background-color: #303030; color: #cccccc; border-top: 1px solid #1b1b1b; }
            QGroupBox { border: 1px solid #1b1b1b; border-radius: 5px; margin-top: 6px; }
            QGroupBox:title { subcontrol-origin: margin; left: 8px; padding: 0 3px 0 3px; }
        """)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Left: Tree + controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_select = QPushButton("Select Library Folder")
        self.btn_select.clicked.connect(self.select_folder)
        left_layout.addWidget(self.btn_select)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        left_layout.addWidget(self.progress_bar)

        self.selected_count_label = QLabel("Selected books: 0")
        left_layout.addWidget(self.selected_count_label)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Title", "Series", "Index", "Author", "Year", "Narrators", "ISBN", "ASIN", "Filename"])
        self.tree.setAlternatingRowColors(True)
        self.tree.itemClicked.connect(self.on_item_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)

        header = self.tree.header()
        for i in range(self.tree.columnCount()):
            if i == 0:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        left_layout.addWidget(self.tree)

        self.btn_apply_tags = QPushButton("Apply Tags")
        self.btn_apply_tags.clicked.connect(self.apply_bulk_tags)
        left_layout.addWidget(self.btn_apply_tags)

        main_layout.addWidget(left_widget, 3)

        # Right: Metadata preview
        self.preview_group = QGroupBox("Metadata Preview")
        preview_layout = QFormLayout()
        self.preview_group.setLayout(preview_layout)

        self.preview_labels = {}
        for field in ["Title", "Series", "Index", "Author", "Year", "Narrators", "ISBN", "ASIN", "Filename"]:
            label = QLabel("")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.preview_labels[field] = label
            preview_layout.addRow(f"{field}:", label)

        main_layout.addWidget(self.preview_group, 2)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready to scan.")

    def select_folder(self):
        last_dir = self.settings.value("last_dir", "")
        folder = QFileDialog.getExistingDirectory(self, "Select Audiobooks Folder", last_dir)
        if folder:
            self.settings.setValue("last_dir", folder)
            self.btn_select.setEnabled(False)
            self.tree.clear()
            self.book_item_map = {}
            self.selected_books.clear()
            self.selected_count_label.setText("Selected books: 0")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            self.scan_worker = ScanWorker(folder)
            self.scan_worker.status_update.connect(self.status_bar.showMessage)
            self.scan_worker.progress_update.connect(self.progress_bar.setValue)
            self.scan_worker.scan_finished.connect(self.on_scan_finished)
            self.scan_worker.start()

    def on_scan_finished(self, data):
        self.library_data = data
        self.populate_tree()
        self.btn_select.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Scan Complete. Found {len(self.library_data)} Authors.")
        self.scan_worker = None

    def populate_tree(self):
        self.tree.clear()
        self.book_item_map = {}
        self.tree.setSortingEnabled(False)

        sorted_authors = sorted(self.library_data.keys())
        for author in sorted_authors:
            author_item = QTreeWidgetItem(self.tree)
            author_item.setText(0, author)
            author_item.setExpanded(True)
            author_item.setData(0, Qt.ItemDataRole.UserRole, "AUTHOR")

            font = author_item.font(0)
            font.setBold(True)
            font.setPointSize(11)
            author_item.setFont(0, font)

            series_dict = self.library_data[author]
            series_keys = sorted(series_dict.keys(), key=lambda x: (x == "Standalone Books", x))

            for series in series_keys:
                series_item = QTreeWidgetItem(author_item)
                series_item.setText(0, series)
                series_item.setData(0, Qt.ItemDataRole.UserRole, "SERIES")
                series_item.setForeground(0, QBrush(QColor("#88c0d0")))

                books = series_dict[series]
                books.sort(key=lambda b: (float(b.series_index) if b.series_index else float('inf'), b.title))

                for book in books:
                    book_item = QTreeWidgetItem(series_item)
                    book_item.setText(0, book.title)
                    book_item.setText(1, f"{book.series} #{book.series_index}" if book.series_index else book.series)
                    book_item.setText(2, str(book.series_index) if book.series_index else "")
                    book_item.setText(3, book.author or "")
                    book_item.setText(4, str(book.year) if getattr(book, "year", None) else "")
                    book_item.setText(5, getattr(book, "narrators", "") or "")
                    book_item.setText(6, getattr(book, "isbn", "") or "")
                    book_item.setText(7, getattr(book, "asin", "") or "")
                    book_item.setText(8, book.filename or "")

                    book_item.setData(0, Qt.ItemDataRole.UserRole, book)
                    self.book_item_map[book.path] = book_item

        self.tree.setSortingEnabled(True)

    def on_item_click(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, Audiobook):
            # Toggle selection
            if item in self.selected_books:
                self.selected_books.remove(item)
                font = item.font(0)
                font.setBold(False)
                item.setFont(0, font)
            else:
                self.selected_books.append(item)
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
            self.selected_count_label.setText(f"Selected books: {len(self.selected_books)}")
            self.update_preview(data)

    def update_preview(self, book: Audiobook):
        self.preview_labels["Title"].setText(book.title or "")
        self.preview_labels["Series"].setText(book.series or "")
        self.preview_labels["Index"].setText(str(book.series_index) if book.series_index else "")
        self.preview_labels["Author"].setText(book.author or "")
        self.preview_labels["Year"].setText(str(book.year) if getattr(book, "year", None) else "")
        self.preview_labels["Narrators"].setText(getattr(book, "narrators", "") or "")
        self.preview_labels["ISBN"].setText(getattr(book, "isbn", "") or "")
        self.preview_labels["ASIN"].setText(getattr(book, "asin", "") or "")
        self.preview_labels["Filename"].setText(book.filename or "")

    def open_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu()

        if isinstance(data, Audiobook):
            action = QAction(f"Sync Tags for: {data.title}", self)
            action.triggered.connect(lambda: self.prepare_tag_sync(item, "BOOK"))
            menu.addAction(action)
        elif data == "SERIES":
            action = QAction(f"Sync Tags for Series: {item.text(0)}", self)
            action.triggered.connect(lambda: self.prepare_tag_sync(item, "SERIES"))
            menu.addAction(action)
        elif data == "AUTHOR":
            action = QAction(f"Sync Tags for Author: {item.text(0)}", self)
            action.triggered.connect(lambda: self.prepare_tag_sync(item, "AUTHOR"))
            menu.addAction(action)

        if not menu.isEmpty():
            menu.exec(self.tree.viewport().mapToGlobal(position))

    def prepare_tag_sync(self, tree_item: QTreeWidgetItem, mode: str):
        books_payload = []

        def collect_books(item: QTreeWidgetItem):
            for i in range(item.childCount()):
                child = item.child(i)
                d = child.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(d, Audiobook):
                    if mode == "BOOK":
                        books_payload.append((d, d.series, d.series_index))
                    elif mode == "SERIES":
                        s_name = tree_item.text(0)
                        books_payload.append((d, s_name, d.series_index))
                    elif mode == "AUTHOR":
                        s_name = child.parent().text(0) if child.parent() else d.series
                        books_payload.append((d, s_name, d.series_index))
                else:
                    collect_books(child)

        collect_books(tree_item)

        if not books_payload:
            return

        from PyQt6.QtWidgets import QMessageBox
        confirm = QMessageBox.question(self, "Confirm Update",
                                       f"Update tags for {len(books_payload)} files?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.run_tag_worker(books_payload)

    def run_tag_worker(self, payload):
        self.progress_bar.setVisible(True)
        self.btn_select.setEnabled(False)
        self.tag_worker = TagWorker(payload)
        self.tag_worker.progress_update.connect(self.progress_bar.setValue)
        self.tag_worker.status_update.connect(self.status_bar.showMessage)
        self.tag_worker.item_updated.connect(self.on_item_tagged)
        self.tag_worker.finished.connect(self.on_tagging_finished)
        self.tag_worker.start()

    def on_item_tagged(self, book_obj, success):
        if book_obj.path in self.book_item_map:
            item = self.book_item_map[book_obj.path]
            if success:
                item.setText(2, "TAG UPDATED")
                item.setForeground(2, QBrush(QColor("#a3be8c")))
            else:
                item.setText(2, "FAILED")
                item.setForeground(2, QBrush(QColor("#bf616a")))

    def on_tagging_finished(self):
        self.progress_bar.setVisible(False)
        self.btn_select.setEnabled(True)
        self.status_bar.showMessage("Tagging complete.")
        self.tag_worker = None

    def apply_bulk_tags(self):
        if not self.selected_books:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Selection", "No books selected to apply tags.")
            return

        books_payload = []
        for item in self.selected_books:
            book = item.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(book, Audiobook):
                books_payload.append((book, book.series, book.series_index))

        self.run_tag_worker(books_payload)