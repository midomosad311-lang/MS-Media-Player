"""
Accessibility Manager - Handles screen reader support and keyboard navigation
"""

from typing import Dict, Optional, Callable
from PySide6.QtCore import QObject, Signal, Qt, QEvent, QTimer
from PySide6.QtWidgets import QWidget, QApplication, QSlider
from PySide6.QtGui import QKeySequence, QShortcut
from settings.settings_manager import SettingsManager


class AccessibilityManager(QObject):
    """Manages accessibility features for screen readers and keyboard navigation"""

    # Signals
    announce_requested = Signal(str)
    shortcut_triggered = Signal(str)

    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        self.settings = settings_manager
        self.shortcuts: Dict[str, QShortcut] = {}
        self.shortcut_descriptions: Dict[str, str] = {}
        self.shortcut_sequences: Dict[str, str] = {}  # name -> key sequence
        self.focus_widget: Optional[QWidget] = None
        self.announce_timer = QTimer()
        self.announce_timer.setSingleShot(True)
        self.announce_timer.timeout.connect(self._process_announce_queue)
        self.announce_queue = []

        # Accessibility settings
        self.screen_reader_support = True
        self._announce_position_enabled = True
        self.announce_shortcuts = True
        self.keyboard_navigation = True

        self._load_settings()

    def _load_settings(self):
        """Load accessibility settings"""
        acc_settings = self.settings.get_accessibility_settings()
        self.screen_reader_support = acc_settings.get("screen_reader_support", True)
        self._announce_position_enabled = acc_settings.get("announce_position", True)
        self.announce_shortcuts = acc_settings.get("announce_shortcuts", True)
        self.keyboard_navigation = acc_settings.get("keyboard_navigation", True)

    def register_shortcut(self, key_sequence: str, callback: Callable,
                          description: str, context: QWidget = None) -> QShortcut:
        """Register a global keyboard shortcut with accessibility description.

        ``context`` should be a QWidget (a window).  A QShortcut with a
        ``Qt::WindowShortcut`` context is only active when its parent is a
        widget belonging to the active window.  Passing a non-widget parent
        (such as the QApplication) produces a shortcut that never fires, which
        is why Next/Previous and every other global shortcut used to do
        nothing.
        """
        # Prefer an explicit widget context, then the active window.
        parent = context
        if parent is None or not isinstance(parent, QWidget):
            active = QApplication.activeWindow()
            parent = active if isinstance(active, QWidget) else None

        if parent is None:
            # No window yet - defer until a window exists (see
            # MediaPlayerApplication._install_shortcuts).
            return None

        shortcut = QShortcut(QKeySequence(key_sequence), parent)
        shortcut.activated.connect(callback)
        # Use WindowShortcut to avoid COM issues with VLC on Windows
        # ApplicationShortcut can cause RPC_E_DISCONNECTED crashes with VLC
        shortcut.setContext(Qt.WindowShortcut)

        shortcut_id = f"{id(parent)}::{key_sequence.lower().replace(' ', '')}"
        self.shortcuts[shortcut_id] = shortcut
        self.shortcut_descriptions[key_sequence.lower().replace(" ", "")] = description
        self.shortcut_sequences[description] = key_sequence

        return shortcut

    def get_shortcut_sequence(self, name: str) -> str:
        """Get the key sequence registered for a shortcut name."""
        if name in self.shortcut_sequences:
            return self.shortcut_sequences[name]
        from accessibility.accessibility_manager import STANDARD_SHORTCUTS
        return STANDARD_SHORTCUTS.get(name, "")

    def unregister_shortcut(self, key_sequence: str):
        """Unregister a keyboard shortcut"""
        shortcut_id = key_sequence.lower().replace(" ", "")
        # Remove every context-specific instance of this key
        for sid in [k for k in self.shortcuts if k.endswith(f"::{shortcut_id}") or k == shortcut_id]:
            try:
                self.shortcuts[sid].deleteLater()
            except Exception:
                pass
            del self.shortcuts[sid]
        self.shortcut_descriptions.pop(shortcut_id, None)

    def get_shortcut_description(self, key_sequence: str) -> str:
        """Get description for a shortcut"""
        shortcut_id = key_sequence.lower().replace(" ", "")
        return self.shortcut_descriptions.get(shortcut_id, "")

    def announce(self, message: str, priority: bool = False):
        """Announce message to screen readers"""
        if not self.screen_reader_support:
            return

        if priority:
            self.announce_queue.insert(0, message)
        else:
            self.announce_queue.append(message)

        if not self.announce_timer.isActive():
            self.announce_timer.start(100)

    def _process_announce_queue(self):
        """Process announce queue"""
        while self.announce_queue:
            message = self.announce_queue.pop(0)
            self.announce_requested.emit(message)

    def announce_position(self, current: float, total: float):
        """Announce playback position"""
        if not self._announce_position_enabled:
            return

        if total > 0:
            percent = int((current / total) * 100)
            mins = int(current // 60)
            secs = int(current % 60)
            total_mins = int(total // 60)
            total_secs = int(total % 60)
            message = f"Position: {mins}:{secs:02d} of {total_mins}:{total_secs:02d}, {percent} percent"
        else:
            message = f"Position: {int(current // 60)}:{int(current % 60):02d}"

        self.announce(message)

    def announce_state(self, state: str):
        """Announce player state"""
        self.announce(state, priority=True)

    def setup_widget_accessibility(self, widget: QWidget, name: str,
                                   description: str = "", shortcut: str = ""):
        """Setup accessibility properties for a widget - announces ONLY shortcut, not name"""
        widget.setAccessibleName(name)
        
        # Description: ONLY the shortcut key, NOT "name shortcut"
        # This prevents screen readers from reading "Play, play space" (duplicate name)
        if shortcut:
            # Extract just the key part (e.g., "Space" from "Ctrl+Space")
            shortcut_key = shortcut.split("+")[-1] if "+" in shortcut else shortcut
            description_text = shortcut_key.lower()
        else:
            description_text = description
        widget.setAccessibleDescription(description_text)

        # Ensure widget can receive focus
        widget.setFocusPolicy(Qt.StrongFocus)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Handle keyboard events for accessible navigation"""
        if not self.keyboard_navigation:
            return super().eventFilter(obj, event)

        if event.type() == QEvent.KeyPress:
            key = event.key()

            # Handle slider navigation
            if hasattr(obj, '_accessibility_get_value_text'):
                if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Home, Qt.Key_End):
                    # Custom slider navigation: Up/Down = 10%, Home = 0%, End = 100%
                    slider = obj
                    if isinstance(slider, QSlider):
                        current_value = slider.value()
                        min_val = slider.minimum()
                        max_val = slider.maximum()
                        range_val = max_val - min_val

                        if key == Qt.Key_Up:
                            # Increase by 10%
                            new_value = min(max_val, current_value + int(range_val * 0.1))
                            slider.setValue(new_value)
                            event.accept()
                        elif key == Qt.Key_Down:
                            # Decrease by 10%
                            new_value = max(min_val, current_value - int(range_val * 0.1))
                            slider.setValue(new_value)
                            event.accept()
                        elif key == Qt.Key_Home:
                            # Jump to start (0%)
                            slider.setValue(min_val)
                            event.accept()
                        elif key == Qt.Key_End:
                            # Jump to end (100%)
                            slider.setValue(max_val)
                            event.accept()

                        # Announce new value
                        QTimer.singleShot(50, lambda: self._announce_slider_value(slider))
                        return True

                # Let slider handle other keys (Left, Right, PageUp, PageDown), then announce
                if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_PageUp, Qt.Key_PageDown):
                    QTimer.singleShot(50, lambda: self._announce_slider_value(obj))

        return super().eventFilter(obj, event)

    def _announce_slider_value(self, slider: QWidget):
        """Announce slider value after change"""
        if hasattr(slider, '_accessibility_get_value_text'):
            text = slider._accessibility_get_value_text()
            if text:
                self.announce(text)

    def enable_screen_reader_support(self, enabled: bool):
        """Enable/disable screen reader support"""
        self.screen_reader_support = enabled
        self.settings.set_accessibility_settings({
            **self.settings.get_accessibility_settings(),
            "screen_reader_support": enabled
        })

    def set_announce_position(self, enabled: bool):
        """Enable/disable position announcements"""
        self._announce_position_enabled = enabled
        self.settings.set_accessibility_settings({
            **self.settings.get_accessibility_settings(),
            "announce_position": enabled
        })

    def set_announce_shortcuts(self, enabled: bool):
        """Enable/disable shortcut announcements"""
        self.announce_shortcuts = enabled
        self.settings.set_accessibility_settings({
            **self.settings.get_accessibility_settings(),
            "announce_shortcuts": enabled
        })

    def set_keyboard_navigation(self, enabled: bool):
        """Enable/disable enhanced keyboard navigation"""
        self.keyboard_navigation = enabled
        self.settings.set_accessibility_settings({
            **self.settings.get_accessibility_settings(),
            "keyboard_navigation": enabled
        })

    def get_all_shortcuts(self) -> Dict[str, str]:
        """Get all registered shortcuts with descriptions"""
        return self.shortcut_descriptions.copy()

    def create_accessible_menu(self, menu, title: str, description: str = ""):
        """Create accessible menu"""
        menu.setTitle(title)
        menu.setAccessibleName(title)
        menu.setAccessibleDescription(description)
        return menu

    def create_accessible_action(self, text: str, shortcut: str = "",
                                 description: str = "", checkable: bool = False):
        """Create accessible action - announces ONLY the shortcut key, not name"""
        from PySide6.QtGui import QAction
        action = QAction(text)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        
        # Accessible name: just the text
        action.setProperty("accessibleName", text)
        
        # Accessible description: ONLY the shortcut key, NOT "name shortcut"
        # Screen readers already announce shortcuts automatically
        # This prevents "Play, play space" duplicate reading
        if shortcut:
            shortcut_key = shortcut.split("+")[-1] if "+" in shortcut else shortcut
            action.setProperty("accessibleDescription", shortcut_key.lower())
        else:
            action.setProperty("accessibleDescription", text.lower())
        
        action.setCheckable(checkable)

        return action

    def update_slider_accessible_value(self, slider: QSlider, value_text: str):
        """Update slider's accessible value for screen readers.

        Note: we deliberately do *not* post a raw ``QAccessibleEvent`` here.
        Emitting ``QAccessible.updateAccessibility`` for a slider from Python
        reproducibly crashes (access violation / 0xC0000005) on Windows with
        the VLC backend, so the stored property is used instead and screen
        readers read the slider's value on focus as usual.
        """
        try:
            slider.setProperty("accessibleValue", value_text)
        except Exception:
            pass

    def setup_slider_accessibility(self, slider: QWidget, name: str,
                                   get_value_text: Callable = None):
        """Setup accessibility for slider/progress bar"""
        self.setup_widget_accessibility(slider, name)

        # Expose the human-readable value both as a property and as the
        # accessible description, so screen readers can read the full state
        # (file name, total duration, elapsed / remaining) on focus.
        if isinstance(slider, QSlider) and get_value_text:
            try:
                value_text = get_value_text()
                slider.setProperty("accessibleValue", value_text)
                if value_text:
                    slider.setAccessibleDescription(value_text)
            except Exception:
                pass

        # Install event filter for keyboard navigation
        slider.installEventFilter(self)

        # Store value text function
        if get_value_text:
            slider._accessibility_get_value_text = get_value_text


# Standard shortcuts for media player - just the key, no descriptions
# Distinct shortcuts for each function to avoid conflicts
STANDARD_SHORTCUTS = {
    "play_pause": "Space",
    "stop": "S",
    "next": "Ctrl+Right",     # Next track
    "previous": "Ctrl+Left",  # Previous track
    "forward": "Right",       # Seek forward (short)
    "backward": "Left",       # Seek backward (short)
    "forward_long": "Shift+Right",  # Seek forward long
    "backward_long": "Shift+Left",  # Seek backward long
    "volume_up": "+",         # Volume up (Plus key)
    "volume_down": "-",       # Volume down (Minus key)
    "mute": "M",
    "fullscreen": "F",
    "playlist": "Ctrl+L",
    "settings": "Ctrl+P",
    "open_file": "Ctrl+O",
    "open_url": "Ctrl+U",
    "quit": "Ctrl+Q",
    "speed_up": "Q",          # Speed up (Q key)
    "speed_down": "A",        # Speed down (A key)
    "speed_normal": "\\",
    "repeat": "R",
    "shuffle": "H",
    "a_point": "",
    "b_point": "",
    "clear_loop": "",
    "subtitle_sync_up": "Ctrl+Up",
    "subtitle_sync_down": "Ctrl+Down",
    # Alt+Up/Down activates the Windows menu bar, so the audio-sync keys use
    # Ctrl+Shift+Up/Down instead (safe and unambiguous).
    "audio_sync_up": "Ctrl+Shift+Up",
    "audio_sync_down": "Ctrl+Shift+Down",
    "audio_track": "",
    "audio_delay": "",
    "equalizer": "",
    "aspect_ratio": "",
    "crop": "",
    "zoom": "",
    "subtitle_track": "",
    "subtitle_delay": "",
    "load_subtitle": "",
    "ab_loop": "",
    "snapshot": "",
    "playlist_manager": "",
    "theme_dark": "",
    "theme_light": "",
    "high_contrast": "",
    "shortcuts": "",
    "about": "",
    "announce_time": "Ctrl+B",  # Time announcement
}