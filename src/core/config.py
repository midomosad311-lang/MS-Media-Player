"""
Configuration Manager - Handles application configuration
"""

import json
from pathlib import Path
from typing import Any, Dict
from platformdirs import user_config_dir
from PySide6.QtCore import QObject, QTimer, QCoreApplication

from core.app_meta import ORG_NAME, USER_AGENT


class ConfigManager(QObject):
    """Manages application configuration

    Saves are *debounced*: rapidly changing settings (dragging the volume
    slider, scrubbing, changing the speed) would otherwise rewrite the whole
    JSON file dozens of times per second and freeze the UI.  Instead, a change
    marks the config dirty and a single-shot timer coalesces writes.
    """

    def __init__(self):
        super().__init__()
        self.config_dir = Path(user_config_dir(ORG_NAME))
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._config = self._load_config()

        # Debounced persistence.  Only used when a Qt event loop exists;
        # otherwise every change is written immediately (e.g. unit tests).
        self._dirty = False
        self._save_timer = None
        if QCoreApplication.instance() is not None:
            self._save_timer = QTimer(self)
            self._save_timer.setSingleShot(True)
            self._save_timer.setInterval(400)
            self._save_timer.timeout.connect(self._flush_save)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "language": "ar",
            "theme": "dark",
            "high_contrast": False,
            "hardware_acceleration": True,
            "volume": 100,
            "speed": 1.0,
            "seek_interval": 10,
            "repeat_mode": "off",
            "shuffle": False,
            "last_files": [],
            # What (if anything) the player reopens on start-up.  "empty" (the
            # default) opens a blank window so the player never attaches itself
            # to a previously played file unless the user asks for it.
            "startup_behavior": "empty",
            "last_session": {},
            "bookmarks": {},
            "window_geometry": {},
            "equalizer": {
                "enabled": False,
                "bands": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "preset": "flat"
            },
            "audio_sync": 0,
            "subtitle": {
                "enabled": True,
                "font_size": 18,
                "font_color": "#FFFFFF",
                "background_color": "#00000080",
                "encoding": "utf-8"
            },
            "network": {
                "buffer_size": 8192,
                "timeout": 30,
                "user_agent": USER_AGENT
            },
            "accessibility": {
                "screen_reader_support": True,
                "announce_position": True,
                "announce_shortcuts": True,
                "keyboard_navigation": True
            },
            "playlist": {
                "auto_load": True,
                "save_on_exit": True,
                "loop_playlist": False
            }
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    return self._merge_config(default_config, loaded)
            except (json.JSONDecodeError, IOError):
                pass

        return default_config

    def _merge_config(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._dirty = True
        self._schedule_save()

    def _schedule_save(self):
        """Coalesce rapid saves; write soon after the burst of changes stops."""
        if self._save_timer is not None:
            self._save_timer.start()  # restart the countdown
        else:
            self._save_config()
            self._dirty = False

    def _flush_save(self):
        """Timer callback: persist if there are pending changes."""
        if self._dirty:
            self._save_config()
            self._dirty = False

    def flush(self):
        """Force an immediate save (call on application exit)."""
        if self._save_timer is not None:
            self._save_timer.stop()
        if self._dirty:
            self._save_config()
            self._dirty = False

    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values"""
        for key, value in updates.items():
            self.set(key, value)

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._config.copy()