"""
Settings Dialog - Application settings
"""

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QLabel, QGroupBox, QSlider, QColorDialog,
    QFontDialog, QLineEdit, QDialogButtonBox, QMessageBox,
    QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from core.app_meta import USER_AGENT
from settings.settings_manager import SettingsManager
from i18n.translation_manager import TranslationManager
from accessibility.accessibility_manager import AccessibilityManager


class SettingsDialog(QDialog):
    """Settings dialog"""

    def __init__(self, settings_manager: SettingsManager,
                 translation_manager: TranslationManager,
                 accessibility_manager: AccessibilityManager,
                 parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.translation = translation_manager
        self.accessibility = accessibility_manager

        self.setWindowTitle(self.tr("Settings"))
        self.resize(600, 500)
        self.setModal(True)

        # Source strings for the tab titles (kept so they can be re-translated
        # in place when the language changes while the dialog is open).
        self._tab_sources = [
            "General", "Playback", "Audio", "Video", "Subtitles",
            "Network", "Accessibility", "Playlist", "Appearance",
        ]

        self._setup_ui()
        self._load_settings()

        # Live language switching: refresh this dialog immediately when the
        # language changes (e.g. via the language combo or the Language menu).
        try:
            self.translation.language_changed.connect(self.retranslate)
        except Exception:
            pass

    def _setup_ui(self):
        """Setup settings UI"""
        layout = QVBoxLayout(self)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # General tab
        self.tabs.addTab(self._create_general_tab(), self.tr("General"))

        # Playback tab
        self.tabs.addTab(self._create_playback_tab(), self.tr("Playback"))

        # Audio tab
        self.tabs.addTab(self._create_audio_tab(), self.tr("Audio"))

        # Video tab
        self.tabs.addTab(self._create_video_tab(), self.tr("Video"))

        # Subtitle tab
        self.tabs.addTab(self._create_subtitle_tab(), self.tr("Subtitles"))

        # Network tab
        self.tabs.addTab(self._create_network_tab(), self.tr("Network"))

        # Accessibility tab
        self.tabs.addTab(self._create_accessibility_tab(), self.tr("Accessibility"))

        # Playlist tab
        self.tabs.addTab(self._create_playlist_tab(), self.tr("Playlist"))

        # Appearance tab
        self.tabs.addTab(self._create_appearance_tab(), self.tr("Appearance"))

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._reset_defaults)
        layout.addWidget(button_box)

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Language
        self.lang_combo = QComboBox()
        for code, info in self.translation.get_available_languages().items():
            self.lang_combo.addItem(info["native"], code)
        self.lang_combo.setCurrentIndex(
            self.lang_combo.findData(self.settings.get_language())
        )
        layout.addRow(self.tr("Language:"), self.lang_combo)

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([self.tr("Dark"), self.tr("Light")])
        self.theme_combo.setCurrentIndex(0 if self.settings.get_theme() == "dark" else 1)
        layout.addRow(self.tr("Theme:"), self.theme_combo)

        # High contrast
        self.high_contrast_check = QCheckBox(self.tr("High Contrast"))
        self.high_contrast_check.setChecked(self.settings.get_high_contrast())
        layout.addRow("", self.high_contrast_check)

        # Hardware acceleration
        self.hw_accel_check = QCheckBox(self.tr("Hardware Acceleration"))
        self.hw_accel_check.setChecked(self.settings.get_hardware_acceleration())
        layout.addRow("", self.hw_accel_check)

        # Startup behavior.  The item order matches
        # SettingsManager.STARTUP_MODES so the index maps directly to the value.
        self.startup_combo = QComboBox()
        self.startup_combo.addItems([
            self.tr("Empty (open with nothing)"),
            self.tr("Last File"),
            self.tr("Last Playlist"),
            self.tr("Resume Playback"),
        ])
        try:
            self.startup_combo.setCurrentIndex(
                self.settings.STARTUP_MODES.index(self.settings.get_startup_behavior())
            )
        except (ValueError, AttributeError):
            self.startup_combo.setCurrentIndex(0)
        layout.addRow(self.tr("On Startup:"), self.startup_combo)

        # Minimize to tray
        self.minimize_tray_check = QCheckBox(self.tr("Minimize to System Tray"))
        layout.addRow("", self.minimize_tray_check)

        return widget

    def _create_playback_tab(self) -> QWidget:
        """Create playback settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Default volume
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(0, 100)
        self.volume_spin.setValue(self.settings.get_volume())
        self.volume_spin.setSuffix("%")
        layout.addRow(self.tr("Default Volume:"), self.volume_spin)

        # Default speed
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.25, 4.0)
        self.speed_spin.setSingleStep(0.25)
        self.speed_spin.setValue(self.settings.get_speed())
        self.speed_spin.setSuffix("x")
        layout.addRow(self.tr("Default Speed:"), self.speed_spin)

        # Seek interval
        self.seek_spin = QSpinBox()
        self.seek_spin.setRange(1, 3600)
        self.seek_spin.setValue(self.settings.get_seek_interval())
        self.seek_spin.setSuffix(self.tr(" sec"))
        layout.addRow(self.tr("Seek Interval:"), self.seek_spin)

        # Repeat mode
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems([self.tr("Off"), self.tr("One"), self.tr("All")])
        mode_map = {"off": 0, "one": 1, "all": 2}
        self.repeat_combo.setCurrentIndex(mode_map.get(self.settings.get_repeat_mode(), 0))
        layout.addRow(self.tr("Repeat Mode:"), self.repeat_combo)

        # Shuffle
        self.shuffle_check = QCheckBox(self.tr("Shuffle by Default"))
        self.shuffle_check.setChecked(self.settings.get_shuffle())
        layout.addRow("", self.shuffle_check)

        # Auto-play next
        self.autoplay_check = QCheckBox(self.tr("Auto-play Next"))
        self.autoplay_check.setChecked(self.settings.get_autoplay_next())
        layout.addRow("", self.autoplay_check)

        # Remember position
        self.remember_pos_check = QCheckBox(self.tr("Remember Playback Position"))
        self.remember_pos_check.setChecked(True)
        layout.addRow("", self.remember_pos_check)

        return widget

    def _create_audio_tab(self) -> QWidget:
        """Create audio settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Audio output
        audio_group = QGroupBox(self.tr("Audio Output"))
        audio_layout = QFormLayout(audio_group)

        self.audio_device_combo = QComboBox()
        self.audio_device_combo.addItems([self.tr("Default"), self.tr("DirectSound"), self.tr("WASAPI"), self.tr("WaveOut")])
        audio_layout.addRow(self.tr("Output Device:"), self.audio_device_combo)

        self.audio_channels_combo = QComboBox()
        self.audio_channels_combo.addItems(["Auto", "Stereo", "5.1", "7.1"])
        audio_layout.addRow(self.tr("Channels:"), self.audio_channels_combo)

        layout.addWidget(audio_group)

        # Audio sync
        sync_group = QGroupBox(self.tr("Synchronization"))
        sync_layout = QFormLayout(sync_group)

        self.audio_sync_spin = QSpinBox()
        self.audio_sync_spin.setRange(-10000, 10000)
        self.audio_sync_spin.setValue(self.settings.get_audio_sync())
        self.audio_sync_spin.setSuffix(self.tr(" ms"))
        sync_layout.addRow(self.tr("Audio Delay:"), self.audio_sync_spin)

        layout.addWidget(sync_group)

        # Equalizer
        eq_group = QGroupBox(self.tr("Equalizer"))
        eq_layout = QVBoxLayout(eq_group)

        self.eq_enabled_check = QCheckBox(self.tr("Enable Equalizer"))
        eq_layout.addWidget(self.eq_enabled_check)

        eq_presets = QHBoxLayout()
        eq_presets.addWidget(QLabel(self.tr("Preset:")))
        self.eq_preset_combo = QComboBox()
        self.eq_preset_combo.addItems([
            self.tr("Flat"), self.tr("Classical"), self.tr("Club"), self.tr("Dance"), self.tr("Full Bass"),
            self.tr("Full Bass & Treble"), self.tr("Full Treble"), self.tr("Headphones"),
            self.tr("Large Hall"), self.tr("Live"), self.tr("Party"), self.tr("Pop"), self.tr("Reggae"),
            self.tr("Rock"), self.tr("Ska"), self.tr("Soft"), self.tr("Techno")
        ])
        eq_presets.addWidget(self.eq_preset_combo)
        eq_layout.addLayout(eq_presets)

        # Equalizer bands
        bands_layout = QHBoxLayout()
        freq_labels = ["60", "170", "310", "600", "1k", "3k", "6k", "12k", "14k", "16k"]
        self.eq_bands = []
        for i, freq in enumerate(freq_labels):
            band_layout = QVBoxLayout()
            band_layout.addWidget(QLabel(f"{freq} Hz", alignment=Qt.AlignCenter))
            slider = QSlider(Qt.Vertical)
            slider.setRange(-20, 20)
            slider.setValue(0)
            slider.setFixedHeight(100)
            slider.setTickPosition(QSlider.TicksBothSides)
            slider.setTickInterval(5)
            self.eq_bands.append(slider)
            band_layout.addWidget(slider)
            bands_layout.addLayout(band_layout)
        eq_layout.addLayout(bands_layout)

        layout.addWidget(eq_group)

        return widget

    def _create_video_tab(self) -> QWidget:
        """Create video settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Video output
        self.video_output_combo = QComboBox()
        self.video_output_combo.addItems([self.tr("Auto"), self.tr("Direct3D11"), self.tr("Direct3D9"), self.tr("OpenGL"), self.tr("Software")])
        layout.addRow(self.tr("Video Output:"), self.video_output_combo)

        # Deinterlacing
        self.deinterlace_combo = QComboBox()
        self.deinterlace_combo.addItems([self.tr("Off"), self.tr("Auto"), self.tr("Mean"), self.tr("Bob"), self.tr("Linear"), self.tr("X"), self.tr("Yadif"), self.tr("Yadif2x"), self.tr("Phosphor"), self.tr("IVTC")])
        layout.addRow(self.tr("Deinterlacing:"), self.deinterlace_combo)

        # Hardware decoding
        self.hw_decode_check = QCheckBox(self.tr("Hardware Decoding"))
        self.hw_decode_check.setChecked(True)
        layout.addRow("", self.hw_decode_check)

        # Post-processing
        self.postprocess_check = QCheckBox(self.tr("Post-processing"))
        layout.addRow("", self.postprocess_check)

        # Aspect ratio
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems([self.tr("Default"), "16:9", "4:3", "1:1", "2.35:1", "2.39:1"])
        layout.addRow(self.tr("Force Aspect Ratio:"), self.aspect_combo)

        # Crop
        self.crop_combo = QComboBox()
        self.crop_combo.addItems([self.tr("Default"), "16:9", "4:3", "1:1", "2.35:1"])
        layout.addRow(self.tr("Crop:"), self.crop_combo)

        return widget

    def _create_subtitle_tab(self) -> QWidget:
        """Create subtitle settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)

        subtitle_settings = self.settings.get_subtitle_settings()

        # Enable subtitles
        self.sub_enabled_check = QCheckBox(self.tr("Enable Subtitles"))
        self.sub_enabled_check.setChecked(subtitle_settings.get("enabled", True))
        layout.addRow("", self.sub_enabled_check)

        # Font
        font_layout = QHBoxLayout()
        self.sub_font_btn = QPushButton(self.tr("Choose Font"))
        self.sub_font_btn.clicked.connect(self._choose_subtitle_font)
        font_layout.addWidget(self.sub_font_btn)
        self.sub_font_label = QLabel(self.tr("Default"))
        font_layout.addWidget(self.sub_font_label)
        layout.addRow(self.tr("Font:"), font_layout)

        # Font size
        self.sub_font_size_spin = QSpinBox()
        self.sub_font_size_spin.setRange(8, 72)
        self.sub_font_size_spin.setValue(subtitle_settings.get("font_size", 18))
        self.sub_font_size_spin.setSuffix(" pt")
        layout.addRow(self.tr("Font Size:"), self.sub_font_size_spin)

        # Font color
        color_layout = QHBoxLayout()
        self.sub_font_color_btn = QPushButton()
        self.sub_font_color_btn.setFixedSize(30, 24)
        self.sub_font_color_btn.setStyleSheet(f"background-color: {subtitle_settings.get('font_color', '#FFFFFF')}; border: 1px solid #888;")
        self.sub_font_color_btn.clicked.connect(lambda: self._choose_color("font"))
        color_layout.addWidget(self.sub_font_color_btn)
        color_layout.addWidget(QLabel(self.tr("Font Color")))
        color_layout.addStretch()
        layout.addRow("", color_layout)

        # Background color
        bg_layout = QHBoxLayout()
        self.sub_bg_color_btn = QPushButton()
        self.sub_bg_color_btn.setFixedSize(30, 24)
        self.sub_bg_color_btn.setStyleSheet(f"background-color: {subtitle_settings.get('background_color', '#00000080')}; border: 1px solid #888;")
        self.sub_bg_color_btn.clicked.connect(lambda: self._choose_color("background"))
        bg_layout.addWidget(self.sub_bg_color_btn)
        bg_layout.addWidget(QLabel(self.tr("Background Color")))
        bg_layout.addStretch()
        layout.addRow("", bg_layout)

        # Encoding
        self.sub_encoding_combo = QComboBox()
        self.sub_encoding_combo.addItems(["UTF-8", "UTF-16", "ISO-8859-1", "Windows-1252", "CP1256", "Auto"])
        self.sub_encoding_combo.setCurrentText(subtitle_settings.get("encoding", "utf-8"))
        layout.addRow(self.tr("Encoding:"), self.sub_encoding_combo)

        # Sync
        self.sub_sync_spin = QSpinBox()
        self.sub_sync_spin.setRange(-10000, 10000)
        self.sub_sync_spin.setSuffix(self.tr(" ms"))
        layout.addRow(self.tr("Subtitle Delay:"), self.sub_sync_spin)

        # Auto-load
        self.sub_autoload_check = QCheckBox(self.tr("Auto-load Subtitles"))
        self.sub_autoload_check.setChecked(True)
        layout.addRow("", self.sub_autoload_check)

        return widget

    def _create_network_tab(self) -> QWidget:
        """Create network settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)

        net_settings = self.settings.get_network_settings()

        # Buffer size
        self.buffer_spin = QSpinBox()
        self.buffer_spin.setRange(1024, 1048576)
        self.buffer_spin.setValue(net_settings.get("buffer_size", 8192))
        self.buffer_spin.setSuffix(" KB")
        layout.addRow(self.tr("Network Buffer:"), self.buffer_spin)

        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(net_settings.get("timeout", 30))
        self.timeout_spin.setSuffix(self.tr(" sec"))
        layout.addRow(self.tr("Connection Timeout:"), self.timeout_spin)

        # User agent
        self.user_agent_edit = QLineEdit()
        self.user_agent_edit.setText(net_settings.get("user_agent", USER_AGENT))
        layout.addRow(self.tr("User Agent:"), self.user_agent_edit)

        # Proxy
        self.proxy_check = QCheckBox(self.tr("Use Proxy"))
        layout.addRow("", self.proxy_check)

        proxy_layout = QFormLayout()
        self.proxy_host_edit = QLineEdit()
        self.proxy_host_edit.setPlaceholderText(self.tr("Host"))
        proxy_layout.addRow(self.tr("Proxy Host:"), self.proxy_host_edit)

        self.proxy_port_spin = QSpinBox()
        self.proxy_port_spin.setRange(1, 65535)
        self.proxy_port_spin.setValue(8080)
        proxy_layout.addRow(self.tr("Proxy Port:"), self.proxy_port_spin)

        self.proxy_user_edit = QLineEdit()
        self.proxy_user_edit.setPlaceholderText(self.tr("Username"))
        proxy_layout.addRow(self.tr("Username:"), self.proxy_user_edit)

        self.proxy_pass_edit = QLineEdit()
        self.proxy_pass_edit.setEchoMode(QLineEdit.Password)
        self.proxy_pass_edit.setPlaceholderText(self.tr("Password"))
        proxy_layout.addRow(self.tr("Password:"), self.proxy_pass_edit)

        layout.addRow(proxy_layout)

        return widget

    def _create_accessibility_tab(self) -> QWidget:
        """Create accessibility settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)

        acc_settings = self.settings.get_accessibility_settings()

        # Screen reader support
        self.sr_check = QCheckBox(self.tr("Screen Reader Support"))
        self.sr_check.setChecked(acc_settings.get("screen_reader_support", True))
        layout.addRow("", self.sr_check)

        # Announce position
        self.announce_pos_check = QCheckBox(self.tr("Announce Playback Position"))
        self.announce_pos_check.setChecked(acc_settings.get("announce_position", True))
        layout.addRow("", self.announce_pos_check)

        # Announce shortcuts
        self.announce_shortcuts_check = QCheckBox(self.tr("Announce Keyboard Shortcuts"))
        self.announce_shortcuts_check.setChecked(acc_settings.get("announce_shortcuts", True))
        layout.addRow("", self.announce_shortcuts_check)

        # Keyboard navigation
        self.kb_nav_check = QCheckBox(self.tr("Enhanced Keyboard Navigation"))
        self.kb_nav_check.setChecked(acc_settings.get("keyboard_navigation", True))
        layout.addRow("", self.kb_nav_check)

        # Show shortcuts button
        self.show_shortcuts_btn = QPushButton(self.tr("View All Shortcuts"))
        self.show_shortcuts_btn.clicked.connect(self._show_shortcuts)
        layout.addRow("", self.show_shortcuts_btn)

        return widget

    def _create_playlist_tab(self) -> QWidget:
        """Create playlist settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)

        pl_settings = self.settings.get_playlist_settings()

        # Auto-load playlist
        self.pl_autoload_check = QCheckBox(self.tr("Auto-load Playlist"))
        self.pl_autoload_check.setChecked(pl_settings.get("auto_load", True))
        layout.addRow("", self.pl_autoload_check)

        # Save on exit
        self.pl_save_check = QCheckBox(self.tr("Save Playlist on Exit"))
        self.pl_save_check.setChecked(pl_settings.get("save_on_exit", True))
        layout.addRow("", self.pl_save_check)

        # Loop playlist
        self.pl_loop_check = QCheckBox(self.tr("Loop Playlist"))
        self.pl_loop_check.setChecked(pl_settings.get("loop_playlist", False))
        layout.addRow("", self.pl_loop_check)

        # Max recent files
        self.pl_recent_spin = QSpinBox()
        self.pl_recent_spin.setRange(0, 50)
        self.pl_recent_spin.setValue(20)
        layout.addRow(self.tr("Max Recent Files:"), self.pl_recent_spin)

        return widget

    def _create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar
        toolbar_group = QGroupBox(self.tr("Toolbar"))
        toolbar_layout = QFormLayout(toolbar_group)

        self.toolbar_style_combo = QComboBox()
        self.toolbar_style_combo.addItems([self.tr("Icons Only"), self.tr("Text Only"), self.tr("Text Beside Icons"), self.tr("Text Under Icons")])
        toolbar_layout.addRow(self.tr("Style:"), self.toolbar_style_combo)

        self.toolbar_size_spin = QSpinBox()
        self.toolbar_size_spin.setRange(16, 64)
        self.toolbar_size_spin.setValue(32)
        self.toolbar_size_spin.setSuffix(" px")
        toolbar_layout.addRow(self.tr("Icon Size:"), self.toolbar_size_spin)

        layout.addWidget(toolbar_group)

        # Font
        font_group = QGroupBox(self.tr("Application Font"))
        font_layout = QHBoxLayout(font_group)

        self.font_btn = QPushButton(self.tr("Choose Font"))
        self.font_btn.clicked.connect(self._choose_font)
        font_layout.addWidget(self.font_btn)

        self.font_label = QLabel(self.tr("System Default"))
        font_layout.addWidget(self.font_label)

        layout.addWidget(font_group)

        # Custom CSS
        css_group = QGroupBox(self.tr("Custom Stylesheet"))
        css_layout = QVBoxLayout(css_group)

        self.css_edit = QLineEdit()
        self.css_edit.setPlaceholderText(self.tr("Path to custom QSS file"))
        css_layout.addWidget(self.css_edit)

        css_btn_layout = QHBoxLayout()
        self.css_browse_btn = QPushButton(self.tr("Browse"))
        self.css_browse_btn.clicked.connect(self._browse_css)
        css_btn_layout.addWidget(self.css_browse_btn)

        self.css_apply_btn = QPushButton(self.tr("Apply"))
        self.css_apply_btn.clicked.connect(self._apply_css)
        css_btn_layout.addWidget(self.css_apply_btn)

        css_layout.addLayout(css_btn_layout)
        layout.addWidget(css_group)

        return widget

    def _load_settings(self):
        """Load current settings into UI"""
        pass  # Settings loaded in _setup_ui

    def _apply_settings(self):
        """Apply settings"""
        # General
        self.settings.set_language(self.lang_combo.currentData())
        self.settings.set_theme("dark" if self.theme_combo.currentIndex() == 0 else "light")
        self.settings.set_high_contrast(self.high_contrast_check.isChecked())
        self.settings.set_hardware_acceleration(self.hw_accel_check.isChecked())
        try:
            modes = self.settings.STARTUP_MODES
            self.settings.set_startup_behavior(modes[self.startup_combo.currentIndex()])
        except (IndexError, AttributeError):
            pass

        # Playback
        self.settings.set_volume(self.volume_spin.value())
        self.settings.set_speed(self.speed_spin.value())
        self.settings.set_seek_interval(self.seek_spin.value())
        repeat_modes = ["off", "one", "all"]
        self.settings.set_repeat_mode(repeat_modes[self.repeat_combo.currentIndex()])
        self.settings.set_shuffle(self.shuffle_check.isChecked())

        # Audio
        eq_settings = self.settings.get_equalizer_settings()
        eq_settings["enabled"] = self.eq_enabled_check.isChecked()
        eq_settings["preset"] = self.eq_preset_combo.currentText()
        bands = [s.value() for s in self.eq_bands]
        eq_settings["bands"] = bands
        self.settings.set_equalizer_settings(eq_settings)
        self.settings.set_audio_sync(self.audio_sync_spin.value())

        # Video
        # Video settings would be applied here

        # Subtitle
        sub_settings = {
            "enabled": self.sub_enabled_check.isChecked(),
            "font_size": self.sub_font_size_spin.value(),
            "font_color": self.sub_font_color_btn.styleSheet().split("background-color: ")[1].split(";")[0],
            "background_color": self.sub_bg_color_btn.styleSheet().split("background-color: ")[1].split(";")[0],
            "encoding": self.sub_encoding_combo.currentText().lower().replace("-", "")
        }
        self.settings.set_subtitle_settings(sub_settings)

        # Network
        net_settings = {
            "buffer_size": self.buffer_spin.value(),
            "timeout": self.timeout_spin.value(),
            "user_agent": self.user_agent_edit.text()
        }
        self.settings.set_network_settings(net_settings)

        # Accessibility
        acc_settings = {
            "screen_reader_support": self.sr_check.isChecked(),
            "announce_position": self.announce_pos_check.isChecked(),
            "announce_shortcuts": self.announce_shortcuts_check.isChecked(),
            "keyboard_navigation": self.kb_nav_check.isChecked()
        }
        self.settings.set_accessibility_settings(acc_settings)

        # Playlist
        pl_settings = {
            "auto_load": self.pl_autoload_check.isChecked(),
            "save_on_exit": self.pl_save_check.isChecked(),
            "loop_playlist": self.pl_loop_check.isChecked(),
            "autoplay_next": self.autoplay_check.isChecked()
        }
        self.settings.set_playlist_settings(pl_settings)

        # Apply theme immediately
        self.settings.apply_theme(self.parent().app if hasattr(self.parent(), 'app') else None)

    def _reset_defaults(self):
        """Reset to defaults"""
        reply = QMessageBox.question(
            self, self.tr("Reset Settings"),
            self.tr("Are you sure you want to reset all settings to defaults?"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.settings.reset_to_defaults()
            self._load_settings()

    def _choose_font(self):
        """Choose application font"""
        font, ok = QFontDialog.getFont(QFont(), self, self.tr("Choose Font"))
        if ok:
            self.font_label.setText(f"{font.family()} {font.pointSize()}pt")
            # Apply font to application
            QApplication.instance().setFont(font)

    def _choose_subtitle_font(self):
        """Choose subtitle font"""
        font, ok = QFontDialog.getFont(QFont(), self, self.tr("Choose Subtitle Font"))
        if ok:
            self.sub_font_label.setText(f"{font.family()} {font.pointSize()}pt")

    def _choose_color(self, which: str):
        """Choose color"""
        btn = self.sub_font_color_btn if which == "font" else self.sub_bg_color_btn
        current_color = btn.styleSheet().split("background-color: ")[1].split(";")[0]
        color = QColorDialog.getColor(QColor(current_color), self, self.tr("Choose Color"))
        if color.isValid():
            btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #888;")

    def _browse_css(self):
        """Browse for custom CSS"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose Stylesheet"), "", self.tr("Stylesheets (*.qss *.css);;All Files (*.*)")
        )
        if file_path:
            self.css_edit.setText(file_path)

    def _apply_css(self):
        """Apply custom CSS"""
        file_path = self.css_edit.text()
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    css = f.read()
                QApplication.instance().setStyleSheet(css)
            except Exception as e:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to load stylesheet: {0}").format(str(e)))

    def _show_shortcuts(self):
        """Show shortcuts dialog"""
        from ui.dialogs.shortcuts_dialog import ShortcutsDialog
        dialog = ShortcutsDialog(self.accessibility, self)
        dialog.exec()

    # (attribute name, kind) pairs used to preserve the user's in-progress
    # edits across a live language-change rebuild of the dialog.
    _SNAPSHOT_SPEC = (
        ("lang_combo", "index"), ("theme_combo", "index"),
        ("high_contrast_check", "checked"), ("hw_accel_check", "checked"),
        ("startup_combo", "index"),
        ("volume_spin", "value"), ("speed_spin", "value"),
        ("seek_spin", "value"), ("repeat_combo", "index"),
        ("shuffle_check", "checked"), ("autoplay_check", "checked"),
        ("remember_pos_check", "checked"),
        ("audio_device_combo", "index"), ("audio_channels_combo", "index"),
        ("audio_sync_spin", "value"), ("eq_enabled_check", "checked"),
        ("eq_preset_combo", "index"),
        ("video_output_combo", "index"), ("deinterlace_combo", "index"),
        ("hw_decode_check", "checked"), ("postprocess_check", "checked"),
        ("aspect_combo", "index"), ("crop_combo", "index"),
        ("sub_enabled_check", "checked"), ("sub_font_label", "text"),
        ("sub_font_size_spin", "value"), ("sub_font_color_btn", "style"),
        ("sub_bg_color_btn", "style"), ("sub_encoding_combo", "index"),
        ("sub_sync_spin", "value"), ("sub_autoload_check", "checked"),
        ("buffer_spin", "value"), ("timeout_spin", "value"),
        ("user_agent_edit", "text"), ("proxy_check", "checked"),
        ("proxy_host_edit", "text"), ("proxy_port_spin", "value"),
        ("proxy_user_edit", "text"), ("proxy_pass_edit", "text"),
        ("sr_check", "checked"), ("announce_pos_check", "checked"),
        ("announce_shortcuts_check", "checked"), ("kb_nav_check", "checked"),
        ("pl_autoload_check", "checked"), ("pl_save_check", "checked"),
        ("pl_loop_check", "checked"), ("pl_recent_spin", "value"),
        ("toolbar_style_combo", "index"), ("toolbar_size_spin", "value"),
        ("font_label", "text"), ("css_edit", "text"),
    )

    def _snapshot_values(self) -> dict:
        """Capture the current (possibly unsaved) widget values."""
        data = {"_tab": self.tabs.currentIndex()}
        for attr, kind in self._SNAPSHOT_SPEC:
            widget = getattr(self, attr, None)
            if widget is None:
                continue
            try:
                if kind == "index":
                    data[attr] = widget.currentIndex()
                elif kind == "checked":
                    data[attr] = widget.isChecked()
                elif kind == "value":
                    data[attr] = widget.value()
                elif kind == "text":
                    data[attr] = widget.text()
                elif kind == "style":
                    data[attr] = widget.styleSheet()
            except Exception:
                pass
        bands = getattr(self, "eq_bands", None)
        if bands:
            data["_eq_bands"] = [s.value() for s in bands]
        return data

    def _restore_values(self, data: dict):
        """Re-apply values captured by :meth:`_snapshot_values`."""
        for attr, kind in self._SNAPSHOT_SPEC:
            if attr not in data:
                continue
            widget = getattr(self, attr, None)
            if widget is None:
                continue
            try:
                if kind == "index":
                    widget.setCurrentIndex(data[attr])
                elif kind == "checked":
                    widget.setChecked(data[attr])
                elif kind == "value":
                    widget.setValue(data[attr])
                elif kind == "text":
                    widget.setText(data[attr])
                elif kind == "style":
                    widget.setStyleSheet(data[attr])
            except Exception:
                pass
        bands = getattr(self, "eq_bands", None)
        if bands and "_eq_bands" in data:
            for slider, value in zip(bands, data["_eq_bands"]):
                slider.setValue(value)
        try:
            self.tabs.setCurrentIndex(data.get("_tab", 0))
        except Exception:
            pass

    def retranslate(self, *args):
        """Re-translate every string in the dialog without losing edits.

        Called automatically when the application language changes so the
        user sees the new language immediately, even while this dialog is
        open.
        """
        if getattr(self, "_retranslating", False):
            return
        self._retranslating = True
        try:
            snapshot = self._snapshot_values()
            tabs = self.tabs
            while tabs.count():
                widget = tabs.widget(0)
                tabs.removeTab(0)
                if widget is not None:
                    widget.deleteLater()
            tabs.addTab(self._create_general_tab(), self.tr("General"))
            tabs.addTab(self._create_playback_tab(), self.tr("Playback"))
            tabs.addTab(self._create_audio_tab(), self.tr("Audio"))
            tabs.addTab(self._create_video_tab(), self.tr("Video"))
            tabs.addTab(self._create_subtitle_tab(), self.tr("Subtitles"))
            tabs.addTab(self._create_network_tab(), self.tr("Network"))
            tabs.addTab(self._create_accessibility_tab(), self.tr("Accessibility"))
            tabs.addTab(self._create_playlist_tab(), self.tr("Playlist"))
            tabs.addTab(self._create_appearance_tab(), self.tr("Appearance"))
            self.setWindowTitle(self.tr("Settings"))
            self._restore_values(snapshot)
        finally:
            self._retranslating = False

    def accept(self):
        """Accept dialog"""
        self._apply_settings()
        super().accept()