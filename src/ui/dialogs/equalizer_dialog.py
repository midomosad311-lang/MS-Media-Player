"""
Equalizer Dialog - Audio equalizer
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSlider, QLabel,
    QPushButton, QComboBox, QCheckBox, QDialogButtonBox,
    QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt
from media.media_engine import MediaEngine
from settings.settings_manager import SettingsManager


class EqualizerDialog(QDialog):
    """Equalizer dialog"""

    def __init__(self, media_engine: MediaEngine, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.media_engine = media_engine
        self.settings = settings_manager
        self.setWindowTitle(self.tr("Equalizer"))
        self.resize(500, 400)
        self.setModal(True)

        self.bands = []
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)

        # Enable checkbox
        self.enabled_check = QCheckBox(self.tr("Enable Equalizer"))
        self.enabled_check.toggled.connect(self._on_enabled_changed)
        layout.addWidget(self.enabled_check)

        # Preset
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel(self.tr("Preset:")))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            self.tr("Flat"), self.tr("Classical"), self.tr("Club"), self.tr("Dance"), self.tr("Full Bass"),
            self.tr("Full Bass & Treble"), self.tr("Full Treble"), self.tr("Headphones"),
            self.tr("Large Hall"), self.tr("Live"), self.tr("Party"), self.tr("Pop"), self.tr("Reggae"),
            self.tr("Rock"), self.tr("Ska"), self.tr("Soft"), self.tr("Techno"), self.tr("Custom")
        ])
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)

        # Preamp
        preamp_layout = QHBoxLayout()
        preamp_layout.addWidget(QLabel(self.tr("Preamp:")))
        self.preamp_slider = QSlider(Qt.Horizontal)
        self.preamp_slider.setRange(-20, 20)
        self.preamp_slider.setValue(0)
        self.preamp_slider.setTickPosition(QSlider.TicksBelow)
        self.preamp_slider.setTickInterval(5)
        self.preamp_slider.valueChanged.connect(self._on_preamp_changed)
        preamp_layout.addWidget(self.preamp_slider)
        self.preamp_label = QLabel("0 dB")
        self.preamp_label.setMinimumWidth(50)
        preamp_layout.addWidget(self.preamp_label)
        layout.addLayout(preamp_layout)

        # Frequency bands
        bands_group = QGroupBox(self.tr("Frequency Bands"))
        bands_layout = QGridLayout(bands_group)

        frequencies = [
            (60, "Hz"), (170, "Hz"), (310, "Hz"), (600, "Hz"),
            (1, "kHz"), (3, "kHz"), (6, "kHz"), (12, "kHz"),
            (14, "kHz"), (16, "kHz")
        ]

        for i, (freq, unit) in enumerate(frequencies):
            band_layout = QVBoxLayout()

            # Frequency label
            freq_label = QLabel(f"{freq} {unit}")
            freq_label.setAlignment(Qt.AlignCenter)
            band_layout.addWidget(freq_label)

            # Slider
            slider = QSlider(Qt.Vertical)
            slider.setRange(-20, 20)
            slider.setValue(0)
            slider.setTickPosition(QSlider.TicksBothSides)
            slider.setTickInterval(5)
            slider.setFixedHeight(120)
            slider.valueChanged.connect(lambda v, idx=i: self._on_band_changed(idx, v))
            band_layout.addWidget(slider, alignment=Qt.AlignCenter)

            # Value label
            value_label = QLabel("0 dB")
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setMinimumHeight(20)
            band_layout.addWidget(value_label)

            self.bands.append({
                "slider": slider,
                "value_label": value_label,
                "freq": freq,
                "unit": unit
            })

            bands_layout.addLayout(band_layout, 0, i)

        layout.addWidget(bands_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.reset_btn = QPushButton(self.tr("Reset"))
        self.reset_btn.clicked.connect(self._reset_bands)
        button_layout.addWidget(self.reset_btn)

        self.flat_btn = QPushButton(self.tr("Flat"))
        self.flat_btn.clicked.connect(self._set_flat)
        button_layout.addWidget(self.flat_btn)

        button_layout.addStretch()

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_equalizer)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)

    def _load_settings(self):
        """Load equalizer settings"""
        eq_settings = self.settings.get_equalizer_settings()
        self.enabled_check.setChecked(eq_settings.get("enabled", False))
        preset = eq_settings.get("preset", "Flat")
        index = self.preset_combo.findText(preset)
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)

        bands = eq_settings.get("bands", [0] * 10)
        for i, value in enumerate(bands):
            if i < len(self.bands):
                self.bands[i]["slider"].setValue(value)
                self.bands[i]["value_label"].setText(f"{value} dB")

    def _on_enabled_changed(self, enabled: bool):
        """Handle enable/disable"""
        self.media_engine.enable_equalizer(enabled)
        for band in self.bands:
            band["slider"].setEnabled(enabled)
        self.preamp_slider.setEnabled(enabled)
        self.preset_combo.setEnabled(enabled)

    def _on_preset_changed(self, preset: str):
        """Handle preset change"""
        if preset == self.tr("Custom"):
            return

        try:
            import vlc
            presets = vlc.AudioEqualizer.get_preset_names()
            if preset in presets:
                self.media_engine.set_equalizer_preset(preset)
                # Update sliders
                for i in range(10):
                    value = self.media_engine.get_equalizer_band(i)
                    self.bands[i]["slider"].setValue(int(value))
                    self.bands[i]["value_label"].setText(f"{int(value)} dB")
        except:
            pass

    def _on_preamp_changed(self, value: int):
        """Handle preamp change"""
        self.preamp_label.setText(f"{value} dB")
        # Apply preamp (would need VLC support)

    def _on_band_changed(self, index: int, value: int):
        """Handle band change"""
        self.bands[index]["value_label"].setText(f"{value} dB")
        self.media_engine.set_equalizer_band(index, float(value))

    def _reset_bands(self):
        """Reset all bands to 0"""
        for band in self.bands:
            band["slider"].setValue(0)
            band["value_label"].setText("0 dB")
        self.preamp_slider.setValue(0)
        self.preamp_label.setText("0 dB")
        self.preset_combo.setCurrentText(self.tr("Custom"))

    def _set_flat(self):
        """Set flat response"""
        self._reset_bands()
        self.preset_combo.setCurrentText(self.tr("Flat"))
        self.media_engine.set_equalizer_preset(self.tr("Flat"))

    def _apply_equalizer(self):
        """Apply equalizer settings"""
        # Save to settings
        eq_settings = {
            "enabled": self.enabled_check.isChecked(),
            "preset": self.preset_combo.currentText(),
            "bands": [b["slider"].value() for b in self.bands]
        }
        self.settings.set_equalizer_settings(eq_settings)

    def accept(self):
        """Accept dialog"""
        self._apply_equalizer()
        super().accept()