"""
Playlist Manager Dialog - Advanced playlist management
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMenu, QFileDialog, QMessageBox, QInputDialog,
    QDialogButtonBox, QSplitter, QWidget, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from media.playlist_manager import PlaylistManager


class PlaylistManagerDialog(QDialog):
    """Playlist manager dialog"""

    def __init__(self, playlist_manager: PlaylistManager, parent=None):
        super().__init__(parent)
        self.playlist_manager = playlist_manager
        self.setWindowTitle(self.tr("Playlist Manager"))
        self.resize(820, 520)
        self.setModal(True)

        self._setup_ui()
        self._update_playlist()
        self._update_named_list()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)

        # Splitter for dual playlist view
        splitter = QSplitter(Qt.Horizontal)

        # Current playlist
        current_widget = QWidget()
        current_layout = QVBoxLayout(current_widget)

        current_layout.addWidget(QLabel(self.tr("Current Playlist")))

        self.current_list = QListWidget()
        self.current_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.current_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.current_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.current_list.customContextMenuRequested.connect(self._show_current_context_menu)
        self.current_list.itemDoubleClicked.connect(self._play_current_item)
        current_layout.addWidget(self.current_list)

        # Current playlist buttons
        current_btn_layout = QHBoxLayout()
        self.add_files_btn = QPushButton(self.tr("Add Files"))
        self.add_files_btn.clicked.connect(self._add_files)
        current_btn_layout.addWidget(self.add_files_btn)

        self.add_url_btn = QPushButton(self.tr("Add URL"))
        self.add_url_btn.clicked.connect(self._add_url)
        current_btn_layout.addWidget(self.add_url_btn)

        self.remove_btn = QPushButton(self.tr("Remove"))
        self.remove_btn.clicked.connect(self._remove_current)
        current_btn_layout.addWidget(self.remove_btn)

        self.clear_btn = QPushButton(self.tr("Clear"))
        self.clear_btn.clicked.connect(self._clear_current)
        current_btn_layout.addWidget(self.clear_btn)

        current_layout.addLayout(current_btn_layout)
        splitter.addWidget(current_widget)

        # Custom (named) playlists - independent groupings of files that may
        # come from many different folders.
        saved_widget = QWidget()
        saved_layout = QVBoxLayout(saved_widget)

        saved_layout.addWidget(QLabel(self.tr("Custom Playlists")))

        self.named_list = QListWidget()
        self.named_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.named_list.customContextMenuRequested.connect(self._show_saved_context_menu)
        self.named_list.itemDoubleClicked.connect(self._load_named_playlist_item)
        saved_layout.addWidget(self.named_list)

        # First row of buttons: create/save/rename/delete named playlists
        named_btn_layout = QHBoxLayout()
        self.new_named_btn = QPushButton(self.tr("New..."))
        self.new_named_btn.clicked.connect(self._new_named_playlist)
        named_btn_layout.addWidget(self.new_named_btn)

        self.save_named_btn = QPushButton(self.tr("Save Current As..."))
        self.save_named_btn.clicked.connect(self._save_current_as_named)
        named_btn_layout.addWidget(self.save_named_btn)

        self.rename_named_btn = QPushButton(self.tr("Rename..."))
        self.rename_named_btn.clicked.connect(self._rename_named_playlist)
        named_btn_layout.addWidget(self.rename_named_btn)

        self.delete_named_btn = QPushButton(self.tr("Delete"))
        self.delete_named_btn.clicked.connect(self._delete_named_playlist)
        named_btn_layout.addWidget(self.delete_named_btn)
        saved_layout.addLayout(named_btn_layout)

        # Second row: manage the contents of the selected named playlist
        contents_btn_layout = QHBoxLayout()
        self.add_to_named_btn = QPushButton(self.tr("Add Files..."))
        self.add_to_named_btn.clicked.connect(self._add_files_to_named_playlist)
        contents_btn_layout.addWidget(self.add_to_named_btn)

        self.remove_from_named_btn = QPushButton(self.tr("Remove Item"))
        self.remove_from_named_btn.clicked.connect(self._remove_from_named_playlist)
        contents_btn_layout.addWidget(self.remove_from_named_btn)

        self.load_named_btn = QPushButton(self.tr("Load Into Player"))
        self.load_named_btn.clicked.connect(self._load_named_playlist)
        contents_btn_layout.addWidget(self.load_named_btn)
        saved_layout.addLayout(contents_btn_layout)

        # Contents of the selected named playlist
        saved_layout.addWidget(QLabel(self.tr("Playlist Contents")))
        self.named_items_list = QListWidget()
        self.named_items_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        saved_layout.addWidget(self.named_items_list)

        self.named_list.currentRowChanged.connect(self._update_named_items)

        # Backwards-compatible alias used by older callers/tests.
        self.saved_list = self.named_list

        splitter.addWidget(saved_widget)

        splitter.setSizes([400, 300])
        layout.addWidget(splitter)

        # Sort buttons
        sort_layout = QHBoxLayout()
        self.sort_name_btn = QPushButton(self.tr("Sort by Name"))
        self.sort_name_btn.clicked.connect(lambda: self.playlist_manager.sort_by_name())
        sort_layout.addWidget(self.sort_name_btn)

        self.sort_path_btn = QPushButton(self.tr("Sort by Path"))
        self.sort_path_btn.clicked.connect(lambda: self.playlist_manager.sort_by_path())
        sort_layout.addWidget(self.sort_path_btn)

        self.shuffle_btn = QPushButton(self.tr("Shuffle"))
        self.shuffle_btn.setCheckable(True)
        self.shuffle_btn.setChecked(self.playlist_manager.get_shuffle())
        self.shuffle_btn.toggled.connect(self.playlist_manager.set_shuffle)
        sort_layout.addWidget(self.shuffle_btn)

        self.repeat_btn = QPushButton(self.tr("Repeat"))
        self.repeat_btn.setCheckable(True)
        self.repeat_btn.clicked.connect(self._cycle_repeat)
        sort_layout.addWidget(self.repeat_btn)

        layout.addLayout(sort_layout)

        # Status
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)

    def _update_playlist(self):
        """Update current playlist display"""
        self.current_list.clear()
        items = self.playlist_manager.get_items()
        for i, item in enumerate(items):
            list_item = QListWidgetItem(f"{i+1}. {item['name']}")
            list_item.setData(Qt.UserRole, item['path'])
            list_item.setToolTip(item['path'])
            self.current_list.addItem(list_item)

        # Highlight current
        current = self.playlist_manager.current_index
        if 0 <= current < self.current_list.count():
            self.current_list.setCurrentRow(current)

        self._update_status()

    def _update_status(self):
        """Update status label"""
        count = self.playlist_manager.get_count()
        current = self.playlist_manager.current_index
        repeat = self.playlist_manager.get_repeat_mode().value
        shuffle = self.tr("On") if self.playlist_manager.get_shuffle() else self.tr("Off")
        self.status_label.setText(
            self.tr("Items: {0} | Current: {1} | Repeat: {2} | Shuffle: {3}").format(
                count, current + 1 if current >= 0 else self.tr("None"), repeat, shuffle
            )
        )

    def _show_current_context_menu(self, position):
        """Show context menu for current playlist"""
        menu = QMenu(self)

        play_action = menu.addAction(self.tr("Play"))
        play_action.triggered.connect(self._play_current_item)

        menu.addSeparator()

        remove_action = menu.addAction(self.tr("Remove"))
        remove_action.triggered.connect(self._remove_current)

        move_up_action = menu.addAction(self.tr("Move Up"))
        move_up_action.triggered.connect(lambda: self._move_current(-1))

        move_down_action = menu.addAction(self.tr("Move Down"))
        move_down_action.triggered.connect(lambda: self._move_current(1))

        menu.addSeparator()

        sort_action = menu.addAction(self.tr("Sort by Name"))
        sort_action.triggered.connect(lambda: self.playlist_manager.sort_by_name())

        menu.exec(QCursor.pos())

    def _show_saved_context_menu(self, position):
        """Show context menu for custom (named) playlists"""
        menu = QMenu(self)

        load_action = menu.addAction(self.tr("Load Into Player"))
        load_action.triggered.connect(self._load_named_playlist)

        add_action = menu.addAction(self.tr("Add Files..."))
        add_action.triggered.connect(self._add_files_to_named_playlist)

        rename_action = menu.addAction(self.tr("Rename..."))
        rename_action.triggered.connect(self._rename_named_playlist)

        delete_action = menu.addAction(self.tr("Delete"))
        delete_action.triggered.connect(self._delete_named_playlist)

        menu.exec(QCursor.pos())

    def _play_current_item(self, item=None):
        """Play selected/current item"""
        if item is None:
            item = self.current_list.currentItem()
        if item:
            row = self.current_list.row(item)
            self.playlist_manager.set_current_index(row)

    def _add_files(self):
        """Add files to playlist"""
        files, _ = QFileDialog.getOpenFileNames(
            self, self.tr("Add Media Files"), "",
            self.tr("Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.flac *.ogg *.m4a *.wma *.3gp *.webm *.ts *.m3u *.m3u8);;All Files (*.*)")
        )
        if files:
            self.playlist_manager.add_files(files)
            self._update_playlist()

    def _add_url(self):
        """Add URL to playlist"""
        url, ok = QInputDialog.getText(self, self.tr("Add URL"), self.tr("Enter media URL:"))
        if ok and url:
            self.playlist_manager.add_file(url)
            self._update_playlist()

    def _remove_current(self):
        """Remove selected items from current playlist"""
        selected = self.current_list.selectedItems()
        if not selected:
            return

        rows = sorted([self.current_list.row(item) for item in selected], reverse=True)
        for row in rows:
            self.playlist_manager.remove_file(row)
        self._update_playlist()

    def _clear_current(self):
        """Clear current playlist"""
        if self.playlist_manager.get_count() > 0:
            reply = QMessageBox.question(
                self, self.tr("Clear Playlist"),
                self.tr("Are you sure you want to clear the playlist?"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.playlist_manager.clear()
                self._update_playlist()

    def _move_current(self, direction: int):
        """Move selected items"""
        selected = self.current_list.selectedItems()
        if not selected:
            return

        rows = sorted([self.current_list.row(item) for item in selected])
        if direction < 0:
            for row in rows:
                if row > 0:
                    self.playlist_manager.move_item(row, row - 1)
        else:
            for row in reversed(rows):
                if row < self.playlist_manager.get_count() - 1:
                    self.playlist_manager.move_item(row, row + 1)
        self._update_playlist()

    # ------------------------------------------------------------------
    # Custom (named) playlists
    # ------------------------------------------------------------------
    def _update_named_list(self):
        """Refresh the list of custom playlists."""
        self.named_list.blockSignals(True)
        selected = self._selected_named_name()
        self.named_list.clear()
        names = self.playlist_manager.get_named_playlists()
        for name in names:
            count = self.playlist_manager.get_named_playlist_count(name)
            item = QListWidgetItem(self.tr("{0} ({1} items)").format(name, count))
            item.setData(Qt.UserRole, name)
            self.named_list.addItem(item)
        # Restore selection when possible, otherwise select the first entry.
        restored = False
        for i in range(self.named_list.count()):
            if self.named_list.item(i).data(Qt.UserRole) == selected:
                self.named_list.setCurrentRow(i)
                restored = True
                break
        if not restored and self.named_list.count() > 0:
            self.named_list.setCurrentRow(0)
        self.named_list.blockSignals(False)
        self._update_named_items()

    def _selected_named_name(self) -> str:
        """Return the name of the selected custom playlist (or '')."""
        item = self.named_list.currentItem()
        return item.data(Qt.UserRole) if item else ""

    def _update_named_items(self, *args):
        """Show the items of the selected custom playlist."""
        self.named_items_list.clear()
        name = self._selected_named_name()
        if not name:
            return
        for entry in self.playlist_manager.get_named_playlist_items(name):
            item = QListWidgetItem(entry["name"])
            item.setData(Qt.UserRole, entry["path"])
            item.setToolTip(entry["path"])
            self.named_items_list.addItem(item)

    def _new_named_playlist(self):
        """Create a new, empty custom playlist."""
        name, ok = QInputDialog.getText(
            self, self.tr("New Custom Playlist"), self.tr("Enter playlist name:")
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        if not self.playlist_manager.create_named_playlist(name):
            QMessageBox.warning(
                self, self.tr("New Custom Playlist"),
                self.tr("A playlist named '{0}' already exists.").format(name)
            )
            return
        self._update_named_list()
        self._select_named(name)

    def _select_named(self, name: str):
        for i in range(self.named_list.count()):
            if self.named_list.item(i).data(Qt.UserRole) == name:
                self.named_list.setCurrentRow(i)
                return

    def _save_current_as_named(self):
        """Save the current queue as a new custom playlist."""
        name, ok = QInputDialog.getText(
            self, self.tr("Save Current As..."), self.tr("Enter playlist name:")
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        existed = self.playlist_manager.has_named_playlist(name)
        if existed:
            reply = QMessageBox.question(
                self, self.tr("Save Current As..."),
                self.tr("A playlist named '{0}' already exists. Replace its contents?").format(name),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        self.playlist_manager.save_to_named_playlist(name, replace=True)
        self._update_named_list()
        self._select_named(name)

    def _add_files_to_named_playlist(self):
        """Add files (from any folder) to the selected custom playlist."""
        name = self._selected_named_name()
        if not name:
            QMessageBox.information(
                self, self.tr("Add Files"),
                self.tr("Select or create a custom playlist first.")
            )
            return
        files, _ = QFileDialog.getOpenFileNames(
            self, self.tr("Add Media Files"), "",
            self.tr("Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.flac *.ogg *.m4a *.wma *.3gp *.webm *.ts *.m3u *.m3u8);;All Files (*.*)")
        )
        if files:
            self.playlist_manager.add_files_to_named_playlist(name, files)
            self._update_named_list()
            self._select_named(name)

    def _remove_from_named_playlist(self):
        """Remove the selected item(s) from the selected custom playlist."""
        name = self._selected_named_name()
        if not name:
            return
        selected = self.named_items_list.selectedItems()
        if not selected:
            return
        rows = sorted([self.named_items_list.row(it) for it in selected], reverse=True)
        for row in rows:
            self.playlist_manager.remove_from_named_playlist(name, row)
        self._update_named_list()
        self._select_named(name)

    def _load_named_playlist(self):
        """Load the selected custom playlist into the active player queue."""
        name = self._selected_named_name()
        if not name:
            return
        if self.playlist_manager.load_named_playlist(name, replace=True):
            self._update_playlist()

    def _load_named_playlist_item(self, item):
        """Load a custom playlist on double click."""
        name = item.data(Qt.UserRole)
        if name and self.playlist_manager.load_named_playlist(name, replace=True):
            self._update_playlist()

    def _rename_named_playlist(self):
        """Rename the selected custom playlist."""
        old_name = self._selected_named_name()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(
            self, self.tr("Rename Custom Playlist"),
            self.tr("New name:"), text=old_name
        )
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()
        if new_name == old_name:
            return
        if not self.playlist_manager.rename_named_playlist(old_name, new_name):
            QMessageBox.warning(
                self, self.tr("Rename Custom Playlist"),
                self.tr("A playlist named '{0}' already exists.").format(new_name)
            )
            return
        self._update_named_list()
        self._select_named(new_name)

    def _delete_named_playlist(self):
        """Delete the selected custom playlist."""
        name = self._selected_named_name()
        if not name:
            return
        reply = QMessageBox.question(
            self, self.tr("Delete Custom Playlist"),
            self.tr("Delete the custom playlist '{0}'?").format(name),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.playlist_manager.delete_named_playlist(name)
            self._update_named_list()
            self._refresh_saved_list()

    def _refresh_saved_list(self):
        """Refresh the custom playlist list (kept for backward compatibility)."""
        self._update_named_list()

    def _cycle_repeat(self):
        """Cycle repeat mode"""
        mode = self.playlist_manager.toggle_repeat()
        self.repeat_btn.setText(f"{self.tr('Repeat')}: {mode.value}")