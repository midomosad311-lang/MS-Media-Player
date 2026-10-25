"""
Main Window - Primary player window
"""

from pathlib import Path
import os
import re
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFileDialog, QMessageBox,
    QInputDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from core.app_meta import APP_NAME
from media.media_engine import MediaEngine, PlaybackState
from media.playlist_manager import PlaylistManager
from media.bookmark_manager import BookmarkManager
from media.subtitle_manager import SubtitleManager, SyncMode
from media.youtube_handler import YouTubeStreamHandler, StreamQuality
from accessibility.accessibility_manager import STANDARD_SHORTCUTS
from ui.widgets.video_widget import VideoWidget
from ui.widgets.control_panel import ControlPanel
from ui.widgets.playlist_widget import PlaylistWidget
from ui.widgets.subtitle_settings_panel import SubtitleSettingsPanel
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.url_dialog import UrlDialog
from ui.dialogs.subtitle_options_dialog import SubtitleOptionsDialog, SubtitleExportDialog


class MainWindow(QMainWindow):
    """Main player window"""

    def __init__(self, app_controller, window_id: str,
                 media_engine: MediaEngine = None,
                 playlist_manager: PlaylistManager = None,
                 bookmark_manager: BookmarkManager = None):
        super().__init__()
        self.app_controller = app_controller
        self.window_id = window_id
        self.media_engine = media_engine
        self.playlist_manager = playlist_manager
        self.bookmark_manager = bookmark_manager
        self.settings = app_controller.settings
        self.translation = app_controller.translation
        self.accessibility = app_controller.accessibility
        self._menu_actions = []  # Keep references to menu actions to prevent GC

        # Initialize subtitle manager
        self.subtitle_manager = SubtitleManager(app_controller.settings if hasattr(app_controller, 'settings') else None)
        
        # Initialize YouTube handler
        self.youtube_handler = YouTubeStreamHandler()
        
        # YouTube URL regex patterns
        self.youtube_patterns = [
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/',
            r'(https?://)?(www\.)?youtube\.com/(watch\?v=|embed/|v/|shorts/)',
            r'(https?://)?youtu\.be/',
        ]

        self._setup_ui()
        self._setup_shortcuts()
        self._connect_signals()
        self._apply_accessibility()

        # Position update timer
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position_display)
        self.position_timer.setInterval(500)

        # Window state
        self.fullscreen = False
        self.previous_geometry = None
        
        # Subtitle settings panel
        self.subtitle_settings_panel = None

    def _setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 700)
        self.setMinimumSize(800, 500)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Menu bar
        self._create_menu_bar()

        # Video widget - takes most of the space
        self.video_widget = VideoWidget(self.media_engine)
        layout.addWidget(self.video_widget, 1)

        # Subtitle settings panel (initially hidden)
        self.subtitle_settings_panel = SubtitleSettingsPanel(self.subtitle_manager)
        self.subtitle_settings_panel.setVisible(False)
        self.subtitle_settings_panel.sync_mode_changed.connect(self._on_sync_mode_changed)
        self.subtitle_settings_panel.offset_changed.connect(self._on_subtitle_offset_changed)
        self.subtitle_settings_panel.visibility_toggled.connect(self._on_subtitle_visibility_changed)
        self.subtitle_settings_panel.subtitle_selected.connect(self._on_subtitle_selected)
        self.subtitle_settings_panel.export_requested.connect(self._on_export_subtitles)
        layout.addWidget(self.subtitle_settings_panel)

        # Control panel (initially hidden until media is loaded)
        self.control_panel = ControlPanel(self.media_engine, self.playlist_manager, self.settings, self.accessibility)
        self.control_panel.setVisible(False)
        # Reflect any restored repeat / shuffle state on the buttons.
        self.control_panel.sync_playlist_toggles()
        layout.addWidget(self.control_panel)

        # Playlist widget (initially hidden)
        self.playlist_widget = PlaylistWidget(self.playlist_manager, self.accessibility)
        self.playlist_widget.setVisible(False)
        layout.addWidget(self.playlist_widget)

        # Make the seek bar the first independent Tab stop after the video
        # area, so a screen-reader user reaches the time description (file
        # name, total duration, elapsed / remaining) with a single Tab.
        QWidget.setTabOrder(self.video_widget, self.control_panel.progress_slider)

        # Status bar
        self.statusBar().showMessage(self.tr("Ready"))

        # Set initial focus to video widget
        self.video_widget.setFocus()

    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        menubar.clear()  # Clear existing menus for retranslation
        self._menu_actions.clear()  # Clear old action references

        # File menu
        file_menu = menubar.addMenu(self.tr("&File"))
        self._add_action(file_menu, self.tr("&Open File..."), "Ctrl+O", self.open_file_dialog, "open_file")
        self._add_action(file_menu, self.tr("Open &URL..."), "Ctrl+U", self.open_url_dialog, "open_url")
        file_menu.addSeparator()
        self._add_action(file_menu, self.tr("Open &YouTube Stream..."), "Ctrl+Y", self._show_youtube_dialog, "open_youtube")
        file_menu.addSeparator()
        self._add_action(file_menu, self.tr("&Playlist..."), "Ctrl+L", self.toggle_playlist, "playlist")
        file_menu.addSeparator()
        self._add_action(file_menu, self.tr("E&xit"), "Ctrl+Q", self.close, "quit")

        # Playback menu
        playback_menu = menubar.addMenu(self.tr("&Playback"))
        self._add_action(playback_menu, self.tr("&Play/Pause"), "Space", self.toggle_play_pause, "play_pause")
        self._add_action(playback_menu, self.tr("&Stop"), "S", self.media_engine.stop, "stop")
        playback_menu.addSeparator()
        self._add_action(playback_menu, self.tr("&Next"), "Ctrl+Right", self.play_next, "next")
        self._add_action(playback_menu, self.tr("&Previous"), "Ctrl+Left", self.play_previous, "previous")
        playback_menu.addSeparator()
        self._add_action(playback_menu, self.tr("Forward"), "Right", lambda: self.media_engine.seek_relative(self.settings.get_seek_interval()), "forward")
        self._add_action(playback_menu, self.tr("Backward"), "Left", lambda: self.media_engine.seek_relative(-self.settings.get_seek_interval()), "backward")
        playback_menu.addSeparator()
        self._add_action(playback_menu, self.tr("Speed Up"), "]", lambda: self.media_engine.set_speed(min(4.0, self.media_engine.get_speed() + 0.25)), "speed_up")
        self._add_action(playback_menu, self.tr("Speed Down"), "[", lambda: self.media_engine.set_speed(max(0.25, self.media_engine.get_speed() - 0.25)), "speed_down")
        self._add_action(playback_menu, self.tr("Normal Speed"), "\\", lambda: self.media_engine.set_speed(1.0), "speed_normal")

        # Audio menu
        audio_menu = menubar.addMenu(self.tr("&Audio"))
        self._add_action(audio_menu, self.tr("Mute"), "M", self.media_engine.toggle_mute, "mute")
        self._add_action(audio_menu, self.tr("Volume Up"), "Up", lambda: self.media_engine.set_volume(self.media_engine.get_volume() + 5), "volume_up")
        self._add_action(audio_menu, self.tr("Volume Down"), "Down", lambda: self.media_engine.set_volume(self.media_engine.get_volume() - 5), "volume_down")
        audio_menu.addSeparator()
        self._add_action(audio_menu, self.tr("Audio Track"), "", self._show_audio_tracks, "audio_track")
        self._add_action(audio_menu, self.tr("Audio Delay..."), "", self._adjust_audio_delay, "audio_delay")
        audio_menu.addSeparator()
        self._add_action(audio_menu, self.tr("Equalizer..."), "", self._show_equalizer, "equalizer")

        # Video menu
        video_menu = menubar.addMenu(self.tr("&Video"))
        self._add_action(video_menu, self.tr("Fullscreen"), "F", self.toggle_fullscreen, "fullscreen")
        video_menu.addSeparator()
        self._add_action(video_menu, self.tr("Aspect Ratio"), "", self._set_aspect_ratio, "aspect_ratio")
        self._add_action(video_menu, self.tr("Crop"), "", self._set_crop, "crop")
        self._add_action(video_menu, self.tr("Zoom"), "", self._set_zoom, "zoom")
        video_menu.addSeparator()
        self._add_action(video_menu, self.tr("Subtitle Track"), "", self._show_subtitle_tracks, "subtitle_track")
        video_menu.addSeparator()
        self._add_action(video_menu, self.tr("Subtitle Delay..."), "", self._adjust_subtitle_delay, "subtitle_delay")
        self._add_action(video_menu, self.tr("Load Subtitle..."), "", self._load_subtitle, "load_subtitle")

        # Subtitle menu (new)
        subtitle_menu = menubar.addMenu(self.tr("&Subtitles"))
        self._add_action(subtitle_menu, self.tr("Subtitle Options..."), "Ctrl+Shift+S", self._show_subtitle_options, "subtitle_options")
        self._add_action(subtitle_menu, self.tr("Export Subtitles..."), "Ctrl+Shift+E", self._show_subtitle_export, "subtitle_export")
        subtitle_menu.addSeparator()
        self._add_action(subtitle_menu, self.tr("Toggle Subtitles"), "Ctrl+T", lambda: self._toggle_subtitles(), "toggle_subtitles")
        self._add_action(subtitle_menu, self.tr("Subtitle Delay..."), "", self._adjust_subtitle_delay, "subtitle_delay")
        self._add_action(subtitle_menu, self.tr("Load Subtitle..."), "", self._load_subtitle, "load_subtitle")

        # Tools menu
        tools_menu = menubar.addMenu(self.tr("&Tools"))
        self._add_action(tools_menu, self.tr("A-B Loop"), "", self._toggle_ab_loop, "ab_loop")
        self._add_action(tools_menu, self.tr("Take Snapshot"), "", self._take_snapshot, "snapshot")
        tools_menu.addSeparator()
        self._add_action(tools_menu, self.tr("Settings..."), "Ctrl+P", self.show_settings, "settings")
        self._add_action(tools_menu, self.tr("Playlist Manager..."), "", self._show_playlist_manager, "playlist_manager")

        # Bookmarks menu
        bookmarks_menu = menubar.addMenu(self.tr("&Bookmarks"))
        self._add_action(bookmarks_menu, self.tr("Show Bookmarks..."), "Ctrl+Shift+M", self._show_bookmarks, "bookmarks")
        self._add_action(bookmarks_menu, self.tr("Add Bookmark"), "Ctrl+Shift+B", self._add_bookmark_at_current_position, "add_bookmark")

        # View menu
        view_menu = menubar.addMenu(self.tr("&View"))
        self._add_action(view_menu, self.tr("Playlist"), "Ctrl+L", self.toggle_playlist, "playlist")
        view_menu.addSeparator()
        self._add_action(view_menu, self.tr("Dark Theme"), "", lambda: self.settings.set_theme("dark"), "theme_dark")
        self._add_action(view_menu, self.tr("Light Theme"), "", lambda: self.settings.set_theme("light"), "theme_light")
        self._add_action(view_menu, self.tr("High Contrast"), "", lambda: self.settings.set_high_contrast(not self.settings.get_high_contrast()), "high_contrast")

        # Help menu
        help_menu = menubar.addMenu(self.tr("&Help"))
        self._add_action(help_menu, self.tr("Keyboard Shortcuts"), "", self._show_shortcuts, "shortcuts")
        self._add_action(help_menu, self.tr("About"), "", self._show_about, "about")

        # Language submenu
        lang_menu = menubar.addMenu(self.tr("&Language"))
        for code, info in self.translation.get_available_languages().items():
            action = QAction(info["native"], self)
            action.setCheckable(True)
            action.setChecked(code == self.translation.get_current_language())
            action.triggered.connect(lambda checked, c=code: self.translation.apply_language(c))
            lang_menu.addAction(action)

    # Menu actions whose shortcut is also registered as a global QShortcut.
    # Their menu shortcut is shown for discoverability but must NOT be active,
    # otherwise the two bindings become an "ambiguous shortcut" and neither
    # fires. The global QShortcut is the single source of truth (it also keeps
    # working in fullscreen when the menu bar is hidden).
    _GLOBAL_SHORTCUT_NAMES = {
        "play_pause", "stop", "next", "previous", "forward", "backward",
        "forward_long", "backward_long", "volume_up", "volume_down", "mute",
        "fullscreen", "speed_up", "speed_down", "speed_normal", "repeat",
        "shuffle", "open_file", "open_url", "settings", "quit", "playlist",
    }

    def _add_action(self, menu, text, shortcut, callback, accessibility_name):
        """Add action to menu with accessibility"""
        # STANDARD_SHORTCUTS now contains just the key string, not (key, description) tuple
        shortcut_key = STANDARD_SHORTCUTS.get(accessibility_name, shortcut)
        action = self.accessibility.create_accessible_action(
            text, shortcut_key, ""  # No description - accessibility manager creates "name shortcut" format
        )
        if accessibility_name in self._GLOBAL_SHORTCUT_NAMES:
            # Show the shortcut but let the global QShortcut handle activation.
            action.setShortcutContext(Qt.WidgetShortcut)
        action.triggered.connect(callback)
        menu.addAction(action)
        self._menu_actions.append(action)  # Keep reference to prevent GC
        return action

    def _setup_shortcuts(self):
        """Setup window-specific shortcuts"""
        pass  # Global shortcuts handled by app controller

    def _connect_signals(self):
        """Connect media engine signals"""
        if self.media_engine:
            self.media_engine.state_changed.connect(self._on_state_changed)
            self.media_engine.position_changed.connect(self._on_position_changed)
            self.media_engine.duration_changed.connect(self._on_duration_changed)
            self.media_engine.volume_changed.connect(self._on_volume_changed)
            self.media_engine.muted_changed.connect(self._on_muted_changed)
            self.media_engine.speed_changed.connect(self._on_speed_changed)
            self.media_engine.error_occurred.connect(self._on_error)
            self.media_engine.media_loaded.connect(self._on_media_loaded)
            self.media_engine.media_ended.connect(self._on_media_ended)
            # Connect media_ready once here (not in load_file) so it does not
            # accumulate duplicate connections across multiple file loads.
            self.media_engine.media_ready.connect(self._on_media_ready, type=Qt.ConnectionType.QueuedConnection)

            # Connect video widget to media engine for video output
            if self.video_widget:
                self.media_engine.set_video_widget(self.video_widget)

        if self.playlist_manager:
            self.playlist_manager.playlist_changed.connect(self._on_playlist_changed)
            self.playlist_manager.current_index_changed.connect(self._on_current_index_changed)

        if getattr(self, "youtube_handler", None):
            self.youtube_handler.stream_ready.connect(self._on_youtube_stream_ready)
            self.youtube_handler.file_ready.connect(self._on_youtube_file_ready)
            self.youtube_handler.download_progress.connect(self._on_youtube_progress)
            self.youtube_handler.stream_error.connect(self._on_youtube_stream_error)
            self.youtube_handler.subtitles_ready.connect(self._on_youtube_subtitles_ready)

    def _apply_accessibility(self):
        """Apply accessibility settings"""
        # Setup widget accessibility
        self.accessibility.setup_widget_accessibility(
            self.video_widget, self.tr("Video Display"), self.tr("Video playback area")
        )

    def load_file(self, file_path: str, headers: dict = None) -> bool:
        """Load media file (auto-plays when ready).

        ``headers`` is forwarded to the media engine for network streams.
        """
        if not self.media_engine:
            return False

        # media_ready is connected once in _connect_signals(), so no need to
        # (re)connect here - this avoids accumulating duplicate callbacks.
        if self.media_engine.load_file(file_path, headers):
            self.setWindowTitle(f"{Path(file_path).name} - {APP_NAME}")
            # Check if media is already ready (synchronous emission)
            import vlc
            if self.media_engine.media and self.media_engine.media.get_parsed_status() == vlc.MediaParsedStatus.done:
                # Media already parsed, trigger ready handler directly
                self._on_media_ready()
            return True
        return False

    def play_next(self):
        """Play the next track in the playlist (actually loads and plays it)."""
        self._play_relative(next=True)

    def play_previous(self):
        """Play the previous track in the playlist (actually loads and plays it)."""
        self._play_relative(next=False)

    def toggle_play_pause(self):
        """Play / pause, or replay when the media has already finished.

        When the file has ended and "Auto-play Next" is enabled with a
        following item, advance to it; otherwise restart the current file from
        the very beginning.  This is what Space (and the Play button) do.
        """
        engine = self.media_engine
        if engine is None:
            return
        try:
            finished = engine.is_finished()
        except Exception:
            finished = False
        if not finished:
            engine.toggle_play_pause()
            return

        auto_next = True
        try:
            auto_next = bool(self.settings.get_autoplay_next())
        except Exception:
            pass
        if auto_next and self.playlist_manager is not None:
            try:
                next_path = self.playlist_manager.get_next_path()
            except Exception:
                next_path = None
            if next_path:
                self.play_next()
                return
        engine.restart()

    def _play_relative(self, next: bool):
        """Advance the playlist and immediately load + play the resulting file."""
        if not self.playlist_manager:
            return

        if self.playlist_manager.is_empty():
            # No playlist: fall back to single-file behaviour (restart / no-op)
            self.accessibility.announce(self.tr("Playlist is empty"))
            return

        path = self.playlist_manager.next() if next else self.playlist_manager.previous()
        if path:
            self.load_file(path)
        else:
            self.accessibility.announce(
                self.tr("No next file") if next else self.tr("No previous file")
            )

    # Extensions considered "compatible media" when auto-filling a folder.
    MEDIA_EXTENSIONS = {
        '.mp4', '.avi', '.mkv', '.mov', '.mp3', '.wav', '.flac', '.ogg', '.m4a',
        '.wma', '.3gp', '.webm', '.ts', '.m3u8', '.wmv', '.mpg', '.mpeg', '.vob',
        '.ogv', '.m2ts', '.mts', '.mxf', '.divx', '.xvid', '.rm', '.rmvb', '.asf',
        '.mpe', '.amv', '.mtv', '.f4v', '.f4a', '.f4b',
    }

    @staticmethod
    def _collect_media_in_folder(folder):
        """Return the sorted list of compatible media files inside *folder*."""
        try:
            if not folder or not os.path.isdir(folder):
                return []
            media_files = [
                os.path.join(folder, name)
                for name in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, name))
                and os.path.splitext(name)[1].lower() in MainWindow.MEDIA_EXTENSIONS
            ]
            media_files.sort(key=lambda p: os.path.basename(p).lower())
            return media_files
        except Exception as e:
            print(f"Error scanning folder '{folder}': {e}")
            return []

    @staticmethod
    def _norm(path: str) -> str:
        try:
            return os.path.normcase(os.path.abspath(path))
        except Exception:
            return path

    def seed_playlist_from_files(self, file_paths):
        """Populate the playlist with every compatible media file found in the
        folder(s) of *file_paths*.

        Files coming from different folders are grouped together; duplicates
        are removed while preserving folder order.  The first requested file
        becomes the current item so it is the one that plays.
        """
        if not self.playlist_manager:
            return
        ordered = []
        seen = set()
        for fp in file_paths or []:
            if not fp:
                continue
            folder = os.path.dirname(fp) if not str(fp).startswith(('http://', 'https://')) else ""
            for mf in self._collect_media_in_folder(folder):
                key = self._norm(mf)
                if key not in seen:
                    seen.add(key)
                    ordered.append(mf)
            # Always keep the requested file itself (even a non-media extension
            # opened via "All Files"), so the user's choice is never dropped.
            key = self._norm(fp)
            if key not in seen:
                seen.add(key)
                ordered.append(fp)

        self.playlist_manager.clear()

        # Remember the folder that seeded this *default* playlist so the queue
        # is clearly identified and Next / Previous walk through it.  Set it
        # before the items are added so the widget shows the name immediately.
        folders = []
        for fp in ordered:
            if str(fp).startswith(('http://', 'https://', 'file://')):
                continue
            d = os.path.dirname(fp)
            if d and d not in folders:
                folders.append(d)
        if len(folders) == 1:
            folder_name = os.path.basename(folders[0].rstrip('\\/')) or folders[0]
        elif len(folders) > 1:
            folder_name = self.tr("{0} folders").format(len(folders))
        else:
            folder_name = ""
        self.playlist_manager.set_folder_name(folder_name)

        for path in ordered:
            self.playlist_manager.add_file(path)

        if file_paths:
            target = self._norm(file_paths[0])
            for i, item in enumerate(self.playlist_manager.get_items()):
                if self._norm(item["path"]) == target:
                    self.playlist_manager.set_current_index(i)
                    break

        if folder_name and ordered:
            try:
                self.accessibility.announce(
                    self.tr("Default playlist: {0} ({1} items)").format(folder_name, len(ordered))
                )
            except Exception:
                pass

    def _add_folder_to_playlist(self, folder, selected_file):
        """Backward-compatible wrapper: seed from a folder + selected file."""
        files = self._collect_media_in_folder(folder)
        if selected_file:
            files = [selected_file] + [f for f in files if self._norm(f) != self._norm(selected_file)]
        self.seed_playlist_from_files([selected_file] if selected_file else files)

    def open_media_file(self, file_path: str):
        """Open a single media file, auto-adding the rest of its folder."""
        if not file_path:
            return
        try:
            folder = os.path.dirname(file_path)
            if folder and os.path.isdir(folder):
                self.settings.set_last_open_dir(folder)
        except Exception:
            pass
        self.seed_playlist_from_files([file_path])
        self.load_file(file_path)

    def open_media_files(self, file_paths):
        """Open several media files (e.g. multi-select), auto-adding folders."""
        paths = [p for p in (file_paths or []) if p]
        if not paths:
            return
        try:
            folder = os.path.dirname(paths[0])
            if folder and os.path.isdir(folder):
                self.settings.set_last_open_dir(folder)
        except Exception:
            pass
        self.seed_playlist_from_files(paths)
        self.load_file(paths[0])

    def set_resume_position(self, position: float):
        """Ask the next loaded file to resume from *position* seconds.

        Used by the "Resume Playback" startup option.  The seek is applied once
        the media has actually been parsed (see :meth:`_on_media_ready`),
        because seeking before the media is ready is silently ignored by VLC.
        """
        try:
            self._resume_position = float(position or 0.0)
        except (TypeError, ValueError):
            self._resume_position = 0.0

    def _on_media_ready(self):
        """Called when media is parsed and ready to play"""
        if self.media_engine:
            self.media_engine.play()
            self.position_timer.start()
            self.video_widget.setFocus()
            # Show control panel when media is ready
            self.control_panel.setVisible(True)
            # Apply a pending "resume where you left off" seek.
            resume = getattr(self, "_resume_position", 0.0)
            if resume and resume > 0:
                self._resume_position = 0.0
                try:
                    from PySide6.QtCore import QTimer as _QTimer
                    _QTimer.singleShot(300, lambda: self.media_engine.seek(resume))
                except Exception:
                    pass

    def open_file_dialog(self):
        """Open the standard native Windows file dialog to choose media files."""
        # Remember the last folder the user opened a file from
        last_dir = self.settings.get_last_open_dir()
        if not last_dir or not os.path.exists(last_dir):
            last_dir = os.path.expanduser("~")

        file_filter = self.tr(
            "Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.flac *.ogg *.m4a *.wma "
            "*.3gp *.webm *.ts *.m3u *.m3u8 *.wmv *.mpg *.mpeg *.vob *.ogv *.m2ts *.mts "
            "*.mxf *.divx *.xvid *.rm *.rmvb *.asf);;All Files (*.*)"
        )

        # Bring the player to the foreground first so the native dialog is owned
        # by this window and opens on top of it (not hidden behind it).
        self.activateWindow()
        self.raise_()

        try:
            # Do NOT pass DontUseNativeDialog -> this is the standard Windows
            # "Common Item Dialog" (the same picker used by Explorer / VLC / WMP).
            # This relies on the GUI thread being an STA; see main.py COM init.
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                self.tr("Open Media File"),
                last_dir,
                file_filter,
            )

            if file_path:
                # Remember folder + auto-add every compatible media file in it.
                self.open_media_file(file_path)
        except Exception as e:
            print(f"Error opening file dialog: {e}")
            import traceback
            traceback.print_exc()

    def open_url_dialog(self):
        """Open URL dialog"""
        dialog = UrlDialog(self)
        if dialog.exec():
            url = dialog.get_url()
            if url:
                self.load_file(url)

    def toggle_playlist(self):
        """Toggle playlist visibility"""
        visible = not self.playlist_widget.isVisible()
        self.playlist_widget.setVisible(visible)
        self.accessibility.announce(self.tr("Playlist shown") if visible else self.tr("Playlist hidden"))

    def toggle_repeat(self):
        """Toggle repeat mode via the control panel (keeps UI + state in sync)."""
        if self.control_panel is not None:
            self.control_panel.toggle_repeat()
        elif self.playlist_manager is not None:
            self.playlist_manager.toggle_repeat()

    def toggle_shuffle(self):
        """Toggle shuffle via the control panel (keeps UI + state in sync)."""
        if self.control_panel is not None:
            self.control_panel.toggle_shuffle()
        elif self.playlist_manager is not None:
            self.playlist_manager.toggle_shuffle()

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.settings, self.translation, self.accessibility, self)
        dialog.exec()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.fullscreen:
            self.showNormal()
            if self.previous_geometry:
                # previous_geometry is a saved-geometry QByteArray, so it must
                # be restored with restoreGeometry() (setGeometry expects a
                # QRect and raises a TypeError).
                self.restoreGeometry(self.previous_geometry)
            self.menuBar().setVisible(True)
            self.control_panel.setVisible(True)
            self.fullscreen = False
        else:
            self.previous_geometry = self.saveGeometry()
            self.showFullScreen()
            self.menuBar().setVisible(False)
            self.control_panel.setVisible(False)
            self.fullscreen = True
        self.accessibility.announce(self.tr("Fullscreen on") if self.fullscreen else self.tr("Fullscreen off"))

    def apply_theme(self):
        """Apply current theme"""
        self.settings.apply_theme(self.app_controller.app)

    def retranslate_ui(self):
        """Retranslate UI for language change (live, no restart needed)."""
        self.setWindowTitle(APP_NAME)
        # Recreate menu bar with new language
        self._create_menu_bar()
        self.control_panel.retranslate()
        self.playlist_widget.retranslate()
        if self.subtitle_settings_panel is not None:
            retranslate = getattr(self.subtitle_settings_panel, "retranslate", None)
            if callable(retranslate):
                retranslate()
        # Refresh the accessible description of the video area.
        try:
            self.accessibility.setup_widget_accessibility(
                self.video_widget, self.tr("Video Display"), self.tr("Video playback area")
            )
        except Exception:
            pass
        # Right-to-left for Arabic, left-to-right for everything else.
        direction = Qt.RightToLeft if self.translation.get_current_language() == "ar" else Qt.LeftToRight
        self.setLayoutDirection(direction)
        self.statusBar().showMessage(self.tr("Ready"))

    # Signal handlers
    def _on_state_changed(self, state: str):
        self.control_panel.update_state(state)
        if state == "playing":
            self.position_timer.start()
            self.statusBar().showMessage(self.tr("Playing"))
            # Show control panel when playing
            self.control_panel.setVisible(True)
        elif state == "paused":
            self.position_timer.stop()
            self.statusBar().showMessage(self.tr("Paused"))
        elif state == "stopped":
            self.position_timer.stop()
            self.statusBar().showMessage(self.tr("Ready"))
            # Hide control panel when stopped
            self.control_panel.setVisible(False)
        elif state == "buffering":
            self.statusBar().showMessage(self.tr("Buffering..."))

    def _on_position_changed(self, current: float, total: float):
        self.control_panel.update_position(current, total)

    def _on_duration_changed(self, duration: float):
        self.control_panel.set_duration(duration)

    def _on_volume_changed(self, volume: int):
        self.control_panel.update_volume(volume)

    def _on_muted_changed(self, muted: bool):
        self.control_panel.update_mute(muted)

    def _on_speed_changed(self, speed: float):
        self.control_panel.update_speed(speed)

    def _on_error(self, error: str):
        QMessageBox.critical(self, self.tr("Error"), error)
        self.statusBar().showMessage(self.tr("Error"))

    def _on_media_loaded(self, path: str):
        self.setWindowTitle(f"{Path(path).name} - {APP_NAME}")
        # Auto-detect subtitles
        self._auto_load_subtitle(path)
        # Announce the new media so the screen-reader user knows a file started.
        # Network streams (YouTube etc.) announce their own title and would
        # otherwise expose an ugly URL, so only local files are announced here.
        if self.media_engine and not self.media_engine.current_url and path:
            self.accessibility.announce(self.tr("Playing: ") + Path(path).name)

    def _on_media_ended(self):
        # Keep the control panel visible (nothing looks "frozen") and do NOT
        # speak "playback finished": pressing Space now either advances to the
        # next file (when Auto-play Next is enabled) or restarts this file from
        # the beginning.  Only a sighted status-bar hint is shown.
        try:
            self.statusBar().showMessage(self.tr("Playback finished"))
        except Exception:
            pass

    def _on_playlist_changed(self):
        self.playlist_widget.update_playlist()

    def _on_current_index_changed(self, index: int):
        self.playlist_widget.set_current_index(index)

    def _update_position_display(self):
        """Update position display periodically"""
        if self.media_engine and self.media_engine.get_state() == PlaybackState.PLAYING:
            current = self.media_engine.get_time()
            total = self.media_engine.get_duration()
            self.control_panel.update_position(current, total)

    # Additional features
    def _auto_load_subtitle(self, video_path: str):
        """Auto-load subtitle file"""
        video_file = Path(video_path)
        subtitle_extensions = ['.srt', '.ass', '.ssa', '.sub', '.vtt']
        for ext in subtitle_extensions:
            sub_path = video_file.with_suffix(ext)
            if sub_path.exists():
                self.media_engine.load_external_subtitle(str(sub_path))
                break

    def _show_audio_tracks(self):
        """Show audio track selection"""
        tracks = self.media_engine.get_audio_tracks()
        if tracks:
            current = self.media_engine.get_current_audio_track()
            names = [t["name"] for t in tracks]
            index, ok = QInputDialog.getItem(self, self.tr("Audio Track"), self.tr("Select audio track:"), names, current, False)
            if ok:
                self.media_engine.set_audio_track(tracks[names.index(index)]["id"])

    def _adjust_audio_delay(self):
        """Adjust audio delay"""
        delay, ok = QInputDialog.getInt(self, self.tr("Audio Delay"), self.tr("Delay in milliseconds:"), 0, -10000, 10000)
        if ok:
            self.media_engine.set_audio_sync(delay)

    def _show_equalizer(self):
        """Show equalizer dialog"""
        from ui.dialogs.equalizer_dialog import EqualizerDialog
        dialog = EqualizerDialog(self.media_engine, self.settings, self)
        dialog.exec()

    def _set_aspect_ratio(self):
        """Set aspect ratio"""
        ratios = ["Default", "16:9", "4:3", "1:1", "2.35:1", "2.39:1"]
        ratio, ok = QInputDialog.getItem(self, self.tr("Aspect Ratio"), self.tr("Select aspect ratio:"), ratios, 0, False)
        if ok and ratio != "Default":
            self.media_engine.set_aspect_ratio(ratio)

    def _set_crop(self):
        """Set video crop"""
        crops = ["Default", "16:9", "4:3", "1:1", "2.35:1"]
        crop, ok = QInputDialog.getItem(self, self.tr("Crop"), self.tr("Select crop:"), crops, 0, False)
        if ok and crop != "Default":
            self.media_engine.set_crop(crop)

    def _set_zoom(self):
        """Set video zoom"""
        zoom, ok = QInputDialog.getDouble(self, self.tr("Zoom"), self.tr("Zoom factor:"), 1.0, 0.1, 10.0, 2)
        if ok:
            self.media_engine.set_scale(zoom)

    def _show_subtitle_tracks(self):
        """Show subtitle track selection"""
        tracks = self.media_engine.get_subtitle_tracks()
        if tracks:
            current = self.media_engine.get_current_subtitle_track()
            names = [t["name"] for t in tracks]
            names.insert(0, self.tr("Disabled"))
            index, ok = QInputDialog.getItem(self, self.tr("Subtitle Track"), self.tr("Select subtitle track:"), names, current + 1, False)
            if ok and index > 0:
                self.media_engine.set_subtitle_track(tracks[names.index(index) - 1]["id"])
            elif ok:
                self.media_engine.set_subtitle_track(-1)

    def _adjust_subtitle_delay(self):
        """Adjust subtitle delay"""
        delay, ok = QInputDialog.getInt(self, self.tr("Subtitle Delay"), self.tr("Delay in milliseconds:"), 0, -10000, 10000)
        if ok:
            self.media_engine.set_subtitle_delay(delay)

    def _load_subtitle(self):
        """Load external subtitle"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Load Subtitle"), "",
            self.tr("Subtitle Files (*.srt *.ass *.ssa *.sub *.vtt);;All Files (*.*)")
        )
        if file_path:
            self.media_engine.load_external_subtitle(file_path)

    def _toggle_ab_loop(self):
        """Toggle A-B loop"""
        # Implementation would go here
        self.accessibility.announce(self.tr("A-B Loop toggled"))

    def _take_snapshot(self):
        """Take video snapshot"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Snapshot"), "", self.tr("Images (*.png *.jpg *.bmp)")
        )
        if file_path:
            if self.media_engine.take_snapshot(file_path):
                self.accessibility.announce(self.tr("Snapshot saved"))
            else:
                self.accessibility.announce(self.tr("Failed to save snapshot"))

    def _show_playlist_manager(self):
        """Show playlist manager"""
        from ui.dialogs.playlist_manager_dialog import PlaylistManagerDialog
        dialog = PlaylistManagerDialog(self.playlist_manager, self)
        dialog.exec()

    def _show_shortcuts(self):
        """Show keyboard shortcuts"""
        from ui.dialogs.shortcuts_dialog import ShortcutsDialog
        dialog = ShortcutsDialog(self.accessibility, self)
        dialog.exec()

    def _show_bookmarks(self):
        """Show bookmarks dialog"""
        if not self.bookmark_manager:
            self.accessibility.announce(self.tr("Bookmark manager not available"))
            return

        # Get current file path
        file_path = ""
        if self.media_engine:
            file_path = self.media_engine.current_file or self.media_engine.current_url

        if not file_path:
            self.accessibility.announce(self.tr("No media file loaded"))
            return

        from ui.dialogs.bookmark_dialog import BookmarkDialog
        dialog = BookmarkDialog(self.bookmark_manager, file_path, self.accessibility, self)
        dialog.bookmark_selected.connect(self._on_bookmark_selected)
        dialog.exec()

    def _add_bookmark_at_current_position(self):
        """Add bookmark at current playback position"""
        if not self.bookmark_manager or not self.media_engine:
            return

        file_path = self.media_engine.current_file or self.media_engine.current_url
        if not file_path:
            self.accessibility.announce(self.tr("No media file loaded"))
            return

        current_position = self.media_engine.get_time()
        n = len(self.bookmark_manager.get_bookmarks(file_path)) + 1
        default_name = self.tr("Bookmark {0}").format(n)

        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self,
            self.tr("Add Bookmark"),
            self.tr("Bookmark name:"),
            text=default_name
        )

        if ok and name.strip():
            bookmark = self.bookmark_manager.add_bookmark(file_path, current_position, name.strip())
            self.accessibility.announce(
                self.tr("Bookmark '{0}' added at {1}").format(
                    bookmark.name, self._format_time(current_position)
                )
            )

    def _on_bookmark_selected(self, position: float):
        """Handle bookmark selection"""
        if self.media_engine and self.media_engine.get_duration() > 0:
            seek_position = position / self.media_engine.get_duration()
            self.media_engine.seek(seek_position)
            self.accessibility.announce(
                self.tr("Jumped to bookmark at {0}").format(
                    self._format_time(position)
                )
            )

    # New feature handlers
    def _on_sync_mode_changed(self, mode: str):
        """Handle subtitle sync mode change"""
        if self.subtitle_manager:
            self.subtitle_manager.set_sync_mode(SyncMode(mode))

    def _on_subtitle_offset_changed(self, offset: float):
        """Handle subtitle offset change"""
        if self.subtitle_manager:
            self.subtitle_manager.set_offset(offset)

    def _on_subtitle_visibility_changed(self, visible: bool):
        """Handle subtitle visibility toggle"""
        if self.subtitle_manager:
            self.subtitle_manager.set_visible(visible)

    def _on_subtitle_selected(self, subtitle_path: str):
        """Handle subtitle selection"""
        if self.subtitle_manager and subtitle_path:
            self.subtitle_manager.load_subtitle(subtitle_path)

    def _on_export_subtitles(self, format_type: str, start_time: float, end_time: float):
        """Handle subtitle export request"""
        if not self.subtitle_manager or not self.subtitle_manager.current_subtitle:
            return
            
        from PySide6.QtWidgets import QFileDialog
        
        format_ext = {'txt': '.txt', 'docx': '.docx', 'pdf': '.pdf', 'srt': '.srt'}
        ext = format_ext.get(format_type, '.txt')
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Export Subtitles"), "",
            self.tr("Subtitle Files (*{0});;All Files (*.*)").format(ext)
        )
        
        if file_path:
            success = False
            if format_type == 'txt':
                success = self.subtitle_manager.export_to_txt(file_path)
            elif format_type == 'docx':
                success = self.subtitle_manager.export_to_docx(file_path)
            elif format_type == 'pdf':
                success = self.subtitle_manager.export_to_pdf(file_path)
            elif format_type == 'srt':
                # Export as SRT - would need implementation
                pass
                
            if success:
                self.accessibility.announce(self.tr("Subtitles exported successfully"))
            else:
                self.accessibility.announce(self.tr("Failed to export subtitles"))

    def _show_subtitle_options(self):
        """Show subtitle options dialog"""
        dialog = SubtitleOptionsDialog(self.subtitle_manager, self.media_engine.current_file or "", self)
        dialog.settings_confirmed.connect(self._on_subtitle_options_confirmed)
        dialog.exec()

    def _on_subtitle_options_confirmed(self, settings: dict):
        """Handle subtitle options confirmation"""
        if self.subtitle_manager:
            self.subtitle_manager.set_enabled(settings.get('enabled', True))
            self.subtitle_manager.set_offset(settings.get('offset', 0.0))
            self.subtitle_manager.set_sync_mode(settings.get('sync_mode', SyncMode.REAL_TIME))
            
            if settings.get('subtitle_path'):
                self.subtitle_manager.load_subtitle(settings['subtitle_path'])

    def _show_subtitle_export(self):
        """Show subtitle export dialog"""
        if not self.subtitle_manager or not self.subtitle_manager.current_subtitle:
            return
            
        dialog = SubtitleExportDialog(self.subtitle_manager, self)
        dialog.export_requested.connect(self._on_export_subtitles)
        dialog.exec()

    def _show_youtube_dialog(self):
        """Show the YouTube dialog (works for recorded videos and live streams)."""
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
            QDialogButtonBox, QComboBox, QCheckBox, QGroupBox
        )

        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Open YouTube Video"))
        dialog.resize(640, 340)
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        # URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel(self.tr("YouTube URL:")))

        self.youtube_url_edit = QLineEdit()
        self.youtube_url_edit.setPlaceholderText(
            self.tr("Paste a YouTube video or live-stream link (youtube.com/watch?v=... or youtu.be/...)")
        )
        url_layout.addWidget(self.youtube_url_edit)
        layout.addLayout(url_layout)

        # Quality selection
        quality_group = QGroupBox(self.tr("Stream Quality"))
        quality_layout = QHBoxLayout(quality_group)

        self.youtube_quality_combo = QComboBox()
        self.youtube_quality_combo.addItems([
            self.tr("Auto (Best)"),
            self.tr("1080p"),
            self.tr("720p"),
            self.tr("480p"),
            self.tr("Audio Only"),
        ])
        quality_layout.addWidget(self.youtube_quality_combo)
        layout.addWidget(quality_group)

        # Subtitle options for YouTube
        subtitle_group = QGroupBox(self.tr("Subtitle Options"))
        subtitle_layout = QVBoxLayout(subtitle_group)

        self.youtube_subtitle_check = QCheckBox(self.tr("Load subtitles if available"))
        self.youtube_subtitle_check.setChecked(True)
        subtitle_layout.addWidget(self.youtube_subtitle_check)

        self.youtube_subtitle_lang = QComboBox()
        # (localized label, yt-dlp language code)
        self._youtube_subtitle_langs = [
            (self.tr("Auto"), ""),
            (self.tr("English"), "en"),
            (self.tr("Arabic"), "ar"),
            (self.tr("Spanish"), "es"),
            (self.tr("French"), "fr"),
            (self.tr("German"), "de"),
            (self.tr("Italian"), "it"),
            (self.tr("Portuguese"), "pt"),
            (self.tr("Turkish"), "tr"),
            (self.tr("Chinese"), "zh"),
        ]
        self.youtube_subtitle_lang.addItems([label for label, _ in self._youtube_subtitle_langs])
        self.youtube_subtitle_lang.setEnabled(False)
        self.youtube_subtitle_check.toggled.connect(self.youtube_subtitle_lang.setEnabled)
        subtitle_layout.addWidget(QLabel(self.tr("Subtitle Language:")))
        subtitle_layout.addWidget(self.youtube_subtitle_lang)
        layout.addWidget(subtitle_group)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._on_youtube_dialog_accepted(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec()

    def _on_youtube_dialog_accepted(self, dialog):
        """Handle YouTube dialog acceptance"""
        url = self.youtube_url_edit.text().strip()
        if not url:
            return

        # Determine quality
        quality_map = {
            0: StreamQuality.BEST,
            1: StreamQuality.HD1080,
            2: StreamQuality.HD720,
            3: StreamQuality.HD480,
            4: StreamQuality.AUDIO_ONLY,
        }
        quality = quality_map.get(self.youtube_quality_combo.currentIndex(), StreamQuality.BEST)

        # Remember requested subtitle language (downloaded after the stream starts)
        self._pending_youtube_subtitle_lang = None
        if self.youtube_subtitle_check.isChecked():
            idx = self.youtube_subtitle_lang.currentIndex()
            if 0 <= idx < len(self._youtube_subtitle_langs):
                self._pending_youtube_subtitle_lang = self._youtube_subtitle_langs[idx][1] or None

        dialog.accept()

        # Resolve and load the video asynchronously
        self._load_youtube_video(url, quality)

    def _load_youtube_video(self, url: str, quality: StreamQuality = StreamQuality.BEST):
        """Load a YouTube video/live stream for playback (non-blocking)."""
        is_youtube = any(re.match(pattern, url) for pattern in self.youtube_patterns)
        if not is_youtube:
            self.accessibility.announce(self.tr("Invalid YouTube URL"))
            QMessageBox.warning(self, self.tr("YouTube"), self.tr("Invalid YouTube URL"))
            return

        self._pending_youtube_url = url
        self.statusBar().showMessage(self.tr("Loading YouTube video..."))
        self.accessibility.announce(self.tr("Loading YouTube video..."))
        self._show_youtube_progress(self.tr("Loading YouTube video..."))
        self.youtube_handler.resolve_stream(url, quality)

    def _show_youtube_progress(self, label: str):
        """Show (or reset) the modal download progress dialog."""
        from PySide6.QtWidgets import QProgressDialog

        if getattr(self, "_youtube_progress", None) is None:
            self._youtube_progress = QProgressDialog(label, self.tr("Cancel"), 0, 0, self)
            self._youtube_progress.setWindowTitle(self.tr("YouTube"))
            self._youtube_progress.setWindowModality(Qt.WindowModal)
            self._youtube_progress.setMinimumDuration(600)
            self._youtube_progress.canceled.connect(self._cancel_youtube)
        self._youtube_progress.setLabelText(label)
        self._youtube_progress.setRange(0, 0)  # indeterminate until progress arrives
        self._youtube_progress.show()

    def _close_youtube_progress(self):
        if getattr(self, "_youtube_progress", None) is not None:
            self._youtube_progress.reset()
            self._youtube_progress.close()

    def _cancel_youtube(self):
        if getattr(self, "youtube_handler", None):
            self.youtube_handler.cancel()
        self._close_youtube_progress()
        self.statusBar().showMessage(self.tr("Canceled"))

    def _on_youtube_progress(self, percent: float, message: str):
        if getattr(self, "_youtube_progress", None) is None:
            return
        if percent is None or percent < 0:
            self._youtube_progress.setRange(0, 0)
            self._youtube_progress.setLabelText(message or self.tr("Loading YouTube video..."))
        else:
            self._youtube_progress.setRange(0, 100)
            self._youtube_progress.setValue(int(percent))
            self._youtube_progress.setLabelText(f"{message}  {int(percent)}%")

    def _apply_youtube_title(self, info: dict):
        title = info.get("title") or self.tr("YouTube Video")
        uploader = info.get("uploader") or ""
        window_title = self.tr("YouTube Live Stream") if info.get("is_live") else title
        if uploader:
            self.setWindowTitle(f"{window_title} - {uploader} - {APP_NAME}")
        else:
            self.setWindowTitle(f"{window_title} - {APP_NAME}")
        self.statusBar().showMessage(self.tr("Playing: ") + title)
        self.accessibility.announce(self.tr("Playing: ") + title)

    def _start_pending_youtube_subtitles(self):
        lang = getattr(self, "_pending_youtube_subtitle_lang", None)
        url = getattr(self, "_pending_youtube_url", None)
        if lang and url:
            self.youtube_handler.download_subtitles_async(url, lang)
        self._pending_youtube_subtitle_lang = None

    def _on_youtube_stream_ready(self, stream_url: str, info: dict):
        """The background resolver produced a directly playable URL."""
        self._close_youtube_progress()
        self.load_file(stream_url, info.get("headers"))
        self._apply_youtube_title(info)
        self._start_pending_youtube_subtitles()

    def _on_youtube_file_ready(self, path: str, info: dict):
        """A recorded video finished downloading and merging."""
        self._close_youtube_progress()
        self.load_file(path)
        self._apply_youtube_title(info)
        self._start_pending_youtube_subtitles()

    def _on_youtube_stream_error(self, message: str):
        """The background resolver failed."""
        self._close_youtube_progress()
        self.statusBar().showMessage(self.tr("Failed to load YouTube video"))
        self.accessibility.announce(self.tr("Failed to load YouTube video"))
        QMessageBox.warning(self, self.tr("YouTube"), self.tr("Failed to load YouTube video"))

    def _on_youtube_subtitles_ready(self, path: str):
        """Subtitle download finished."""
        if path and self.subtitle_manager:
            self.subtitle_manager.load_subtitle(path)

    def _load_youtube_video_legacy(self, url: str, quality: StreamQuality = StreamQuality.BEST):
        """(unused) synchronous fallback"""
        stream_url = self.youtube_handler.get_stream_url(url, quality)
        if stream_url:
            self.load_file(stream_url)

    def _on_youtube_info_ready(self, info: dict):
        """Handle YouTube video info ready"""
        title = info.get('title', '')
        uploader = info.get('uploader', '')
        if title:
            self.setWindowTitle(f"{title} - {uploader} - {APP_NAME}")
            self.statusBar().showMessage(self.tr("Playing: ") + title)

    def _show_subtitle_export(self):
        """Show subtitle export dialog"""
        if not self.subtitle_manager or not self.subtitle_manager.current_subtitle:
            return
            
        dialog = SubtitleExportDialog(self.subtitle_manager, self)
        dialog.export_requested.connect(self._on_export_subtitles)
        dialog.exec()

    def _toggle_subtitles(self):
        """Toggle subtitle visibility"""
        if self.subtitle_manager:
            current_visible = self.subtitle_settings_panel.subtitle_toggle.isChecked() if self.subtitle_settings_panel else True
            new_visible = not current_visible
            self.subtitle_manager.set_visible(new_visible)
            if self.subtitle_settings_panel:
                self.subtitle_settings_panel.subtitle_toggle.setChecked(new_visible)

    def _show_about(self):
        """Show the localized, detailed About dialog."""
        from ui.dialogs.about_dialog import AboutDialog

        language = "en"
        try:
            language = self.translation.get_current_language()
        except Exception:
            pass

        dialog = AboutDialog(
            language, APP_NAME, self,
            translation_manager=self.translation,
            accessibility_manager=self.accessibility,
        )
        dialog.exec()

    def closeEvent(self, event):
        """Handle window close"""
        # Save geometry
        self.app_controller.settings.save_window_geometry(self.window_id, self.saveGeometry())

        # Don't cleanup media engine here - it causes COM crashes on Windows
        # Cleanup will happen on application exit

        # Close window
        self.app_controller.close_window(self)
        event.accept()

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape and self.fullscreen:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_T and event.modifiers() == Qt.ControlModifier:
            self._toggle_subtitles()
        else:
            super().keyPressEvent(event)