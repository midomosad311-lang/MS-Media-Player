"""
Application Core - Main application controller
"""

from pathlib import Path
from typing import List, Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject
from core.config import ConfigManager
from settings.settings_manager import SettingsManager
from i18n.translation_manager import TranslationManager
from accessibility.accessibility_manager import AccessibilityManager
from media.media_engine import MediaEngine
from media.playlist_manager import PlaylistManager, RepeatMode
from media.bookmark_manager import BookmarkManager
from ui.windows.main_window import MainWindow


class MediaPlayerApplication(QObject):
    """Main application controller"""

    def __init__(self, app: QApplication, config_manager: ConfigManager,
                 settings_manager: SettingsManager, translation_manager: TranslationManager,
                 accessibility_manager: AccessibilityManager):
        super().__init__()
        self.app = app
        self.config = config_manager
        self.settings = settings_manager
        self.translation = translation_manager
        self.accessibility = accessibility_manager

        # Core components
        self.media_engine = MediaEngine(settings_manager)
        self.playlist_manager = PlaylistManager(settings_manager)
        self.bookmark_manager = BookmarkManager(settings_manager)

        # Windows management
        self.windows: List[MainWindow] = []
        self.window_counter = 0

        # Connect signals
        self._connect_signals()
        # Note: Global shortcuts are registered in register_shortcuts() which must be called after QApplication is created

        # Connect cleanup to application aboutToQuit
        self.app.aboutToQuit.connect(self._cleanup)

    def _connect_signals(self):
        """Connect core signals"""
        # Media engine signals
        self.media_engine.state_changed.connect(self._on_state_changed)
        self.media_engine.position_changed.connect(self._on_position_changed)
        self.media_engine.duration_changed.connect(self._on_duration_changed)
        self.media_engine.volume_changed.connect(self._on_volume_changed)
        self.media_engine.muted_changed.connect(self._on_muted_changed)
        self.media_engine.speed_changed.connect(self._on_speed_changed)
        self.media_engine.error_occurred.connect(self._on_error)
        self.media_engine.media_loaded.connect(self._on_media_loaded)
        self.media_engine.media_ended.connect(self._on_media_ended)

        # Playlist signals
        self.playlist_manager.playlist_changed.connect(self._on_playlist_changed)
        self.playlist_manager.current_index_changed.connect(self._on_current_index_changed)

        # Settings signals
        self.settings.theme_changed.connect(self._on_theme_changed)
        self.settings.settings_changed.connect(self._on_settings_changed)

        # Translation signals
        self.translation.language_changed.connect(self._on_language_changed)

        # Accessibility announcements - speak to the screen reader.
        self.accessibility.announce_requested.connect(self._on_announce_requested)

    def _on_announce_requested(self, message: str):
        """Deliver an accessibility announcement to the screen reader.

        Uses Qt's dedicated announcement event, which NVDA / Narrator / other
        Windows screen readers speak.  The active window is used as the event
        source; the message is also mirrored to the status bar so sighted
        users see it.
        """
        if not message:
            return
        window = self._active_window() or (self.windows[-1] if self.windows else None)
        try:
            from PySide6.QtGui import QAccessible, QAccessibleAnnouncementEvent
            if window is not None:
                event = QAccessibleAnnouncementEvent(window, message)
                try:
                    event.setPoliteness(QAccessible.AnnouncementPoliteness.Polite)
                except Exception:
                    pass
                QAccessible.updateAccessibility(event)
        except Exception:
            # Fall back silently if the announcement API is unavailable.
            pass
        if window is not None:
            try:
                window.statusBar().showMessage(message, 4000)
            except Exception:
                pass

    def register_shortcuts(self):
        """Register global keyboard shortcuts - must be called after QApplication is created.

        The shortcuts are (re)installed on every player window so they keep
        working in all modes - including fullscreen, where the menu bar is
        hidden.
        """
        from accessibility.accessibility_manager import STANDARD_SHORTCUTS

        # Predefined speed steps
        self._speed_steps = [0.25, 0.50, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

        def speed_up():
            engine = self._current_engine()
            current = engine.get_speed()
            next_speed = next((s for s in self._speed_steps if s > current), 4.0)
            engine.set_speed(next_speed)
            self.accessibility.announce(self.tr("Speed: {0}x").format(next_speed))

        def speed_down():
            engine = self._current_engine()
            current = engine.get_speed()
            prev_speed = next((s for s in reversed(self._speed_steps) if s < current), 0.25)
            engine.set_speed(prev_speed)
            self.accessibility.announce(self.tr("Speed: {0}x").format(prev_speed))

        def volume_up():
            engine = self._current_engine()
            volume = min(100, engine.get_volume() + 5)
            engine.set_volume(volume)
            self.accessibility.announce(self.tr("Volume: {0}%").format(volume))

        def volume_down():
            engine = self._current_engine()
            volume = max(0, engine.get_volume() - 5)
            engine.set_volume(volume)
            self.accessibility.announce(self.tr("Volume: {0}%").format(volume))

        def toggle_mute():
            engine = self._current_engine()
            engine.toggle_mute()
            self.accessibility.announce(
                self.tr("Muted") if engine.is_muted() else self.tr("Unmuted")
            )

        def seek(delta: float):
            self._current_engine().seek_relative(delta)
            self._announce_position_brief()

        def play_pause():
            """Space: play/pause; when the media has finished, replay it.

            The active window owns the logic (it knows the playlist and the
            "Auto-play Next" setting): when a next item exists and the setting
            is on, Space advances to it; otherwise the current file restarts
            from the very beginning.  It must never just re-report the end.
            """
            window = self._active_window()
            if window is not None and hasattr(window, "toggle_play_pause"):
                window.toggle_play_pause()
                return
            engine = self._current_engine()
            if engine is not None:
                engine.toggle_play_pause()

        def announce_time():
            self._announce_current_time()

        def play_next():
            window = self._active_window()
            if window:
                window.play_next()

        def play_previous():
            window = self._active_window()
            if window:
                window.play_previous()

        def toggle_playlist():
            window = self._active_window()
            if window:
                window.toggle_playlist()

        def toggle_fullscreen():
            window = self._active_window()
            if window:
                window.toggle_fullscreen()

        def toggle_repeat():
            # Route through the window's control panel so the button state,
            # the screen-reader announcement and the playlist mode all stay in
            # sync (a bare playlist toggle left the UI stale, which is why the
            # R shortcut used to look like it did nothing).
            window = self._active_window()
            if window is not None:
                window.toggle_repeat()
            else:
                playlist = self._current_playlist()
                if playlist is not None:
                    playlist.toggle_repeat()

        def toggle_shuffle():
            window = self._active_window()
            if window is not None:
                window.toggle_shuffle()
            else:
                playlist = self._current_playlist()
                if playlist is not None:
                    playlist.toggle_shuffle()

        def subtitle_sync_up():
            engine = self._current_engine()
            ms = engine.adjust_subtitle_delay(50)
            self.accessibility.announce(self.tr("Subtitle delay: {0} ms").format(ms))

        def subtitle_sync_down():
            engine = self._current_engine()
            ms = engine.adjust_subtitle_delay(-50)
            self.accessibility.announce(self.tr("Subtitle delay: {0} ms").format(ms))

        def audio_sync_up():
            engine = self._current_engine()
            s = engine.get_audio_sync() + 1
            engine.set_audio_sync(s)
            self.accessibility.announce(self.tr("Audio delay: {0} s").format(s))

        def audio_sync_down():
            engine = self._current_engine()
            s = engine.get_audio_sync() - 1
            engine.set_audio_sync(s)
            self.accessibility.announce(self.tr("Audio delay: {0} s").format(s))

        # (key sequence, callback, shortcut id)
        self._shortcut_specs = [
            (STANDARD_SHORTCUTS["play_pause"], play_pause, "play_pause"),
            (STANDARD_SHORTCUTS["stop"], lambda: self._current_engine().stop(), "stop"),
            (STANDARD_SHORTCUTS["next"], play_next, "next"),
            (STANDARD_SHORTCUTS["previous"], play_previous, "previous"),
            (STANDARD_SHORTCUTS["forward"], lambda: seek(self.settings.get_seek_interval()), "forward"),
            (STANDARD_SHORTCUTS["backward"], lambda: seek(-self.settings.get_seek_interval()), "backward"),
            (STANDARD_SHORTCUTS["forward_long"], lambda: seek(60), "forward_long"),
            (STANDARD_SHORTCUTS["backward_long"], lambda: seek(-60), "backward_long"),
            (STANDARD_SHORTCUTS["volume_up"], volume_up, "volume_up"),
            (STANDARD_SHORTCUTS["volume_down"], volume_down, "volume_down"),
            (STANDARD_SHORTCUTS["mute"], toggle_mute, "mute"),
            (STANDARD_SHORTCUTS["fullscreen"], toggle_fullscreen, "fullscreen"),
            (STANDARD_SHORTCUTS["playlist"], toggle_playlist, "playlist"),
            ("Q", speed_up, "speed_up"),
            ("A", speed_down, "speed_down"),
            (STANDARD_SHORTCUTS["speed_normal"], lambda: self._current_engine().set_speed(1.0), "speed_normal"),
            (STANDARD_SHORTCUTS["repeat"], toggle_repeat, "repeat"),
            (STANDARD_SHORTCUTS["shuffle"], toggle_shuffle, "shuffle"),
            (STANDARD_SHORTCUTS["subtitle_sync_up"], subtitle_sync_up, "subtitle_sync_up"),
            (STANDARD_SHORTCUTS["subtitle_sync_down"], subtitle_sync_down, "subtitle_sync_down"),
            (STANDARD_SHORTCUTS["audio_sync_up"], audio_sync_up, "audio_sync_up"),
            (STANDARD_SHORTCUTS["audio_sync_down"], audio_sync_down, "audio_sync_down"),
            (STANDARD_SHORTCUTS["open_file"], self._open_file_dialog, "open_file"),
            (STANDARD_SHORTCUTS["open_url"], self._open_url_dialog, "open_url"),
            (STANDARD_SHORTCUTS["settings"], self._show_settings, "settings"),
            (STANDARD_SHORTCUTS["quit"], self.app.quit, "quit"),
            ("Ctrl+B", announce_time, "announce_time"),
            # Letter aliases for next/previous so both the documented
            # Ctrl+Left/Right and the single-key N/P work.
            ("N", play_next, "next"),
            ("P", play_previous, "previous"),
        ]

        # Install now in case a window already exists.
        for window in self.windows:
            self._install_shortcuts(window)

    def _install_shortcuts(self, window: "MainWindow"):
        """Install the global shortcuts, parented to a real window widget.

        WindowShortcut shortcuts created without a widget parent never fire,
        so each window owns its own copies (active while that window is
        active - including fullscreen).
        """
        if not hasattr(self, "_shortcut_specs"):
            return
        for key, callback, name in self._shortcut_specs:
            self.accessibility.register_shortcut(key, callback, name, context=window)

    def _active_window(self) -> Optional[MainWindow]:
        """Return the currently active player window (or the first one)."""
        active = self.app.activeWindow()
        if isinstance(active, MainWindow):
            return active
        return self.windows[0] if self.windows else None

    def _current_engine(self):
        window = self._active_window()
        return window.media_engine if window and window.media_engine else self.media_engine

    def _current_playlist(self):
        window = self._active_window()
        return window.playlist_manager if window and window.playlist_manager else self.playlist_manager

    def _toggle_fullscreen_active_window(self):
        """Toggle fullscreen for active window"""
        active_window = self.app.activeWindow()
        if isinstance(active_window, MainWindow):
            active_window.toggle_fullscreen()

    def _open_file_dialog(self):
        """Open file dialog in active window"""
        active_window = self.app.activeWindow()
        if isinstance(active_window, MainWindow):
            active_window.open_file_dialog()

    def _open_url_dialog(self):
        """Open URL dialog in active window"""
        active_window = self.app.activeWindow()
        if isinstance(active_window, MainWindow):
            active_window.open_url_dialog()

    def _show_settings(self):
        """Show settings dialog in active window"""
        active_window = self.app.activeWindow()
        if isinstance(active_window, MainWindow):
            active_window.show_settings()

    def create_window(self, file_path: str = None) -> MainWindow:
        """Create new player window"""
        self.window_counter += 1
        
        # Create engine and playlist for this window
        if not self.windows:
            # First window - use shared engine and playlist
            media_engine = self.media_engine
            playlist_manager = self.playlist_manager
        else:
            # Additional windows - create new engine and playlist
            media_engine = MediaEngine(self.settings)
            playlist_manager = PlaylistManager(self.settings)
        
        window = MainWindow(
            app_controller=self,
            window_id=f"window_{self.window_counter}",
            media_engine=media_engine,
            playlist_manager=playlist_manager,
            bookmark_manager=self.bookmark_manager,
        )

        # Connect signals for additional windows
        if self.windows:
            self._connect_window_signals(window)

        self.windows.append(window)

        # Restore geometry
        geometry = self.settings.get_window_geometry(window.window_id)
        if geometry:
            window.restoreGeometry(geometry)

        # Load file if provided (auto-adds the rest of its folder to the queue)
        if file_path:
            window.open_media_file(file_path)

        window.show()

        # Install global shortcuts on this window so they work in every mode,
        # including fullscreen where the menu bar is hidden.
        self._install_shortcuts(window)

        return window

    def _connect_window_signals(self, window: MainWindow):
        """Connect signals for additional window"""
        engine = window.media_engine
        playlist = window.playlist_manager

        engine.state_changed.connect(window._on_state_changed)
        engine.position_changed.connect(window._on_position_changed)
        engine.duration_changed.connect(window._on_duration_changed)
        engine.volume_changed.connect(window._on_volume_changed)
        engine.muted_changed.connect(window._on_muted_changed)
        engine.speed_changed.connect(window._on_speed_changed)
        engine.error_occurred.connect(window._on_error)
        engine.media_loaded.connect(window._on_media_loaded)
        engine.media_ended.connect(window._on_media_ended)

        # Connect video widget to media engine for video output
        if window.video_widget:
            engine.set_video_widget(window.video_widget)

        playlist.playlist_changed.connect(window._on_playlist_changed)
        playlist.current_index_changed.connect(window._on_current_index_changed)

    def close_window(self, window: MainWindow):
        """Close a player window"""
        if window in self.windows:
            # Save geometry
            self.settings.save_window_geometry(window.window_id, window.saveGeometry())

            # Cleanup engine if separate
            if window.media_engine != self.media_engine:
                window.media_engine.cleanup()

            self.windows.remove(window)
            window.deleteLater()

            # Quit app if no windows left
            if not self.windows:
                self.app.quit()

    def _cleanup(self):
        """Cleanup resources on application exit"""
        # Remember the session (playlist / file / position) *before* the media
        # engine is torn down so it can be restored when the user asks for it.
        try:
            self._save_last_session()
        except Exception:
            pass

        # Flush any pending (debounced) settings to disk
        try:
            self.config.flush()
        except Exception:
            pass

        # Cleanup main media engine
        if self.media_engine:
            self.media_engine.cleanup()
        
        # Cleanup additional window media engines
        for window in self.windows:
            if window.media_engine and window.media_engine != self.media_engine:
                window.media_engine.cleanup()

    def handle_command_line_args(self, args: list):
        """Handle command-line arguments (file paths from file associations)"""
        # Filter valid media files from arguments
        media_extensions = {
            '.mp4', '.avi', '.mkv', '.mov', '.mp3', '.wav', '.flac', '.ogg', '.m4a', '.wma',
            '.3gp', '.webm', '.ts', '.m3u', '.m3u8', '.wmv', '.mpg', '.mpeg', '.vob', '.ogv',
            '.m2ts', '.mts', '.mxf', '.divx', '.xvid', '.rm', '.rmvb', '.asf', '.amv', '.mtv',
            '.drc', '.ifo', '.vro', '.tp', '.trp', '.f4v', '.f4p', '.f4a', '.f4b'
        }
        
        file_paths = []
        for arg in args:
            path = Path(arg)
            if path.exists() and path.suffix.lower() in media_extensions:
                file_paths.append(str(path))
            elif path.exists() and path.is_file():
                # Allow any file if explicitly passed (user might have non-standard extensions)
                file_paths.append(str(path))
        
        # Store for later use in run()
        self._command_line_files = file_paths

    def _startup_restore(self):
        """Return ``(file_path, resume_position)`` for the "On Startup" setting.

        The behaviour defaults to ``"empty"``: a freshly installed player must
        never silently re-associate itself with a file that happened to be open
        in a previous session.
        """
        try:
            behavior = self.settings.get_startup_behavior()
        except Exception:
            behavior = SettingsManager.STARTUP_EMPTY
        if behavior == SettingsManager.STARTUP_EMPTY:
            return ("", 0.0)

        session = self.settings.get_last_session() or {}
        file_path = session.get("file") or ""
        if not file_path or not Path(file_path).exists():
            # Fall back to the most recent file that still exists so a deleted
            # entry can never make the player start on a broken file.
            recent = self.settings.get_recent_files()
            file_path = next((f for f in recent if f and Path(f).exists()), "")
        if not file_path:
            return ("", 0.0)

        position = 0.0
        if behavior == SettingsManager.STARTUP_RESUME:
            try:
                position = float(session.get("position", 0.0) or 0.0)
            except (TypeError, ValueError):
                position = 0.0
        return (file_path, position)

    def _save_last_session(self):
        """Persist the current session so it can be restored on request."""
        try:
            window = self._active_window()
            playlist = window.playlist_manager if window else self.playlist_manager
            engine = window.media_engine if window else self.media_engine
            if playlist is None:
                return
            paths = [item.get("path", "") for item in playlist.get_items()]
            paths = [p for p in paths if p]
            current = playlist.get_current_path() or ""
            position = 0.0
            if engine is not None:
                try:
                    position = float(engine.get_position() or 0.0)
                except Exception:
                    position = 0.0
            self.settings.set_last_session({
                "file": current,
                "playlist": paths,
                "index": playlist.current_index,
                "position": position,
            })
        except Exception:
            pass

    def run(self) -> int:
        """Run application"""
        # Create initial window with command-line file(s) if provided
        if hasattr(self, '_command_line_files') and self._command_line_files:
            window = self.create_window()
            # Opening the first file also pulls in every compatible media file
            # from its folder; additional files (possibly from other folders)
            # are grouped in as well, without duplicates.
            window.open_media_files(self._command_line_files)
        else:
            startup_file, resume_position = self._startup_restore()
            window = self.create_window(startup_file or None)
            if startup_file and resume_position > 0:
                window.set_resume_position(resume_position)

        return self.app.exec()

    # Signal handlers
    def _on_state_changed(self, state: str):
        pass  # Handled by windows

    def _on_position_changed(self, current: float, total: float):
        # Deliberately does NOT announce on every tick.
        #
        # ``position_changed`` is emitted every 100 ms.  Announcing each value
        # floods the screen reader with "Position ... percent" and makes the
        # whole app unusable with a screen reader.  The seek bar now speaks
        # only while it holds focus (see ControlPanel), and Ctrl+B announces
        # the elapsed / total / remaining time on demand.
        return

    def _on_duration_changed(self, duration: float):
        pass

    def _on_volume_changed(self, volume: int):
        pass

    def _on_muted_changed(self, muted: bool):
        pass

    def _on_speed_changed(self, speed: float):
        pass

    def _on_error(self, error: str):
        self.accessibility.announce(f"Error: {error}", priority=True)

    def _on_media_loaded(self, path: str):
        self.settings.add_recent_file(path)
        # The owning MainWindow announces the media that is starting (it knows
        # the current UI language), so nothing is announced here.

    def _on_media_ended(self):
        # Guard against the same "ended" notification firing repeatedly in a
        # tight loop: an unguarded loop reloaded the same file over and over
        # and made the whole app appear to freeze.
        import time
        now = time.monotonic()
        if now - getattr(self, "_last_media_ended_at", 0.0) < 1.0:
            return
        self._last_media_ended_at = now

        window = self._active_window()
        engine = window.media_engine if window and window.media_engine else self.media_engine
        playlist = window.playlist_manager if window and window.playlist_manager else self.playlist_manager
        if engine is None or playlist is None:
            return

        # Repeat the current track if repeat-one is enabled
        if playlist.repeat_mode == RepeatMode.ONE:
            current = playlist.get_current_path()
            if current:
                engine.load_file(current)
                engine.play()
                return

        # Auto-play the next track when "Auto-play Next" is enabled.  When it is
        # disabled the file simply stops, so pressing Space can replay it.
        try:
            auto_next = self.settings.get_autoplay_next()
        except Exception:
            auto_next = True
        if not auto_next:
            return

        next_path = playlist.next()
        if next_path:
            engine.load_file(next_path)
            engine.play()

    def _on_playlist_changed(self):
        pass

    def _on_current_index_changed(self, index: int):
        pass

    def _on_theme_changed(self, theme: str):
        for window in self.windows:
            window.apply_theme()

    def _on_settings_changed(self, key: str, value):
        # Live language switching: when the language changes (e.g. from the
        # Settings dialog) immediately swap the Qt translator instead of
        # waiting for the next start-up.
        if key == "language" and value:
            # Guard against recursion: TranslationManager.apply_language()
            # itself calls settings.set_language(), which re-emits this signal.
            if value != self.translation.get_current_language():
                self.translation.apply_language(value)

    def _on_language_changed(self, language: str):
        # Apply the right-to-left / left-to-right layout direction globally so
        # every (re)created dialog follows the selected language.
        try:
            from PySide6.QtCore import Qt
            direction = Qt.RightToLeft if language == "ar" else Qt.LeftToRight
            self.app.setLayoutDirection(direction)
        except Exception:
            pass
        for window in self.windows:
            window.retranslate_ui()
        # Retranslate any open dialogs as well (Settings, About, ...).
        try:
            from PySide6.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                if widget is None:
                    continue
                retranslate = getattr(widget, "retranslate", None)
                if callable(retranslate) and widget not in self.windows:
                    try:
                        retranslate()
                    except Exception:
                        pass
        except Exception:
            pass

    def _announce_current_time(self):
        """Announce current playback time with total, elapsed, and remaining"""
        # Use the same robust lookup as the other shortcuts so this works even
        # when QApplication.activeWindow() momentarily reports None.
        active_window = self._active_window()
        if not active_window or not active_window.media_engine:
            return

        engine = active_window.media_engine
        current = engine.get_time()
        total = engine.get_duration()

        if total <= 0:
            self.accessibility.announce(self.tr("No media loaded"))
            return

        remaining = total - current

        lang = getattr(self.translation, "current_language", "en")

        if lang == "ar":
            def format_time_detailed(seconds: float) -> str:
                """Format time as hours, minutes, seconds in Arabic"""
                if seconds < 0:
                    seconds = 0
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)

                parts = []
                if hours > 0:
                    parts.append(f"{hours} ساعة" if hours == 1 else f"{hours} ساعات")
                if minutes > 0:
                    parts.append(f"{minutes} دقيقة" if minutes == 1 else f"{minutes} دقائق")
                if secs > 0 or not parts:
                    parts.append(f"{secs} ثانية" if secs == 1 else f"{secs} ثوانٍ")
                return " و ".join(parts)

            message = (
                f"{format_time_detailed(total)}، "
                f"انقضى منها {format_time_detailed(current)}، "
                f"ومتبقي {format_time_detailed(remaining)}"
            )
        else:
            def fmt(seconds: float) -> str:
                seconds = max(0, int(seconds))
                return f"{seconds // 60}:{seconds % 60:02d}"

            message = (
                f"{fmt(total)} total, "
                f"{fmt(current)} elapsed, "
                f"{fmt(remaining)} remaining"
            )

        self.accessibility.announce(message, priority=True)

    @staticmethod
    def _format_time_words(seconds: float, lang: str) -> str:
        """Format a duration as spoken words.

        Arabic uses its real singular / dual / plural forms so the phrasing is
        natural ("ساعتان", "3 ساعات", "59 دقيقة") instead of a run of digits.
        """
        try:
            total = int(round(max(0.0, float(seconds))))
        except Exception:
            total = 0
        hours, rem = divmod(total, 3600)
        minutes, secs = divmod(rem, 60)

        if str(lang).startswith("ar"):
            def unit(n, one, two, few, many):
                if n == 0:
                    return ""
                if n == 1:
                    return one
                if n == 2:
                    return two
                if 3 <= n <= 10:
                    return f"{n} {few}"
                return f"{n} {many}"

            parts = [
                unit(hours, "ساعة", "ساعتان", "ساعات", "ساعة"),
                unit(minutes, "دقيقة", "دقيقتان", "دقائق", "دقيقة"),
                unit(secs, "ثانية", "ثانيتان", "ثوانٍ", "ثانية"),
            ]
            parts = [p for p in parts if p]
            return " و".join(parts) if parts else "0 ثانية"

        parts = []
        if hours:
            parts.append(f"{hours} hour" + ("s" if hours != 1 else ""))
        if minutes:
            parts.append(f"{minutes} minute" + ("s" if minutes != 1 else ""))
        if secs or not parts:
            parts.append(f"{secs} second" + ("s" if secs != 1 else ""))
        return " ".join(parts)

    def _announce_position_brief(self):
        """Announce the position after seeking, in full spoken words.

        The old "M:SS / M:SS" formatting was read out by screen readers as a
        run of meaningless digits; the requirement is a natural phrase such as
        "50 minutes and 0 seconds of 5 hours" (elapsed, then total).  Works
        whether the file is playing, paused or stopped.
        """
        window = self._active_window()
        engine = window.media_engine if window and window.media_engine else self.media_engine
        if not engine:
            return
        total = engine.get_duration()
        if total <= 0:
            self.accessibility.announce(self.tr("No media loaded"), priority=True)
            return

        remaining = max(0.0, total - engine.get_time())
        lang = getattr(self.translation, "current_language", "en")
        if str(lang).startswith("ar"):
            message = (f"{self._format_time_words(engine.get_time(), lang)} "
                       f"من {self._format_time_words(total, lang)}، "
                       f"ويتبقى {self._format_time_words(remaining, lang)}")
        else:
            message = (f"{self._format_time_words(engine.get_time(), lang)} elapsed of "
                       f"{self._format_time_words(total, lang)}, "
                       f"{self._format_time_words(remaining, lang)} remaining")
        self.accessibility.announce(message, priority=True)