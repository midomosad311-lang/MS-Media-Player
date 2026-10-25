"""
Playlist Widget - Playlist display and management
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMenu, QFileDialog, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from media.playlist_manager import PlaylistManager
from accessibility.accessibility_manager import AccessibilityManager


class PlaylistWidget(QWidget):
    """Playlist widget"""

    def __init__(self, playlist_manager: PlaylistManager, accessibility_manager: AccessibilityManager):
        super().__init__()
        self.playlist_manager = playlist_manager
        self.accessibility = accessibility_manager
        self.setMaximumHeight(200)
        self.setMinimumHeight(150)

        self._setup_ui()
        self._connect_signals()
        self._apply_accessibility()

    def _setup_ui(self):
        """Setup playlist UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        header_layout = QHBoxLayout()

        self.title_label = QLabel(self.tr("Playlist"))
        self.title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Buttons
        self.add_btn = QPushButton("➕")
        self.add_btn.setToolTip(self.tr("Add files"))
        self.add_btn.setFixedSize(28, 28)
        self.add_btn.clicked.connect(self._add_files)
        self.accessibility.setup_widget_accessibility(self.add_btn, self.tr("Add Files"), self.tr("Add media files to playlist"))
        header_layout.addWidget(self.add_btn)

        self.add_url_btn = QPushButton("🔗")
        self.add_url_btn.setToolTip(self.tr("Add URL"))
        self.add_url_btn.setFixedSize(28, 28)
        self.add_url_btn.clicked.connect(self._add_url)
        self.accessibility.setup_widget_accessibility(self.add_url_btn, self.tr("Add URL"), self.tr("Add network stream"))
        header_layout.addWidget(self.add_url_btn)

        self.remove_btn = QPushButton("🗑")
        self.remove_btn.setToolTip(self.tr("Remove selected"))
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.clicked.connect(self._remove_selected)
        self.accessibility.setup_widget_accessibility(self.remove_btn, self.tr("Remove"), self.tr("Remove selected items"))
        header_layout.addWidget(self.remove_btn)

        self.clear_btn = QPushButton("✕")
        self.clear_btn.setToolTip(self.tr("Clear playlist"))
        self.clear_btn.setFixedSize(28, 28)
        self.clear_btn.clicked.connect(self._clear_playlist)
        self.accessibility.setup_widget_accessibility(self.clear_btn, self.tr("Clear"), self.tr("Clear entire playlist"))
        header_layout.addWidget(self.clear_btn)

        self.save_btn = QPushButton("💾")
        self.save_btn.setToolTip(self.tr("Save playlist"))
        self.save_btn.setFixedSize(28, 28)
        self.save_btn.clicked.connect(self._save_playlist)
        self.accessibility.setup_widget_accessibility(self.save_btn, self.tr("Save"), self.tr("Save playlist as M3U"))
        header_layout.addWidget(self.save_btn)

        self.load_btn = QPushButton("📂")
        self.load_btn.setToolTip(self.tr("Load playlist"))
        self.load_btn.setFixedSize(28, 28)
        self.load_btn.clicked.connect(self._load_playlist)
        self.accessibility.setup_widget_accessibility(self.load_btn, self.tr("Load"), self.tr("Load M3U playlist"))
        header_layout.addWidget(self.load_btn)

        layout.addLayout(header_layout)

        # Playlist view
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.currentRowChanged.connect(self._on_current_row_changed)
        self.accessibility.setup_widget_accessibility(
            self.list_widget, self.tr("Playlist Items"), self.tr("List of media files in playlist")
        )
        layout.addWidget(self.list_widget)

        # Status
        self.status_label = QLabel(self.tr("0 items"))
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _connect_signals(self):
        """Connect signals"""
        if self.playlist_manager:
            self.playlist_manager.playlist_changed.connect(self.update_playlist)
            self.playlist_manager.current_index_changed.connect(self._on_current_index_changed)

    def _apply_accessibility(self):
        """Apply accessibility settings"""
        pass

    def update_playlist(self):
        """Update playlist display"""
        self.list_widget.clear()
        items = self.playlist_manager.get_items()
        for index, item in enumerate(items, start=1):
            # Number every entry sequentially (1, 2, 3, ...) so the queue is
            # easy to follow with a screen reader and matches the position that
            # Next / Previous move through.
            list_item = QListWidgetItem(f"{index}. {item['name']}")
            list_item.setData(Qt.UserRole, item["path"])
            list_item.setToolTip(item["path"])
            self.list_widget.addItem(list_item)

        # Show which folder this automatic (default) playlist came from.
        folder = self._folder_name()
        if folder:
            self.title_label.setText(self.tr("Default playlist: {0}").format(folder))
        else:
            self.title_label.setText(self.tr("Playlist"))

        # Highlight current item
        current = self.playlist_manager.current_index
        if 0 <= current < self.list_widget.count():
            self.list_widget.setCurrentRow(current)

        self._update_status()

    def _folder_name(self) -> str:
        """Return the folder that seeded the default playlist, if any."""
        try:
            return self.playlist_manager.get_folder_name() or ""
        except Exception:
            return ""

    def _update_status(self):
        """Update status label"""
        count = self.playlist_manager.get_count()
        current = self.playlist_manager.current_index
        folder = self._folder_name()
        if count > 0:
            if folder:
                self.status_label.setText(
                    self.tr("Default playlist: {0} - {1} items - Current: {2}").format(
                        folder, count, current + 1
                    )
                )
            else:
                self.status_label.setText(self.tr("{0} items - Current: {1}").format(count, current + 1))
        else:
            self.status_label.setText(self.tr("0 items"))

    def set_current_index(self, index: int):
        """Set current item"""
        if 0 <= index < self.list_widget.count():
            self.list_widget.setCurrentRow(index)
            self.list_widget.scrollToItem(self.list_widget.item(index))

    def _on_current_index_changed(self, index: int):
        """Handle current index change from manager"""
        self.set_current_index(index)
        self._update_status()

    def _on_current_row_changed(self, row: int):
        """Handle current row change from UI"""
        if row >= 0:
            self.playlist_manager.set_current_index(row)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle item double click"""
        index = self.list_widget.row(item)
        self.playlist_manager.set_current_index(index)

    def _show_context_menu(self, position):
        """Show context menu"""
        menu = QMenu(self)

        play_action = menu.addAction(self.tr("Play"))
        play_action.triggered.connect(self._play_selected)

        menu.addSeparator()

        remove_action = menu.addAction(self.tr("Remove"))
        remove_action.triggered.connect(self._remove_selected)

        move_up_action = menu.addAction(self.tr("Move Up"))
        move_up_action.triggered.connect(lambda: self._move_selected(-1))

        move_down_action = menu.addAction(self.tr("Move Down"))
        move_down_action.triggered.connect(lambda: self._move_selected(1))

        menu.addSeparator()

        sort_action = menu.addAction(self.tr("Sort by Name"))
        sort_action.triggered.connect(lambda: self.playlist_manager.sort_by_name())

        menu.exec(QCursor.pos())

    def _play_selected(self):
        """Play selected item"""
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            self.playlist_manager.set_current_index(current_row)

    def _add_files(self):
        """Add files to playlist"""
        files, _ = QFileDialog.getOpenFileNames(
            self, self.tr("Add Media Files"), "",
            self.tr("Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.flac *.ogg *.m4a *.wma *.3gp *.webm *.ts *.m3u *.m3u8);;All Files (*.*)")
        )
        if files:
            self.playlist_manager.add_files(files)

    def _add_url(self):
        """Add URL to playlist"""
        url, ok = QInputDialog.getText(self, self.tr("Add URL"), self.tr("Enter media URL:"))
        if ok and url:
            self.playlist_manager.add_file(url)

    def _remove_selected(self):
        """Remove selected items"""
        selected = self.list_widget.selectedItems()
        if not selected:
            return

        # Remove in reverse order to maintain indices
        rows = sorted([self.list_widget.row(item) for item in selected], reverse=True)
        for row in rows:
            self.playlist_manager.remove_file(row)

    def _clear_playlist(self):
        """Clear playlist"""
        if self.playlist_manager.get_count() > 0:
            reply = QMessageBox.question(
                self, self.tr("Clear Playlist"),
                self.tr("Are you sure you want to clear the playlist?"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.playlist_manager.clear()

    def _save_playlist(self):
        """Save playlist as M3U"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Playlist"), "", self.tr("M3U Playlist (*.m3u);;All Files (*.*)")
        )
        if file_path:
            if not file_path.endswith('.m3u'):
                file_path += '.m3u'
            if self.playlist_manager.save_m3u(file_path):
                self.accessibility.announce(self.tr("Playlist saved"))
            else:
                self.accessibility.announce(self.tr("Failed to save playlist"))

    def _load_playlist(self):
        """Load M3U playlist"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Load Playlist"), "", self.tr("M3U Playlist (*.m3u *.m3u8);;All Files (*.*)")
        )
        if file_path:
            if self.playlist_manager.load_m3u(file_path):
                self.accessibility.announce(self.tr("Playlist loaded"))
            else:
                self.accessibility.announce(self.tr("Failed to load playlist"))

    def _move_selected(self, direction: int):
        """Move selected items up/down"""
        selected = self.list_widget.selectedItems()
        if not selected:
            return

        rows = sorted([self.list_widget.row(item) for item in selected])
        if direction < 0:
            # Move up
            for row in rows:
                if row > 0:
                    self.playlist_manager.move_item(row, row - 1)
        else:
            # Move down - process in reverse
            for row in reversed(rows):
                if row < self.playlist_manager.get_count() - 1:
                    self.playlist_manager.move_item(row, row + 1)

    def retranslate(self):
        """Retranslate UI"""
        self.title_label.setText(self.tr("Playlist"))
        self.add_btn.setToolTip(self.tr("Add files"))
        self.add_url_btn.setToolTip(self.tr("Add URL"))
        self.remove_btn.setToolTip(self.tr("Remove selected"))
        self.clear_btn.setToolTip(self.tr("Clear playlist"))
        self.save_btn.setToolTip(self.tr("Save playlist"))
        self.load_btn.setToolTip(self.tr("Load playlist"))
        self._update_status()