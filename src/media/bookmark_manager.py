"""
Bookmark Manager - Handles bookmarks for media files
"""

import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, asdict
from datetime import datetime
from PySide6.QtCore import QObject, Signal
from settings.settings_manager import SettingsManager


@dataclass
class Bookmark:
    """Represents a bookmark"""
    name: str
    position: float  # in seconds
    file_path: str
    created_at: str  # ISO format

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Bookmark':
        return cls(**data)


class BookmarkManager(QObject):
    """Manages bookmarks for media files"""

    bookmarks_changed = Signal(str)  # file_path

    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        self.settings = settings_manager
        self.bookmarks_file = Path(settings_manager.config.config_dir) / "bookmarks.json"
        self._bookmarks: Dict[str, List[Bookmark]] = {}  # file_path -> List[Bookmark]
        self._load_bookmarks()

    def _load_bookmarks(self):
        """Load bookmarks from JSON file"""
        if self.bookmarks_file.exists():
            try:
                with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for file_path, bookmarks_list in data.items():
                    self._bookmarks[file_path] = [Bookmark.from_dict(b) for b in bookmarks_list]
            except (json.JSONDecodeError, IOError) as e:
                print(f"Failed to load bookmarks: {e}")
                self._bookmarks = {}

    def _save_bookmarks(self):
        """Save bookmarks to JSON file"""
        try:
            data = {}
            for file_path, bookmarks_list in self._bookmarks.items():
                data[file_path] = [b.to_dict() for b in bookmarks_list]
            with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Failed to save bookmarks: {e}")

    def get_bookmarks(self, file_path: str) -> List[Bookmark]:
        """Get bookmarks for a file"""
        return self._bookmarks.get(file_path, [])

    def add_bookmark(self, file_path: str, position: float, name: str = None) -> Bookmark:
        """Add a new bookmark"""
        if file_path not in self._bookmarks:
            self._bookmarks[file_path] = []

        # Generate default name if not provided
        if name is None or name.strip() == "":
            existing_count = len(self._bookmarks[file_path])
            name = f"Bookmark {existing_count + 1}"

        bookmark = Bookmark(
            name=name,
            position=position,
            file_path=file_path,
            created_at=datetime.now().isoformat()
        )

        self._bookmarks[file_path].append(bookmark)
        self._save_bookmarks()
        self.bookmarks_changed.emit(file_path)
        return bookmark

    def remove_bookmark(self, file_path: str, index: int) -> bool:
        """Remove a bookmark by index"""
        if file_path in self._bookmarks and 0 <= index < len(self._bookmarks[file_path]):
            del self._bookmarks[file_path][index]
            if not self._bookmarks[file_path]:
                del self._bookmarks[file_path]
            self._save_bookmarks()
            self.bookmarks_changed.emit(file_path)
            return True
        return False

    def update_bookmark(self, file_path: str, index: int, name: str = None, position: float = None) -> bool:
        """Update a bookmark"""
        if file_path in self._bookmarks and 0 <= index < len(self._bookmarks[file_path]):
            bookmark = self._bookmarks[file_path][index]
            if name is not None:
                bookmark.name = name
            if position is not None:
                bookmark.position = position
            self._save_bookmarks()
            self.bookmarks_changed.emit(file_path)
            return True
        return False

    def clear_bookmarks(self, file_path: str):
        """Clear all bookmarks for a file"""
        if file_path in self._bookmarks:
            del self._bookmarks[file_path]
            self._save_bookmarks()
            self.bookmarks_changed.emit(file_path)

    def get_next_default_name(self, file_path: str) -> str:
        """Get next default bookmark name"""
        count = len(self._bookmarks.get(file_path, []))
        return f"Bookmark {count + 1}"