"""
Bookmark Dialog - UI for managing bookmarks
"""

from typing import List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from media.bookmark_manager import BookmarkManager, Bookmark
from accessibility.accessibility_manager import AccessibilityManager


class BookmarkDialog(QDialog):
    """Dialog for managing bookmarks"""

    bookmark_selected = Signal(float)  # position in seconds

    def __init__(self, bookmark_manager: BookmarkManager, file_path: str,
                 accessibility: AccessibilityManager, parent=None):
        super().__init__(parent)
        self.bookmark_manager = bookmark_manager
        self.file_path = file_path
        self.accessibility = accessibility
        self._bookmarks: List[Bookmark] = []

        self.setWindowTitle(self.tr("Bookmarks"))
        self.resize(400, 500)
        self.setMinimumSize(350, 400)

        self._setup_ui()
        self._load_bookmarks()
        self._apply_accessibility()

    def _setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel(self.tr("Bookmarks"))
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.add_btn = QPushButton(self.tr("Add Bookmark"))
        self.add_btn.setMinimumHeight(36)
        self.add_btn.clicked.connect(self._on_add_bookmark)
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        # Bookmarks list
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget, 1)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.goto_btn = QPushButton(self.tr("Go To"))
        self.goto_btn.setEnabled(False)
        self.goto_btn.clicked.connect(self._on_goto)
        buttons_layout.addWidget(self.goto_btn)

        self.rename_btn = QPushButton(self.tr("Rename"))
        self.rename_btn.setEnabled(False)
        self.rename_btn.clicked.connect(self._on_rename)
        buttons_layout.addWidget(self.rename_btn)

        self.delete_btn = QPushButton(self.tr("Delete"))
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._on_delete)
        buttons_layout.addWidget(self.delete_btn)

        buttons_layout.addStretch()

        self.close_btn = QPushButton(self.tr("Close"))
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)

        layout.addLayout(buttons_layout)

    def _apply_accessibility(self):
        """Apply accessibility settings"""
        self.accessibility.setup_widget_accessibility(
            self.list_widget, self.tr("Bookmarks List"), self.tr("List of saved bookmarks")
        )
        self.accessibility.setup_widget_accessibility(
            self.add_btn, self.tr("Add Bookmark"), self.tr("Add a new bookmark at current position")
        )
        self.accessibility.setup_widget_accessibility(
            self.goto_btn, self.tr("Go To"), self.tr("Jump to selected bookmark")
        )
        self.accessibility.setup_widget_accessibility(
            self.rename_btn, self.tr("Rename"), self.tr("Rename selected bookmark")
        )
        self.accessibility.setup_widget_accessibility(
            self.delete_btn, self.tr("Delete"), self.tr("Delete selected bookmark")
        )
        self.accessibility.setup_widget_accessibility(
            self.close_btn, self.tr("Close"), self.tr("Close dialog")
        )

    def _load_bookmarks(self):
        """Load and display bookmarks"""
        self.list_widget.clear()
        self._bookmarks = self.bookmark_manager.get_bookmarks(self.file_path)

        if not self._bookmarks:
            # Show empty state
            item = QListWidgetItem(self.tr("No bookmarks yet. Click 'Add Bookmark' to create one."))
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.list_widget.addItem(item)
            self.title_label.setText(self.tr("Bookmarks"))
            self.add_btn.setText(self.tr("Add Bookmark"))
        else:
            self.title_label.setText(self.tr("Bookmarks"))
            self.add_btn.setText(self.tr("Add Bookmark"))
            for bookmark in self._bookmarks:
                self._add_bookmark_item(bookmark)

    def _add_bookmark_item(self, bookmark: Bookmark):
        """Add bookmark to list widget"""
        hours = int(bookmark.position // 3600)
        minutes = int((bookmark.position % 3600) // 60)
        seconds = int(bookmark.position % 60)
        if hours > 0:
            time_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes}:{seconds:02d}"

        item = QListWidgetItem(f"{bookmark.name}  [{time_str}]")
        item.setData(Qt.UserRole, bookmark.position)
        self.list_widget.addItem(item)

    def _on_add_bookmark(self):
        """Handle add bookmark"""
        from ui.windows.main_window import MainWindow
        window = self.window()
        current_position = 0.0
        if isinstance(window, MainWindow) and window.media_engine:
            current_position = window.media_engine.get_time()

        n = len(self.bookmark_manager.get_bookmarks(self.file_path)) + 1
        default_name = self.tr("Bookmark {0}").format(n)

        name, ok = QInputDialog.getText(
            self,
            self.tr("Add Bookmark"),
            self.tr("Bookmark name:"),
            text=default_name
        )

        if ok and name.strip():
            bookmark = self.bookmark_manager.add_bookmark(
                self.file_path, current_position, name.strip()
            )
            self._load_bookmarks()
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.data(Qt.UserRole) == bookmark.position:
                    self.list_widget.setCurrentRow(i)
                    break
            self.accessibility.announce(self.tr("Bookmark '{0}' added").format(bookmark.name))

    def _on_item_double_clicked(self, item: QListWidgetItem):
        position = item.data(Qt.UserRole)
        if position is not None:
            self.bookmark_selected.emit(position)
            self.accept()

    def _on_selection_changed(self):
        has_selection = len(self.list_widget.selectedItems()) > 0
        is_real_bookmark = has_selection and self.list_widget.currentItem().data(Qt.UserRole) is not None
        self.goto_btn.setEnabled(is_real_bookmark)
        self.rename_btn.setEnabled(is_real_bookmark)
        self.delete_btn.setEnabled(is_real_bookmark)

    def _on_goto(self):
        item = self.list_widget.currentItem()
        if item:
            position = item.data(Qt.UserRole)
            if position is not None:
                self.bookmark_selected.emit(position)
                self.accept()

    def _on_rename(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        position = item.data(Qt.UserRole)
        if position is None:
            return
        current_name = item.text().split("  [")[0]
        new_name, ok = QInputDialog.getText(
            self,
            self.tr("Rename Bookmark"),
            self.tr("New name:"),
            text=current_name
        )
        if ok and new_name.strip():
            for i, bookmark in enumerate(self._bookmarks):
                if bookmark.position == position:
                    self.bookmark_manager.update_bookmark(self.file_path, i, name=new_name.strip())
                    self._load_bookmarks()
                    self.accessibility.announce(self.tr("Bookmark renamed to '{0}'").format(new_name.strip()))
                    break

    def _on_delete(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        position = item.data(Qt.UserRole)
        if position is None:
            return
        name = item.text().split("  [")[0]
        reply = QMessageBox.question(
            self,
            self.tr("Delete Bookmark"),
            self.tr("Delete bookmark '{0}'?").format(name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for i, bookmark in enumerate(self._bookmarks):
                if bookmark.position == position:
                    self.bookmark_manager.remove_bookmark(self.file_path, i)
                    self._load_bookmarks()
                    self.accessibility.announce(self.tr("Bookmark '{0}' deleted").format(name))
                    break

    def retranslate(self):
        """Retranslate UI"""
        self.setWindowTitle(self.tr("Bookmarks"))
        self.title_label.setText(self.tr("Bookmarks"))
        self.add_btn.setText(self.tr("Add Bookmark"))
        self.goto_btn.setText(self.tr("Go To"))
        self.rename_btn.setText(self.tr("Rename"))
        self.delete_btn.setText(self.tr("Delete"))
        self.close_btn.setText(self.tr("Close"))
        self._load_bookmarks()
