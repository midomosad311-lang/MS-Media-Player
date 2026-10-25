"""
Control Panel - Playback controls
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider,
    QLabel, QComboBox, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QTimer, QEvent
from core.app_meta import APP_NAME
from media.media_engine import MediaEngine, PlaybackState
from media.playlist_manager import PlaylistManager, RepeatMode
from settings.settings_manager import SettingsManager
from accessibility.accessibility_manager import AccessibilityManager, STANDARD_SHORTCUTS


class ControlPanel(QWidget):
    """Playback control panel"""

    def __init__(self, media_engine: MediaEngine, playlist_manager: PlaylistManager,
                 settings_manager: SettingsManager, accessibility_manager: AccessibilityManager):
        super().__init__()
        self.media_engine = media_engine
        self.playlist_manager = playlist_manager
        self.settings = settings_manager
        self.accessibility = accessibility_manager

        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.mouse_over = False
        # True while the seek bar is being repositioned by the player (not by
        # the user), so the change is not treated as a seek request.
        self._syncing_slider = False

        self._setup_ui()
        self._connect_signals()
        self._apply_accessibility()

        # Position update timer
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position_display)
        self.position_timer.setInterval(500)

    def _setup_ui(self):
        """Setup control panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Add a visible top border to separate from video
        self.setStyleSheet("""
            ControlPanel {
                border-top: 2px solid #555555;
                background-color: #2d2d2d;
            }
        """)

        # Progress bar
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)

        self.position_label = QLabel("0:00")
        self.position_label.setMinimumWidth(50)
        self.position_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.accessibility.setup_widget_accessibility(
            self.position_label, self.tr("Current Position"), self.tr("Current playback position")
        )
        # The labels are purely visual: keep them out of the Tab order so the
        # seek bar itself is the single independent stop that speaks the file
        # name, the total duration and the elapsed / remaining time.
        self.position_label.setFocusPolicy(Qt.NoFocus)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progress_slider.setToolTip(self.tr("Seek position"))
        # Usable keyboard steps (2% / 10%) so arrow keys seek a sensible amount.
        self.progress_slider.setSingleStep(20)
        self.progress_slider.setPageStep(100)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)
        self.progress_slider.valueChanged.connect(self._on_progress_value_changed)
        # Watch focus so the seek bar only speaks while focused and is not
        # moved underneath the user while they are interacting with it.
        self.progress_slider.installEventFilter(self)

        self.duration_label = QLabel("0:00")
        self.duration_label.setMinimumWidth(50)
        self.duration_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.accessibility.setup_widget_accessibility(
            self.duration_label, self.tr("Total Duration"), self.tr("Total media duration")
        )
        # Not a Tab stop (see position_label above).
        self.duration_label.setFocusPolicy(Qt.NoFocus)

        # Setup slider accessibility after duration_label is created.
        # When a screen reader focuses the seek bar it reads, in order:
        #   (a) the current file name,
        #   (b) the total duration spoken as hours/minutes/seconds,
        #   (c) the elapsed and remaining time spoken precisely.
        self.accessibility.setup_slider_accessibility(
            self.progress_slider, self.tr("Seek Bar"),
            self._get_progress_accessible_text
        )

        progress_layout.addWidget(self.position_label)
        progress_layout.addWidget(self.progress_slider, 1)
        progress_layout.addWidget(self.duration_label)

        layout.addLayout(progress_layout)

        # Control buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)

        # Previous
        self.prev_btn = self._create_button(
            "⏮", self.tr("Previous"), "Ctrl+Left",
            self._play_previous, "previous"
        )
        buttons_layout.addWidget(self.prev_btn)

        # Rewind
        self.rewind_btn = self._create_button(
            "⏪", self.tr("Rewind"), "Left",
            lambda: self._seek_by(-self.settings.get_seek_interval()), "backward"
        )
        buttons_layout.addWidget(self.rewind_btn)

        # Play/Pause
        self.play_btn = self._create_button(
            "▶", self.tr("Play"), "Space",
            self._toggle_play_pause, "play_pause"
        )
        self.play_btn.setMinimumWidth(60)
        buttons_layout.addWidget(self.play_btn)

        # Forward
        self.forward_btn = self._create_button(
            "⏩", self.tr("Forward"), "Right",
            lambda: self._seek_by(self.settings.get_seek_interval()), "forward"
        )
        buttons_layout.addWidget(self.forward_btn)

        # Next
        self.next_btn = self._create_button(
            "⏭", self.tr("Next"), "Ctrl+Right",
            self._play_next, "next"
        )
        buttons_layout.addWidget(self.next_btn)

        # Stop
        self.stop_btn = self._create_button(
            "⏹", self.tr("Stop"), "S",
            self.media_engine.stop, "stop"
        )
        buttons_layout.addWidget(self.stop_btn)

        # Spacer
        buttons_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Volume
        self.mute_btn = self._create_button(
            "🔊", self.tr("Mute"), "M",
            self.media_engine.toggle_mute, "mute"
        )
        buttons_layout.addWidget(self.mute_btn)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.settings.get_volume())
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setToolTip(self.tr("Volume"))
        self.accessibility.setup_slider_accessibility(
            self.volume_slider, self.tr("Volume"),
            lambda: f"{self.volume_slider.value()}%"
        )
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        buttons_layout.addWidget(self.volume_slider)

        # Spacer
        buttons_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Speed
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.50x", "0.75x", "1.0x", "1.5x", "2.0x", "2.5x", "3.0x", "3.5x", "4.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.setFixedWidth(80)
        self.speed_combo.setToolTip(self.tr("Playback Speed"))
        self.accessibility.setup_widget_accessibility(
            self.speed_combo, self.tr("Playback Speed"), self.tr("Adjust playback speed"), "A/Q"
        )
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        buttons_layout.addWidget(self.speed_combo)

        # Seek interval
        self.seek_combo = QComboBox()
        self.seek_combo.addItems([
            self.tr("5 sec"), self.tr("10 sec"), self.tr("30 sec"), self.tr("1 min"),
            self.tr("5 min"), self.tr("10 min"), self.tr("30 min"), self.tr("1 hour")
        ])
        self.seek_combo.setCurrentIndex(1)  # 10 sec default
        self.seek_combo.setFixedWidth(100)
        self.seek_combo.setToolTip(self.tr("Seek Interval"))
        self.accessibility.setup_widget_accessibility(
            self.seek_combo, self.tr("Seek Interval"), self.tr("Set seek forward/backward interval")
        )
        self.seek_combo.currentIndexChanged.connect(self._on_seek_interval_changed)
        buttons_layout.addWidget(self.seek_combo)

        # Repeat
        self.repeat_btn = self._create_button(
            "🔁", self.tr("Repeat"), "R",
            self._toggle_repeat, "repeat"
        )
        self.repeat_btn.setCheckable(True)
        buttons_layout.addWidget(self.repeat_btn)

        # Shuffle
        self.shuffle_btn = self._create_button(
            "🔀", self.tr("Shuffle"), "H",
            self._toggle_shuffle, "shuffle"
        )
        self.shuffle_btn.setCheckable(True)
        buttons_layout.addWidget(self.shuffle_btn)

        # Fullscreen
        self.fullscreen_btn = self._create_button(
            "⛶", self.tr("Fullscreen"), "F",
            self._toggle_fullscreen, "fullscreen"
        )
        buttons_layout.addWidget(self.fullscreen_btn)

        # Playlist
        self.playlist_btn = self._create_button(
            "📋", self.tr("Playlist"), "Ctrl+L",
            self._toggle_playlist, "playlist"
        )
        buttons_layout.addWidget(self.playlist_btn)

        # Subtitle Settings
        self.subtitle_btn = self._create_button(
            "📝", self.tr("Subtitles"), "Ctrl+Shift+S",
            self._toggle_subtitle_panel, "subtitle_options"
        )
        buttons_layout.addWidget(self.subtitle_btn)

        layout.addLayout(buttons_layout)

        # Time display
        self.time_info = QLabel("")
        self.time_info.setAlignment(Qt.AlignCenter)
        self.time_info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.time_info)

        self.slider_pressed = False

    def _create_button(self, text: str, tooltip: str, shortcut: str,
                        callback, accessibility_name: str):
        """Create accessible button"""
        btn = QPushButton(text)
        btn.setToolTip(f"{tooltip} ({shortcut})" if shortcut else tooltip)
        btn.setMinimumSize(40, 40)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.clicked.connect(callback)

        # Accessibility - new format: just pass the name and shortcut
        # The accessibility manager will create "name shortcut" format
        shortcut_key = STANDARD_SHORTCUTS.get(accessibility_name, shortcut)
        self.accessibility.setup_widget_accessibility(btn, tooltip, "", shortcut_key)

        return btn

    def _connect_signals(self):
        """Connect signals"""
        pass

    def _apply_accessibility(self):
        """Apply accessibility settings"""
        pass

    def _on_slider_pressed(self):
        """Handle slider press"""
        self.slider_pressed = True

    def _on_slider_released(self):
        """Handle slider release"""
        self.slider_pressed = False
        if self.media_engine and self.media_engine.get_duration() > 0:
            position = self.progress_slider.value() / 1000.0
            self.media_engine.seek(position)

    def _on_slider_moved(self, value: int):
        """Handle slider move"""
        if self.media_engine and self.media_engine.get_duration() > 0:
            position = value / 1000.0
            current = position * self.media_engine.get_duration()
            self.position_label.setText(self._format_time(current))

    def eventFilter(self, obj, event):
        """Sync the seek bar to the live position and speak its full state
        when it gains focus.

        The player does not move the seek bar while it has focus (see
        ``update_position``), so on focus we snap it to the current position.
        We then announce, in order: the current file name, the total duration,
        and the elapsed / remaining time, so a screen-reader user gets a
        complete, actionable description the moment they reach the control.
        """
        if obj is self.progress_slider and event.type() == QEvent.FocusIn:
            duration = self.media_engine.get_duration() if self.media_engine else 0
            if duration > 0:
                self._syncing_slider = True
                self.progress_slider.setValue(
                    int((self.media_engine.get_time() / duration) * 1000)
                )
                self._syncing_slider = False
            # Refresh the accessible NAME so the screen reader reads the full
            # description (file name, total duration, elapsed / remaining) the
            # moment the seek bar is focused.  The player also keeps this name
            # current while the bar is *not* focused (see update_position),
            # because Qt raises the accessibility focus event before this
            # filter runs.
            self._refresh_seek_accessible_text(force=True)
        return super().eventFilter(obj, event)

    def _on_progress_value_changed(self, value: int):
        """Seek when the user changes the seek bar with the keyboard.

        Only fires for user-driven changes while the bar has focus; automatic
        playback updates are flagged with ``_syncing_slider`` and ignored.
        """
        if self._syncing_slider or self.slider_pressed:
            return
        if not self.progress_slider.hasFocus():
            return
        if self.media_engine and self.media_engine.get_duration() > 0:
            self.media_engine.seek(value / 1000.0)
            self.position_label.setText(
                self._format_time(value / 1000.0 * self.media_engine.get_duration())
            )

    def _on_volume_changed(self, value: int):
        """Handle volume change"""
        if self.media_engine:
            self.media_engine.set_volume(value)

    def _on_speed_changed(self, text: str):
        """Handle speed change"""
        if self.media_engine:
            speed = float(text.replace('x', ''))
            self.media_engine.set_speed(speed)

    def _on_seek_interval_changed(self, index: int):
        """Handle seek interval change"""
        intervals = [5, 10, 30, 60, 300, 600, 1800, 3600]
        if index < len(intervals):
            self.settings.set_seek_interval(intervals[index])

    def _toggle_play_pause(self):
        """Play/pause via the window so it can restart/advance after the end."""
        win = self.window()
        if hasattr(win, "toggle_play_pause"):
            win.toggle_play_pause()
        elif self.media_engine:
            self.media_engine.toggle_play_pause()

    def _seek_by(self, delta: float):
        """Seek by *delta* seconds and speak the new position in full words."""
        if not self.media_engine:
            return
        self.media_engine.seek_relative(delta)
        self._announce_position_words()

    def _announce_position_words(self):
        """Speak the current position as words (elapsed of total, remaining)."""
        total = self.media_engine.get_duration() if self.media_engine else 0
        current = max(0.0, self.media_engine.get_time()) if self.media_engine else 0.0
        if total <= 0:
            self.accessibility.announce(self.tr("No media loaded"), priority=True)
            return
        remaining = max(0.0, total - current)
        lang = self._language_code()
        if str(lang).startswith("ar"):
            message = (f"{self._format_duration_words(current, lang)} "
                       f"من {self._format_duration_words(total, lang)}، "
                       f"ويتبقى {self._format_duration_words(remaining, lang)}")
        else:
            message = (f"{self._format_duration_words(current, lang)} elapsed of "
                       f"{self._format_duration_words(total, lang)}, "
                       f"{self._format_duration_words(remaining, lang)} remaining")
        self.accessibility.announce(message, priority=True)

    def _play_next(self):
        """Play next track via the owning window"""
        window = self.window()
        if hasattr(window, 'play_next'):
            window.play_next()
        elif self.playlist_manager:
            path = self.playlist_manager.next()
            if path:
                self.media_engine.load_file(path)
                self.media_engine.play()

    def _play_previous(self):
        """Play previous track via the owning window"""
        window = self.window()
        if hasattr(window, 'play_previous'):
            window.play_previous()
        elif self.playlist_manager:
            path = self.playlist_manager.previous()
            if path:
                self.media_engine.load_file(path)
                self.media_engine.play()

    def _toggle_repeat(self):
        """Toggle repeat mode (button handler)."""
        self.toggle_repeat()

    def toggle_repeat(self):
        """Toggle repeat mode and keep button, persistence and announcement in sync.

        Called both by the on-screen button and by the global ``R`` shortcut.
        """
        if self.playlist_manager is None:
            return
        mode = self.playlist_manager.toggle_repeat()
        # Persist so the choice survives a restart.
        try:
            self.settings.set_repeat_mode(mode.value)
        except Exception:
            pass
        self.repeat_btn.setChecked(mode != RepeatMode.OFF)
        self.repeat_btn.setToolTip(self._repeat_tooltip(mode))
        self.accessibility.announce(self.tr("Repeat: ") + self._repeat_label(mode))

    def _repeat_label(self, mode: RepeatMode) -> str:
        if mode == RepeatMode.ONE:
            return self.tr("One")
        if mode == RepeatMode.ALL:
            return self.tr("All")
        return self.tr("Off")

    def _repeat_tooltip(self, mode: RepeatMode) -> str:
        return self.tr("Repeat ({0}) (R)").format(self._repeat_label(mode))

    def _toggle_shuffle(self):
        """Toggle shuffle (button handler)."""
        self.toggle_shuffle()

    def toggle_shuffle(self):
        """Toggle shuffle and keep button, persistence and announcement in sync.

        Called both by the on-screen button and by the global ``H`` shortcut.
        """
        if self.playlist_manager is None:
            return
        enabled = self.playlist_manager.toggle_shuffle()
        try:
            self.settings.set_shuffle(enabled)
        except Exception:
            pass
        self.shuffle_btn.setChecked(enabled)
        self.accessibility.announce(
            self.tr("Shuffle: ") + (self.tr("On") if enabled else self.tr("Off"))
        )

    def sync_playlist_toggles(self):
        """Reflect the playlist manager's repeat/shuffle state in the buttons.

        Used when a window is first shown or when the state is changed
        elsewhere, so the keyboard shortcut and the buttons never disagree.
        """
        if self.playlist_manager is None:
            return
        try:
            mode = self.playlist_manager.get_repeat_mode()
            self.repeat_btn.setChecked(mode != RepeatMode.OFF)
            self.repeat_btn.setToolTip(self._repeat_tooltip(mode))
            self.shuffle_btn.setChecked(self.playlist_manager.get_shuffle())
        except Exception:
            pass

    def _toggle_fullscreen(self):
        """Toggle fullscreen"""
        window = self.window()
        if hasattr(window, 'toggle_fullscreen'):
            window.toggle_fullscreen()

    def _toggle_playlist(self):
        """Toggle playlist"""
        window = self.window()
        if hasattr(window, 'toggle_playlist'):
            window.toggle_playlist()

    def _toggle_subtitle_panel(self):
        """Toggle subtitle settings panel"""
        window = self.window()
        if hasattr(window, 'subtitle_settings_panel') and window.subtitle_settings_panel:
            visible = not window.subtitle_settings_panel.isVisible()
            window.subtitle_settings_panel.setVisible(visible)
            self.subtitle_btn.setChecked(visible)

    def update_state(self, state: str):
        """Update play/pause button"""
        if state == "playing":
            self.play_btn.setText("⏸")
            self.play_btn.setToolTip(self.tr("Pause (Space)"))
            self.accessibility.setup_widget_accessibility(
                self.play_btn, self.tr("Pause"), self.tr("Pause playback"), "Space"
            )
        else:
            self.play_btn.setText("▶")
            self.play_btn.setToolTip(self.tr("Play (Space)"))
            self.accessibility.setup_widget_accessibility(
                self.play_btn, self.tr("Play"), self.tr("Start playback"), "Space"
            )

    def update_position(self, current: float, total: float):
        """Update position display"""
        # Don't update if control panel is not visible (widgets not ready)
        if not self.isVisible():
            return
            
        try:
            # Never move the seek bar while the user is interacting with it
            # (dragging or keyboard focus).  Moving it would (a) fight the
            # user's own seeking and (b) make the screen reader announce the
            # position on every 100 ms tick.
            if (total > 0 and not self.slider_pressed
                    and not self.progress_slider.hasFocus()):
                progress = int((current / total) * 1000)
                self._syncing_slider = True
                self.progress_slider.setValue(progress)
                self._syncing_slider = False

            pos_text = self._format_time(current)
            if self.position_label.text() != pos_text:
                self.position_label.setText(pos_text)
            dur_text = self._format_time(total)
            if self.duration_label.text() != dur_text:
                self.duration_label.setText(dur_text)

            # Keep the seek bar's accessible name current while it does not
            # hold focus, so the screen reader reads fresh values the instant
            # focus lands on it (Qt raises the accessibility focus event before
            # our FocusIn filter runs).  This is a no-op unless the spoken text
            # actually changed, which keeps the accessibility event rate low.
            if not self.progress_slider.hasFocus():
                self._refresh_seek_accessible_text()

            # Update accessible value for screen readers - DISABLED to prevent crashes on Windows
            # try:
            #     self.accessibility.update_slider_accessible_value(
            #         self.progress_slider, self._get_progress_accessible_text()
            #     )
            # except Exception:
            #     pass

            # Update time info
            if total > 0:
                percent = int((current / total) * 100)
                remaining = total - current
                info_text = f"{percent}% | Remaining: -{self._format_time(remaining)}"
                if self.time_info.text() != info_text:
                    self.time_info.setText(info_text)
        except Exception as e:
            print(f"Error in update_position: {e}")

    def _language_code(self) -> str:
        """Current UI language code (lower-case), e.g. ``ar`` or ``en``."""
        try:
            return (self.settings.get_language() or "en").lower()
        except Exception:
            return "en"

    @staticmethod
    def _format_duration_words(seconds: float, lang: str = "en") -> str:
        """Format a duration as a human-readable, screen-reader friendly string.

        Arabic uses its real singular / dual / plural forms so the phrasing
        matches the requirement's examples ("ساعتان", "3 ساعات", "59 دقيقة",
        "30 ثانية").  Other languages use the English form
        ("3 hours 30 seconds").
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

    def _current_media_name(self) -> str:
        """Best-effort friendly name of the media currently loaded."""
        import os
        engine = self.media_engine if self.media_engine else None
        name = ""
        if engine is not None:
            name = engine.current_file or engine.current_url or ""
        # For network/YouTube streams the raw URL is meaningless to a listener,
        # so fall back to the (already localized) window title.
        if name and '://' in str(name):
            try:
                win = self.window()
                title = (win.windowTitle() if win is not None else "") or ""
                for suffix in (f" - {APP_NAME}", " - MS Media"):
                    if title.endswith(suffix):
                        title = title[: -len(suffix)]
                if title:
                    name = title
            except Exception:
                pass
        if not name:
            name = self.tr("No media loaded")
        try:
            # Only take a basename for real file paths.
            if os.path.sep in str(name):
                name = os.path.basename(str(name))
        except Exception:
            pass
        return str(name)

    def _get_progress_accessible_text(self, filename=None, current=None, total=None, *args, **kwargs) -> str:
        """Return the full accessibility announcement when the seek bar is
        focused.

        Announces, in order: (a) the current file name, (b) the total
        duration spoken as hours/minutes/seconds, and (c) the elapsed and
        remaining time spoken precisely.
        """
        engine = self.media_engine if self.media_engine else None

        if filename is not None and str(filename).strip():
            import os
            fname = str(filename)
            if os.path.sep in fname:
                fname = os.path.basename(fname)
        else:
            fname = self._current_media_name()

        total_sec = float(total) if total is not None else 0.0
        current_sec = float(current) if current is not None else 0.0
        if engine is not None:
            total_sec = float(engine.get_duration() or total_sec)
            current_sec = float(engine.get_time() or current_sec)

        if total_sec <= 0:
            try:
                total_sec = self._parse_time(self.duration_label.text())
            except Exception:
                pass
        if current_sec < 0:
            current_sec = 0

        lang = self._language_code()
        total_words = self._format_duration_words(total_sec, lang)
        elapsed_words = self._format_duration_words(current_sec, lang)
        remaining_words = self._format_duration_words(max(0.0, total_sec - current_sec), lang)

        if str(lang).startswith("ar"):
            return (f"{fname}. المدة الكلية {total_words}. "
                    f"فات منها {elapsed_words}، ويتبقى {remaining_words}")
        return (f"{fname}. Total {total_words}. "
                f"Elapsed {elapsed_words}. Remaining {remaining_words}")

    _get_progress_accessibility_text = _get_progress_accessible_text  # backward compatibility with older callers

    def _refresh_seek_accessible_text(self, force: bool = False):
        """Publish the seek bar's full description as its accessible NAME.

        Screen readers read the *name* of the object they move focus to; the
        accessible *description* stays hidden unless the user explicitly turns
        it on.  Storing the sentence as the name is what makes NVDA / Narrator
        speak the file name, the total duration and the elapsed / remaining
        time the moment the seek bar receives focus.

        The name is only recomputed / pushed when the value actually changed
        (or when *force* is set), so the screen reader is not flooded with
        accessibility events on every 100 ms playback tick - that event storm
        made the app appear to freeze after a minute or two of playback.
        """
        try:
            text = self._get_progress_accessible_text()
        except Exception:
            return
        if not force and text == getattr(self, "_last_seek_a11y_text", None):
            return
        self._last_seek_a11y_text = text
        try:
            if self.progress_slider.accessibleName() != text:
                self.progress_slider.setAccessibleName(text)
            # Do not duplicate the sentence in the description: with "report
            # object descriptions" enabled it would be spoken twice.
            if self.progress_slider.accessibleDescription():
                self.progress_slider.setAccessibleDescription("")
            if self.progress_slider.property("accessibleValue") != text:
                self.progress_slider.setProperty("accessibleValue", text)
        except Exception:
            pass

    def _parse_time(self, time_str: str) -> float:
        """Parse time string (MM:SS or HH:MM:SS) to seconds"""
        parts = time_str.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0.0

    def set_duration(self, duration: float):
        """Set total duration"""
        if not self.isVisible():
            return
        try:
            self.duration_label.setText(self._format_time(duration))
            # The total duration is part of the seek bar's spoken description.
            if not self.progress_slider.hasFocus():
                self._refresh_seek_accessible_text()
        except Exception as e:
            print(f"Error in set_duration: {e}")

    def update_volume(self, volume: int):
        """Update volume slider"""
        if not self.isVisible():
            return
        try:
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(volume)
            self.volume_slider.blockSignals(False)

            # Update accessible value for screen readers
            try:
                self.accessibility.update_slider_accessible_value(
                    self.volume_slider, f"{volume}%"
                )
            except Exception:
                pass

            # Update mute button
            if volume == 0:
                self.mute_btn.setText("🔇")
            else:
                self.mute_btn.setText("🔊")
        except Exception as e:
            print(f"Error in update_volume: {e}")

    def update_mute(self, muted: bool):
        """Update mute button"""
        if not self.isVisible():
            return
        try:
            self.mute_btn.setText("🔇" if muted else "🔊")
            self.mute_btn.setChecked(muted)
        except Exception as e:
            print(f"Error in update_mute: {e}")

    def update_speed(self, speed: float):
        """Update speed combo"""
        if not self.isVisible():
            return
        try:
            self.speed_combo.blockSignals(True)
            self.speed_combo.setCurrentText(f"{speed}x")
            self.speed_combo.blockSignals(False)
        except Exception as e:
            print(f"Error in update_speed: {e}")

    def retranslate(self):
        """Retranslate UI"""
        self.prev_btn.setToolTip(self.tr("Previous (Ctrl+Left)"))
        self.rewind_btn.setToolTip(self.tr("Rewind (Left)"))
        self.play_btn.setToolTip(self.tr("Play/Pause (Space)"))
        self.forward_btn.setToolTip(self.tr("Forward (Right)"))
        self.next_btn.setToolTip(self.tr("Next (Ctrl+Right)"))
        self.stop_btn.setToolTip(self.tr("Stop (S)"))
        self.mute_btn.setToolTip(self.tr("Mute (M)"))
        self.volume_slider.setToolTip(self.tr("Volume"))
        self.speed_combo.setToolTip(self.tr("Playback Speed"))
        self.seek_combo.setToolTip(self.tr("Seek Interval"))
        self.repeat_btn.setToolTip(self.tr("Repeat (R)"))
        self.shuffle_btn.setToolTip(self.tr("Shuffle (H)"))
        self.fullscreen_btn.setToolTip(self.tr("Fullscreen (F)"))
        self.playlist_btn.setToolTip(self.tr("Playlist (Ctrl+L)"))

        # Retranslate combo box items, preserving the current selection.
        speed_index = self.speed_combo.currentIndex()
        seek_index = self.seek_combo.currentIndex()
        self.speed_combo.blockSignals(True)
        self.seek_combo.blockSignals(True)

        self.speed_combo.clear()
        self.speed_combo.addItems(["0.25x", "0.50x", "0.75x", "1.0x", "1.5x", "2.0x", "2.5x", "3.0x", "3.5x", "4.0x"])
        if 0 <= speed_index < self.speed_combo.count():
            self.speed_combo.setCurrentIndex(speed_index)
        else:
            self.speed_combo.setCurrentText("1.0x")

        self.seek_combo.clear()
        self.seek_combo.addItems([
            self.tr("5 sec"), self.tr("10 sec"), self.tr("30 sec"), self.tr("1 min"),
            self.tr("5 min"), self.tr("10 min"), self.tr("30 min"), self.tr("1 hour")
        ])
        if 0 <= seek_index < self.seek_combo.count():
            self.seek_combo.setCurrentIndex(seek_index)

        self.speed_combo.blockSignals(False)
        self.seek_combo.blockSignals(False)

        # Refresh the accessible names/descriptions spoken by screen readers.
        try:
            self.accessibility.setup_widget_accessibility(
                self.position_label, self.tr("Current Position"),
                self.tr("Current playback position"))
            self.accessibility.setup_widget_accessibility(
                self.duration_label, self.tr("Total Duration"),
                self.tr("Total media duration"))
            self.accessibility.setup_slider_accessibility(
                self.progress_slider, self.tr("Seek Bar"),
                self._get_progress_accessible_text)
            self.accessibility.setup_slider_accessibility(
                self.volume_slider, self.tr("Volume"),
                lambda: f"{self.volume_slider.value()}%")
            self.accessibility.setup_widget_accessibility(
                self.speed_combo, self.tr("Playback Speed"),
                self.tr("Adjust playback speed"), "A/Q")
            self.accessibility.setup_widget_accessibility(
                self.seek_combo, self.tr("Seek Interval"),
                self.tr("Set seek forward/backward interval"))
            button_names = (
                (self.prev_btn, "Previous", "Ctrl+Left"),
                (self.rewind_btn, "Rewind", "Left"),
                (self.play_btn, "Play", "Space"),
                (self.forward_btn, "Forward", "Right"),
                (self.next_btn, "Next", "Ctrl+Right"),
                (self.stop_btn, "Stop", "S"),
                (self.mute_btn, "Mute", "M"),
                (self.repeat_btn, self._repeat_label(self.media_engine.get_repeat_mode())
                 if self.media_engine else self.tr("Repeat"), "R"),
                (self.shuffle_btn, self.tr("Shuffle"), "H"),
                self.fullscreen_btn and (self.fullscreen_btn, self.tr("Fullscreen"), "F"),
                (self.playlist_btn, self.tr("Playlist"), "Ctrl+L"),
                (self.subtitle_btn, self.tr("Subtitles"), "Ctrl+Shift+S"),
            )
            for item in button_names:
                if not item:
                    continue
                btn, name, shortcut = item
                self.accessibility.setup_widget_accessibility(btn, name, "", shortcut)
        except Exception:
            pass

    def set_mouse_over(self, over: bool):
        """Set mouse over state"""
        self.mouse_over = over

    def _update_position_display(self):
        """Update position display periodically"""
        if self.media_engine and self.media_engine.get_state() == PlaybackState.PLAYING:
            current = self.media_engine.get_time()
            total = self.media_engine.get_duration()
            self.update_position(current, total)

    def _connect_signals(self):
        """Connect signals"""
        pass

    def _apply_accessibility(self):
        """Apply accessibility settings"""
        pass

    def _format_time(self, seconds: float) -> str:
        """Format time as MM:SS or HH:MM:SS"""
        if seconds < 0:
            seconds = 0
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"