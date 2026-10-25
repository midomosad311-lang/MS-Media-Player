"""
Settings Manager - Handles application settings and theme management
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal
from core.app_meta import USER_AGENT
from core.config import ConfigManager
from ui.themes.theme_manager import ThemeManager


class SettingsManager(QObject):
    """Manages application settings"""

    settings_changed = Signal(str, object)
    theme_changed = Signal(str)

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        self.theme_manager = ThemeManager(self)
        self._setup_defaults()

    def _setup_defaults(self):
        """Setup default settings"""
        pass

    def get_language(self) -> str:
        return self.config.get("language", "ar")

    def set_language(self, language: str):
        self.config.set("language", language)
        self.settings_changed.emit("language", language)

    def get_theme(self) -> str:
        return self.config.get("theme", "dark")

    def set_theme(self, theme: str):
        self.config.set("theme", theme)
        self.theme_manager.apply_theme(theme)
        self.theme_changed.emit(theme)

    def get_high_contrast(self) -> bool:
        return self.config.get("high_contrast", False)

    def set_high_contrast(self, enabled: bool):
        self.config.set("high_contrast", enabled)
        self.theme_manager.apply_high_contrast(enabled)
        self.settings_changed.emit("high_contrast", enabled)

    def get_hardware_acceleration(self) -> bool:
        return self.config.get("hardware_acceleration", True)

    def set_hardware_acceleration(self, enabled: bool):
        self.config.set("hardware_acceleration", enabled)
        self.settings_changed.emit("hardware_acceleration", enabled)

    def get_volume(self) -> int:
        return self.config.get("volume", 100)

    def set_volume(self, volume: int):
        self.config.set("volume", max(0, min(100, volume)))
        self.settings_changed.emit("volume", self.get_volume())

    def get_speed(self) -> float:
        return self.config.get("speed", 1.0)

    def set_speed(self, speed: float):
        self.config.set("speed", speed)
        self.settings_changed.emit("speed", speed)

    def get_seek_interval(self) -> int:
        return self.config.get("seek_interval", 10)

    def set_seek_interval(self, interval: int):
        self.config.set("seek_interval", max(1, min(3600, interval)))
        self.settings_changed.emit("seek_interval", self.get_seek_interval())

    def get_repeat_mode(self) -> str:
        return self.config.get("repeat_mode", "off")

    def set_repeat_mode(self, mode: str):
        self.config.set("repeat_mode", mode)
        self.settings_changed.emit("repeat_mode", mode)

    def get_shuffle(self) -> bool:
        return self.config.get("shuffle", False)

    def set_shuffle(self, enabled: bool):
        self.config.set("shuffle", enabled)
        self.settings_changed.emit("shuffle", enabled)

    def get_equalizer_settings(self) -> Dict[str, Any]:
        return self.config.get("equalizer", {
            "enabled": False,
            "bands": [0] * 10,
            "preset": "flat"
        })

    def set_equalizer_settings(self, settings: Dict[str, Any]):
        self.config.set("equalizer", settings)
        self.settings_changed.emit("equalizer", settings)

    def get_audio_sync(self) -> int:
        return self.config.get("audio_sync", 0)

    def set_audio_sync(self, sync: int):
        self.config.set("audio_sync", sync)
        self.settings_changed.emit("audio_sync", sync)

    def get_subtitle_settings(self) -> Dict[str, Any]:
        return self.config.get("subtitle", {
            "enabled": True,
            "font_size": 18,
            "font_color": "#FFFFFF",
            "background_color": "#00000080",
            "encoding": "utf-8"
        })

    def set_subtitle_settings(self, settings: Dict[str, Any]):
        self.config.set("subtitle", settings)
        self.settings_changed.emit("subtitle", settings)

    # Startup behaviour ---------------------------------------------------
    # One of "empty" (default), "last_file", "last_playlist", "resume".
    STARTUP_EMPTY = "empty"
    STARTUP_LAST_FILE = "last_file"
    STARTUP_LAST_PLAYLIST = "last_playlist"
    STARTUP_RESUME = "resume"
    STARTUP_MODES = (
        STARTUP_EMPTY, STARTUP_LAST_FILE, STARTUP_LAST_PLAYLIST, STARTUP_RESUME,
    )

    def get_startup_behavior(self) -> str:
        """How the player should start next time.

        Defaults to "empty" so a freshly installed (or freshly uninstalled and
        reinstalled) player always opens without a media file loaded - it must
        never silently re-associate itself with a file from a previous session.
        """
        value = self.config.get("startup_behavior", self.STARTUP_EMPTY)
        return value if value in self.STARTUP_MODES else self.STARTUP_EMPTY

    def set_startup_behavior(self, behavior: str):
        if behavior not in self.STARTUP_MODES:
            behavior = self.STARTUP_EMPTY
        self.config.set("startup_behavior", behavior)
        self.settings_changed.emit("startup_behavior", behavior)

    def get_last_session(self) -> Dict[str, Any]:
        """Snapshot of the previous session (playlist, current file, position)."""
        return self.config.get("last_session", {}) or {}

    def set_last_session(self, session: Dict[str, Any]):
        self.config.set("last_session", session or {})

    def get_network_settings(self) -> Dict[str, Any]:
        return self.config.get("network", {
            "buffer_size": 8192,
            "timeout": 30,
            "user_agent": USER_AGENT
        })

    def set_network_settings(self, settings: Dict[str, Any]):
        self.config.set("network", settings)
        self.settings_changed.emit("network", settings)

    def get_accessibility_settings(self) -> Dict[str, Any]:
        return self.config.get("accessibility", {
            "screen_reader_support": True,
            "announce_position": True,
            "announce_shortcuts": True,
            "keyboard_navigation": True
        })

    def set_accessibility_settings(self, settings: Dict[str, Any]):
        self.config.set("accessibility", settings)
        self.settings_changed.emit("accessibility", settings)

    def get_playlist_settings(self) -> Dict[str, Any]:
        return self.config.get("playlist", {
            "auto_load": True,
            "save_on_exit": True,
            "loop_playlist": False
        })

    def set_playlist_settings(self, settings: Dict[str, Any]):
        # Merge instead of replacing so options that are not present in the
        # caller's dict (for example "autoplay_next") are not silently dropped.
        merged = dict(self.config.get("playlist", {}) or {})
        merged.update(settings)
        self.config.set("playlist", merged)
        self.settings_changed.emit("playlist", merged)

    def get_autoplay_next(self) -> bool:
        """Whether playback advances to the next item when a file finishes.

        This backs the "Auto-play Next" option in Settings > Playback and
        decides what the Space key does once a file has ended: advance to the
        next item when enabled (and one exists), otherwise replay the current
        file from the beginning.
        """
        playlist = self.config.get("playlist", {}) or {}
        return bool(playlist.get("autoplay_next", True))

    def set_autoplay_next(self, enabled: bool):
        playlist = dict(self.config.get("playlist", {}) or {})
        playlist["autoplay_next"] = bool(enabled)
        self.config.set("playlist", playlist)
        self.settings_changed.emit("playlist", playlist)

    def add_recent_file(self, file_path: str):
        recent = self.config.get("last_files", [])
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        recent = recent[:20]
        self.config.set("last_files", recent)
        # Keep the "Open Recent" menu in sync while the app is running.
        self.settings_changed.emit("last_files", recent)

    def get_recent_files(self) -> list:
        return self.config.get("last_files", [])

    def get_named_playlists(self) -> Dict[str, Any]:
        """Return the persisted custom (named) playlists."""
        return self.config.get("named_playlists", {})

    def set_named_playlists(self, playlists: Dict[str, Any]):
        """Persist the custom (named) playlists."""
        self.config.set("named_playlists", playlists)
        self.settings_changed.emit("named_playlists", playlists)

    def get_last_open_dir(self) -> str:
        return self.config.get("last_open_dir", "")

    def set_last_open_dir(self, directory: str):
        self.config.set("last_open_dir", directory)
        self.settings_changed.emit("last_open_dir", directory)

    def clear_recent_files(self):
        self.config.set("last_files", [])
        self.settings_changed.emit("last_files", [])

    def save_bookmark(self, file_path: str, position: float):
        bookmarks = self.config.get("bookmarks", {})
        bookmarks[file_path] = position
        self.config.set("bookmarks", bookmarks)

    def get_bookmark(self, file_path: str) -> Optional[float]:
        bookmarks = self.config.get("bookmarks", {})
        return bookmarks.get(file_path)

    def remove_bookmark(self, file_path: str):
        bookmarks = self.config.get("bookmarks", {})
        if file_path in bookmarks:
            del bookmarks[file_path]
            self.config.set("bookmarks", bookmarks)

    def save_window_geometry(self, window_id: str, geometry: bytes):
        geometries = self.config.get("window_geometry", {})
        # QByteArray doesn't have .hex() method in PySide6
        geometries[window_id] = bytes(geometry).hex()
        self.config.set("window_geometry", geometries)

    def get_window_geometry(self, window_id: str) -> Optional[bytes]:
        geometries = self.config.get("window_geometry", {})
        hex_str = geometries.get(window_id)
        if hex_str:
            return bytes.fromhex(hex_str)
        return None

    def apply_theme(self, app: QApplication):
        """Apply current theme to application"""
        theme = self.get_theme()
        high_contrast = self.get_high_contrast()
        self.theme_manager.apply_theme(theme, high_contrast, app)

    def export_settings(self, file_path: str) -> bool:
        """Export settings to file"""
        try:
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.get_all(), f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False

    def import_settings(self, file_path: str) -> bool:
        """Import settings from file"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            for key, value in settings.items():
                self.config.set(key, value)
            return True
        except Exception:
            return False

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        default_keys = [
            "language", "theme", "high_contrast", "hardware_acceleration",
            "volume", "speed", "seek_interval", "repeat_mode", "shuffle",
            "equalizer", "audio_sync", "subtitle", "network",
            "accessibility", "playlist"
        ]
        for key in default_keys:
            self.config.set(key, self.config._load_config().get(key))