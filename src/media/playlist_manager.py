"""
Playlist Manager - Handles playlist management (M3U, shuffle, repeat)
"""

import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum
from PySide6.QtCore import QObject, Signal


class RepeatMode(Enum):
    OFF = "off"
    ONE = "one"
    ALL = "all"


class PlaylistManager(QObject):
    """Manages media playlists"""

    playlist_changed = Signal()
    current_index_changed = Signal(int)
    playlist_loaded = Signal(str)
    playlist_saved = Signal(str)
    named_playlists_changed = Signal()

    def __init__(self, settings_manager):
        super().__init__()
        self.settings = settings_manager
        self.items: List[Dict[str, Any]] = []
        self.current_index = -1
        # Restore the last used repeat / shuffle state so the shortcuts and
        # buttons start from the value the user last chose.
        try:
            self.repeat_mode = RepeatMode(self.settings.get_repeat_mode())
        except Exception:
            self.repeat_mode = RepeatMode.OFF
        try:
            self.shuffle = bool(self.settings.get_shuffle())
        except Exception:
            self.shuffle = False
        self.shuffle_indices: List[int] = []
        self.original_indices: List[int] = []
        if self.shuffle:
            self._generate_shuffle_indices()

        # Custom, independent named playlists.  Each entry maps a user-chosen
        # name to ``{"name": str, "items": [ {...}, ... ]}`` so files from
        # different folders can be grouped together without touching the
        # currently playing queue.
        self.named_playlists: Dict[str, Dict[str, Any]] = {}
        self._load_named_playlists()

        # Name of the folder that seeded the *default* playlist.  When the user
        # opens a file its folder automatically becomes the active playlist, so
        # Next / Previous walk through that folder; we remember the folder name
        # to show (and announce) it as the default playlist.
        self.folder_name = ""

    def set_folder_name(self, name: str):
        """Remember which folder the default playlist was built from."""
        self.folder_name = name or ""

    def get_folder_name(self) -> str:
        """Return the folder name of the current default playlist (may be empty)."""
        return self.folder_name

    def add_file(self, file_path: str, metadata: Dict = None) -> int:
        """Add file to playlist"""
        item = {
            "path": file_path,
            "name": Path(file_path).name,
            "metadata": metadata or {}
        }
        self.items.append(item)
        self.playlist_changed.emit()
        return len(self.items) - 1

    def add_files(self, file_paths: List[str]):
        """Add multiple files to playlist"""
        for path in file_paths:
            self.add_file(path)

    def remove_file(self, index: int) -> bool:
        """Remove file at index"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            if self.current_index >= index:
                self.current_index = max(-1, self.current_index - 1)
            self._update_shuffle_indices()
            self.playlist_changed.emit()
            return True
        return False

    def clear(self):
        """Clear playlist"""
        self.items.clear()
        self.current_index = -1
        self.shuffle_indices.clear()
        self.original_indices.clear()
        # An empty (or freshly loaded custom) queue is no longer a folder
        # playlist; drop the remembered folder name.
        self.folder_name = ""
        self.playlist_changed.emit()

    def get_items(self) -> List[Dict[str, Any]]:
        """Get playlist items"""
        return self.items.copy()

    def get_current_item(self) -> Optional[Dict[str, Any]]:
        """Get current playlist item"""
        if 0 <= self.current_index < len(self.items):
            return self.items[self.current_index]
        return None

    def get_current_path(self) -> Optional[str]:
        """Get current file path"""
        item = self.get_current_item()
        return item["path"] if item else None

    def set_current_index(self, index: int) -> bool:
        """Set current playlist index"""
        if 0 <= index < len(self.items):
            self.current_index = index
            self.current_index_changed.emit(index)
            return True
        return False

    def next(self) -> Optional[str]:
        """Get next item"""
        if not self.items:
            return None

        if self.shuffle:
            return self._shuffle_next()
        else:
            return self._sequential_next()

    def previous(self) -> Optional[str]:
        """Get previous item"""
        if not self.items:
            return None

        if self.shuffle:
            return self._shuffle_previous()
        else:
            return self._sequential_previous()

    def _sequential_next(self) -> Optional[str]:
        """Get next item in sequential order"""
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
        elif self.repeat_mode == RepeatMode.ALL:
            self.current_index = 0
        else:
            return None

        self.current_index_changed.emit(self.current_index)
        return self.items[self.current_index]["path"]

    def _sequential_previous(self) -> Optional[str]:
        """Get previous item in sequential order"""
        if self.current_index > 0:
            self.current_index -= 1
        elif self.repeat_mode == RepeatMode.ALL:
            self.current_index = len(self.items) - 1
        else:
            return None

        self.current_index_changed.emit(self.current_index)
        return self.items[self.current_index]["path"]

    def _shuffle_next(self) -> Optional[str]:
        """Get next item in shuffle order"""
        if not self.shuffle_indices:
            self._generate_shuffle_indices()

        try:
            current_pos = self.shuffle_indices.index(self.current_index)
            next_pos = current_pos + 1

            if next_pos >= len(self.shuffle_indices):
                if self.repeat_mode == RepeatMode.ALL:
                    self._generate_shuffle_indices()
                    next_pos = 0
                else:
                    return None

            self.current_index = self.shuffle_indices[next_pos]
            self.current_index_changed.emit(self.current_index)
            return self.items[self.current_index]["path"]
        except ValueError:
            # Current index not in shuffle list, start from beginning
            self.current_index = self.shuffle_indices[0]
            self.current_index_changed.emit(self.current_index)
            return self.items[self.current_index]["path"]

    def _shuffle_previous(self) -> Optional[str]:
        """Get previous item in shuffle order"""
        if not self.shuffle_indices:
            self._generate_shuffle_indices()

        try:
            current_pos = self.shuffle_indices.index(self.current_index)
            prev_pos = current_pos - 1

            if prev_pos < 0:
                if self.repeat_mode == RepeatMode.ALL:
                    self._generate_shuffle_indices()
                    prev_pos = len(self.shuffle_indices) - 1
                else:
                    return None

            self.current_index = self.shuffle_indices[prev_pos]
            self.current_index_changed.emit(self.current_index)
            return self.items[self.current_index]["path"]
        except ValueError:
            self.current_index = self.shuffle_indices[0]
            self.current_index_changed.emit(self.current_index)
            return self.items[self.current_index]["path"]

    def _generate_shuffle_indices(self):
        """Generate new shuffle order"""
        self.shuffle_indices = list(range(len(self.items)))
        random.shuffle(self.shuffle_indices)

    def _update_shuffle_indices(self):
        """Update shuffle indices after playlist modification"""
        if self.shuffle:
            # Remove invalid indices
            self.shuffle_indices = [i for i in self.shuffle_indices if i < len(self.items)]
            # Add new indices
            existing = set(self.shuffle_indices)
            for i in range(len(self.items)):
                if i not in existing:
                    self.shuffle_indices.append(i)

    def set_repeat_mode(self, mode: RepeatMode):
        """Set repeat mode"""
        self.repeat_mode = mode

    def get_repeat_mode(self) -> RepeatMode:
        return self.repeat_mode

    def toggle_repeat(self) -> RepeatMode:
        """Cycle through repeat modes"""
        modes = [RepeatMode.OFF, RepeatMode.ONE, RepeatMode.ALL]
        current_idx = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(current_idx + 1) % len(modes)]
        return self.repeat_mode

    def set_shuffle(self, enabled: bool):
        """Enable/disable shuffle"""
        self.shuffle = enabled
        if enabled:
            self._generate_shuffle_indices()
        else:
            self.shuffle_indices.clear()

    def get_shuffle(self) -> bool:
        return self.shuffle

    def toggle_shuffle(self) -> bool:
        """Toggle shuffle"""
        self.set_shuffle(not self.shuffle)
        return self.shuffle

    def move_item(self, from_index: int, to_index: int) -> bool:
        """Move item to new position"""
        if 0 <= from_index < len(self.items) and 0 <= to_index < len(self.items):
            item = self.items.pop(from_index)
            self.items.insert(to_index, item)

            # Update current index
            if self.current_index == from_index:
                self.current_index = to_index
            elif from_index < self.current_index <= to_index:
                self.current_index -= 1
            elif to_index <= self.current_index < from_index:
                self.current_index += 1

            self._update_shuffle_indices()
            self.playlist_changed.emit()
            return True
        return False

    def sort_by_name(self, ascending: bool = True):
        """Sort playlist by name"""
        self.items.sort(key=lambda x: x["name"].lower(), reverse=not ascending)
        self._update_indices_after_sort()
        self.playlist_changed.emit()

    def sort_by_path(self, ascending: bool = True):
        """Sort playlist by path"""
        self.items.sort(key=lambda x: x["path"].lower(), reverse=not ascending)
        self._update_indices_after_sort()
        self.playlist_changed.emit()

    def _update_indices_after_sort(self):
        """Update indices (current + shuffle) after sorting the playlist."""
        self._update_shuffle_indices()

    def load_m3u(self, file_path: str, clear_existing: bool = True) -> bool:
        """Load M3U playlist"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.strip().split('\n')
            paths = []

            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Handle relative paths
                    if not os.path.isabs(line):
                        base_dir = Path(file_path).parent
                        line = str(base_dir / line)
                    paths.append(line)

            if clear_existing:
                self.clear()
            self.add_files(paths)
            self.playlist_loaded.emit(file_path)
            return True

        except Exception as e:
            print(f"Failed to load M3U: {e}")
            return False

    def save_m3u(self, file_path: str) -> bool:
        """Save playlist as M3U"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for item in self.items:
                    f.write(f"#EXTINF:-1,{item['name']}\n")
                    f.write(f"{item['path']}\n")
            self.playlist_saved.emit(file_path)
            return True
        except Exception as e:
            print(f"Failed to save M3U: {e}")
            return False

    def get_count(self) -> int:
        return len(self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def get_next_path(self) -> Optional[str]:
        """Peek at next path without changing current"""
        if not self.items:
            return None

        if self.shuffle:
            if not self.shuffle_indices:
                self._generate_shuffle_indices()
            try:
                current_pos = self.shuffle_indices.index(self.current_index)
                next_pos = (current_pos + 1) % len(self.shuffle_indices)
                return self.items[self.shuffle_indices[next_pos]]["path"]
            except ValueError:
                return self.items[self.shuffle_indices[0]]["path"]
        else:
            next_idx = self.current_index + 1
            if next_idx >= len(self.items):
                if self.repeat_mode == RepeatMode.ALL:
                    next_idx = 0
                else:
                    return None
            return self.items[next_idx]["path"]

    def export_to_dict(self) -> Dict[str, Any]:
        """Export playlist to dictionary"""
        return {
            "items": self.items,
            "current_index": self.current_index,
            "repeat_mode": self.repeat_mode.value,
            "shuffle": self.shuffle
        }

    def import_from_dict(self, data: Dict[str, Any]):
        """Import playlist from dictionary"""
        self.items = data.get("items", [])
        self.current_index = data.get("current_index", -1)
        self.repeat_mode = RepeatMode(data.get("repeat_mode", "off"))
        self.shuffle = data.get("shuffle", False)
        if self.shuffle:
            self._generate_shuffle_indices()
        self.playlist_changed.emit()

    # ------------------------------------------------------------------
    # Custom named playlists (independent of the active queue)
    # ------------------------------------------------------------------
    @staticmethod
    def _make_item(path: str) -> Dict[str, Any]:
        """Build a playlist item dict for a path/URL."""
        return {
            "path": path,
            "name": Path(path).name or path,
            "metadata": {}
        }

    def _load_named_playlists(self):
        """Load named playlists persisted in the settings store."""
        try:
            data = self.settings.get_named_playlists()
        except Exception:
            data = {}
        self.named_playlists = {}
        if isinstance(data, dict):
            for name, entry in data.items():
                if isinstance(entry, dict):
                    self.named_playlists[name] = {
                        "name": name,
                        "items": [self._make_item(p) if isinstance(p, str) else p
                                  for p in entry.get("items", [])]
                    }

    def _save_named_playlists(self):
        """Persist named playlists to the settings store."""
        try:
            data = {
                name: {"name": name, "items": [it["path"] for it in entry["items"]]}
                for name, entry in self.named_playlists.items()
            }
            self.settings.set_named_playlists(data)
        except Exception as e:
            print(f"Failed to save named playlists: {e}")
        self.named_playlists_changed.emit()

    def get_named_playlists(self) -> List[str]:
        """Return the sorted list of custom playlist names."""
        return sorted(self.named_playlists.keys(), key=str.lower)

    def has_named_playlist(self, name: str) -> bool:
        return name in self.named_playlists

    def create_named_playlist(self, name: str, overwrite: bool = False) -> bool:
        """Create a new, empty custom playlist with the given name.

        Returns False when a playlist with that name already exists (unless
        ``overwrite`` is True).
        """
        name = (name or "").strip()
        if not name:
            return False
        if name in self.named_playlists and not overwrite:
            return False
        self.named_playlists[name] = {"name": name, "items": []}
        self._save_named_playlists()
        return True

    def delete_named_playlist(self, name: str) -> bool:
        """Delete a custom playlist."""
        if name in self.named_playlists:
            del self.named_playlists[name]
            self._save_named_playlists()
            return True
        return False

    def rename_named_playlist(self, old_name: str, new_name: str) -> bool:
        """Rename a custom playlist, keeping its items."""
        new_name = (new_name or "").strip()
        if old_name not in self.named_playlists or not new_name:
            return False
        if new_name in self.named_playlists and new_name != old_name:
            return False
        entry = self.named_playlists.pop(old_name)
        entry["name"] = new_name
        self.named_playlists[new_name] = entry
        self._save_named_playlists()
        return True

    def add_to_named_playlist(self, name: str, file_path: str) -> bool:
        """Add a file/URL to a custom playlist, creating it if needed."""
        if not name:
            return False
        if name not in self.named_playlists:
            self.create_named_playlist(name)
        entry = self.named_playlists[name]
        if any(it["path"] == file_path for it in entry["items"]):
            return False  # already present - keep playlists duplicate-free
        entry["items"].append(self._make_item(file_path))
        self._save_named_playlists()
        return True

    def add_files_to_named_playlist(self, name: str, file_paths: List[str]):
        """Add several files/URLs to a custom playlist."""
        for path in file_paths:
            self.add_to_named_playlist(name, path)

    def remove_from_named_playlist(self, name: str, index: int) -> bool:
        """Remove an item from a custom playlist by index."""
        entry = self.named_playlists.get(name)
        if not entry or not (0 <= index < len(entry["items"])):
            return False
        entry["items"].pop(index)
        self._save_named_playlists()
        return True

    def get_named_playlist_items(self, name: str) -> List[Dict[str, Any]]:
        """Return a copy of a custom playlist's items."""
        entry = self.named_playlists.get(name)
        return [dict(it) for it in entry["items"]] if entry else []

    def get_named_playlist_count(self, name: str) -> int:
        entry = self.named_playlists.get(name)
        return len(entry["items"]) if entry else 0

    def load_named_playlist(self, name: str, replace: bool = True) -> bool:
        """Load a custom playlist into the active queue for playback."""
        entry = self.named_playlists.get(name)
        if entry is None:
            return False
        if replace:
            self.clear()
        for it in entry["items"]:
            self.add_file(it["path"], it.get("metadata"))
        self.playlist_loaded.emit(name)
        return True

    def save_to_named_playlist(self, name: str, replace: bool = True) -> bool:
        """Save the active queue as a custom named playlist."""
        name = (name or "").strip()
        if not name:
            return False
        if replace or name not in self.named_playlists:
            self.named_playlists[name] = {"name": name, "items": []}
        entry = self.named_playlists[name]
        existing = {it["path"] for it in entry["items"]}
        for it in self.items:
            if it["path"] not in existing:
                entry["items"].append({"path": it["path"], "name": it["name"],
                                       "metadata": it.get("metadata", {})})
                existing.add(it["path"])
        self._save_named_playlists()
        return True