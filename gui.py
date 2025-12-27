from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QLabel, QHeaderView, QMenu,
    QMessageBox, QProgressBar, QApplication, QStyle
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor, QBrush, QAction, QFont, QIcon

from models import Audiobook
from workers import ScanWorker, TagWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audiobook Metadata Manager")
        self.resize(1150, 750)

        self.settings = QSettings("AudiobookManager", "MainApp")

        self.library_data = {}
        self.scan_worker = None
        self.tag_worker = None
        self.book_item_map = {}

        self._apply_gtk_theme()
        self._init_ui()

    def _apply_gtk_theme(self):
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
                selection-background-color: #3584e4;
                selection-color: #ffffff;
            }
            QTreeWidget::item { padding: 4px; border-bottom: 1px solid #282828; }
            QTreeWidget::item:selected { background-color: #3584e4; }
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
        """)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Top Bar
        top_bar = QWidget()
        top_layout = QVBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_select = QPushButton("Select Library Folder")
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.clicked.connect(self.select_folder)
        top_layout.addWidget(self.btn_select)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        top_layout.addWidget(self.progress_bar)

        layout.addWidget(top_bar)

        # Tree View (4 Columns now)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Hierarchy / Title", "Index", "Source", "Filename"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)

        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        # Filename (3) stretches/resizes interactively

        layout.addWidget(self.tree)

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

        icon_author = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        icon_series = self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        icon_book = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)

        sorted_authors = sorted(self.library_data.keys())

        for author in sorted_authors:
            author_item = QTreeWidgetItem(self.tree)
            author_item.setText(0, author)
            author_item.setIcon(0, icon_author)
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
                series_item.setIcon(0, icon_series)
                series_item.setData(0, Qt.ItemDataRole.UserRole, "SERIES")
                series_item.setForeground(0, QBrush(QColor("#88c0d0")))

                books = series_dict[series]
                books.sort(key=lambda b: (float(b.series_index) if b.series_index else float('inf'), b.title))

                for book in books:
                    book_item = QTreeWidgetItem(series_item)
                    book_item.setText(0, book.title)
                    book_item.setIcon(0, icon_book)

                    book_item.setText(1, str(book.series_index) if book.series_index else "-")
                    book_item.setText(2, book.source)
                    book_item.setText(3, book.filename)
                    book_item.setData(0, Qt.ItemDataRole.UserRole, book)

                    self.book_item_map[book.path] = book_item

        self.tree.setSortingEnabled(True)

    def open_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item: return

        data = item.data(0, Qt.ItemDataRole.UserRole)

        menu = QMenu()
        if data == "SERIES":
            name = item.text(0)
            action = QAction(f"Sync Tags for Series: {name}", self)
            action.triggered.connect(lambda: self.prepare_tag_sync(item, "SERIES"))
            menu.addAction(action)
        elif data == "AUTHOR":
            name = item.text(0)
            action = QAction(f"Sync Tags for Author: {name}", self)
            action.triggered.connect(lambda: self.prepare_tag_sync(item, "AUTHOR"))
            menu.addAction(action)

        if not menu.isEmpty():
            menu.exec(self.tree.viewport().mapToGlobal(position))

    def prepare_tag_sync(self, tree_item, mode):
        books_payload = []

        def collect_books(item):
            for i in range(item.childCount()):
                child = item.child(i)
                d = child.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(d, Audiobook):
                    s_name = tree_item.text(0) if mode == "SERIES" else child.parent().text(0)
                    books_payload.append((d, s_name, d.series_index))
                else:
                    collect_books(child)

        collect_books(tree_item)

        if not books_payload: return

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