"""
Shortcuts Dialog - Keyboard shortcuts viewer
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QLineEdit, QDialogButtonBox, QHeaderView
)
from PySide6.QtCore import Qt
from accessibility.accessibility_manager import AccessibilityManager


class ShortcutsDialog(QDialog):
    """Keyboard shortcuts dialog"""

    def __init__(self, accessibility_manager: AccessibilityManager, parent=None):
        super().__init__(parent)
        self.accessibility = accessibility_manager
        self.setWindowTitle(self.tr("Keyboard Shortcuts"))
        self.resize(700, 500)
        self.setModal(True)

        self._setup_ui()
        self._load_shortcuts()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel(self.tr("Search:")))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(self.tr("Filter shortcuts..."))
        self.search_edit.textChanged.connect(self._filter_shortcuts)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Shortcuts tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([self.tr("Action"), self.tr("Shortcut"), self.tr("Description")])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.AscendingOrder)

        # Set column widths
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(self.tree)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel(self.tr("Legend:")))
        legend_layout.addWidget(QLabel("Ctrl = Ctrl | Shift = Shift | Alt = Alt | Esc = Esc"))
        legend_layout.addStretch()
        layout.addLayout(legend_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)

    def _load_shortcuts(self):
        """Load shortcuts into tree (localized labels, real key sequences)."""
        # (name, localized label) grouped by localized category
        categories = [
            (self.tr("Playback"), [
                ("play_pause", self.tr("Play / Pause")),
                ("stop", self.tr("Stop")),
                ("next", self.tr("Next Track")),
                ("previous", self.tr("Previous Track")),
                ("forward", self.tr("Seek Forward")),
                ("backward", self.tr("Seek Backward")),
                ("forward_long", self.tr("Seek Forward (long)")),
                ("backward_long", self.tr("Seek Backward (long)")),
            ]),
            (self.tr("Volume"), [
                ("volume_up", self.tr("Volume Up")),
                ("volume_down", self.tr("Volume Down")),
                ("mute", self.tr("Mute")),
            ]),
            (self.tr("View"), [
                ("fullscreen", self.tr("Fullscreen")),
                ("playlist", self.tr("Playlist")),
            ]),
            (self.tr("Speed"), [
                ("speed_up", self.tr("Speed Up")),
                ("speed_down", self.tr("Speed Down")),
                ("speed_normal", self.tr("Normal Speed")),
            ]),
            (self.tr("Playlist"), [
                ("repeat", self.tr("Repeat")),
                ("shuffle", self.tr("Shuffle")),
            ]),
            (self.tr("File"), [
                ("open_file", self.tr("Open File")),
                ("open_url", self.tr("Open URL")),
                ("quit", self.tr("Exit")),
            ]),
            (self.tr("Tools"), [
                ("settings", self.tr("Settings")),
                ("announce_time", self.tr("Announce Current Time")),
            ]),
        ]

        for category, entries in categories:
            cat_item = QTreeWidgetItem([category, "", ""])
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsSelectable)
            font = cat_item.font(0)
            font.setBold(True)
            cat_item.setFont(0, font)
            self.tree.addTopLevelItem(cat_item)

            for name, label in entries:
                shortcut = self.accessibility.get_shortcut_sequence(name)
                item = QTreeWidgetItem([label, shortcut, ""])
                cat_item.addChild(item)

        self.tree.expandAll()

    def _parse_shortcut(self, key: str, description: str) -> tuple:
        """Return (key_sequence, description) for a shortcut name."""
        shortcut = self.accessibility.get_shortcut_sequence(key)
        return shortcut, description

    def _filter_shortcuts(self, text: str):
        """Filter shortcuts"""
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(i)
            has_visible = False
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                action = child.text(0).lower()
                shortcut = child.text(1).lower()
                match = text in action or text in shortcut
                child.setHidden(not match)
                if match:
                    has_visible = True
            cat_item.setHidden(not has_visible)