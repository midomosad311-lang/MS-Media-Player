"""
Subtitle Settings Panel - Runtime subtitle controls
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QMenu
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction

from media.subtitle_manager import SubtitleManager, SyncMode


class SubtitleSettingsPanel(QWidget):
    """Runtime subtitle settings panel for control panel integration"""
    
    # Signals
    sync_mode_changed = Signal(str)  # SyncMode value
    offset_changed = Signal(float)   # offset in seconds
    visibility_toggled = Signal(bool)  # visibility state
    subtitle_selected = Signal(str)  # subtitle path
    export_requested = Signal(str, float, float)  # format, start, end
    
    def __init__(self, subtitle_manager: SubtitleManager, parent=None):
        super().__init__(parent)
        self.subtitle_manager = subtitle_manager
        
        self.setFixedHeight(160)
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            self.sizePolicy().verticalPolicy()
        )
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Main controls row
        main_row = QHBoxLayout()
        main_row.setSpacing(8)
        
        # Subtitle toggle
        self.subtitle_toggle = QPushButton("📝 CC")
        self.subtitle_toggle.setCheckable(True)
        self.subtitle_toggle.setChecked(True)
        self.subtitle_toggle.setMinimumSize(50, 36)
        self.subtitle_toggle.setToolTip("Toggle subtitles (Ctrl+T)")
        self.subtitle_toggle.clicked.connect(self._on_toggle_visibility)
        main_row.addWidget(self.subtitle_toggle)
        
        # Subtitle track selector
        self.track_combo = QComboBox()
        self.track_combo.addItem("Select Subtitle...")
        self.track_combo.setMinimumWidth(180)
        self.track_combo.setToolTip("Select subtitle track")
        self.track_combo.currentTextChanged.connect(self._on_track_changed)
        main_row.addWidget(self.track_combo)
        
        # Sync mode selector
        self.sync_mode_combo = QComboBox()
        self.sync_mode_combo.addItem("⚡ Real-time Sync", SyncMode.REAL_TIME.value)
        self.sync_mode_combo.addItem("📖 Paragraph by Paragraph", SyncMode.PARAGRAPH_BY_PARAGRAPH.value)
        self.sync_mode_combo.setToolTip("Subtitle synchronization mode")
        self.sync_mode_combo.currentIndexChanged.connect(self._on_sync_mode_changed)
        main_row.addWidget(self.sync_mode_combo)
        
        # Offset control
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(QLabel("⏱"))
        self.offset_slider = QSlider(Qt.Horizontal)
        self.offset_slider.setRange(-500, 500)  # -50 to +50 seconds * 10
        self.offset_slider.setValue(0)
        self.offset_slider.setFixedWidth(120)
        self.offset_slider.setToolTip("Subtitle offset (Ctrl+Shift+Left/Right)")
        self.offset_slider.valueChanged.connect(self._on_offset_changed)
        offset_layout.addWidget(self.offset_slider)
        
        self.offset_label = QLabel("0.0s")
        self.offset_label.setMinimumWidth(45)
        offset_layout.addWidget(self.offset_label)
        main_row.addLayout(offset_layout)
        
        # Menu button
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFixedSize(36, 36)
        self.menu_btn.setToolTip("Subtitle options")
        self.menu_btn.clicked.connect(self._show_menu)
        main_row.addWidget(self.menu_btn)
        
        layout.addLayout(main_row)
        
        # Current subtitle display
        self.current_text_label = QLabel("")
        self.current_text_label.setWordWrap(True)
        self.current_text_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background-color: rgba(0, 0, 0, 0.7);
                padding: 8px;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        self.current_text_label.setAlignment(Qt.AlignCenter)
        self.current_text_label.setMinimumHeight(40)
        layout.addWidget(self.current_text_label)
        
        # Update timer for current subtitle text
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_current_text)
        self.update_timer.setInterval(500)
        
    def _connect_signals(self):
        """Connect subtitle manager signals"""
        if self.subtitle_manager:
            self.subtitle_manager.current_subtitle_changed.connect(self._on_subtitle_changed)
            self.subtitle_manager.sync_mode_changed.connect(self._on_external_sync_mode_changed)
            
    def _on_toggle_visibility(self, checked: bool):
        """Handle subtitle visibility toggle"""
        self.subtitle_manager.set_visible(checked)
        self.visibility_toggled.emit(checked)
        
    def _on_track_changed(self, text: str):
        """Handle subtitle track selection"""
        if text != "Select Subtitle...":
            # Find and load the selected subtitle
            pass
            
    def _on_sync_mode_changed(self, index: int):
        """Handle sync mode change"""
        mode = self.sync_mode_combo.currentData()
        if mode:
            # mode is a string value like "real_time" or "paragraph"
            self.subtitle_manager.set_sync_mode(SyncMode(mode))
            self.sync_mode_changed.emit(mode)
            
    def _on_offset_changed(self, value: int):
        """Handle offset slider change"""
        offset = value / 10.0
        self.offset_label.setText(f"{offset:+.1f}s")
        self.subtitle_manager.set_offset(offset)
        self.offset_changed.emit(offset)
        
    def _show_menu(self):
        """Show subtitle options menu"""
        menu = QMenu(self)
        
        # Load external subtitle
        load_action = QAction("Load External Subtitle...", self)
        load_action.triggered.connect(self._load_external_subtitle)
        menu.addAction(load_action)
        
        menu.addSeparator()
        
        # Export options
        export_menu = menu.addMenu("Export Subtitles")
        
        export_txt = QAction("Export as Text (.txt)", self)
        export_txt.triggered.connect(lambda: self.export_requested.emit('txt', 0, 0))
        export_menu.addAction(export_txt)
        
        export_docx = QAction("Export as Word (.docx)", self)
        export_docx.triggered.connect(lambda: self.export_requested.emit('docx', 0, 0))
        export_menu.addAction(export_docx)
        
        export_pdf = QAction("Export as PDF (.pdf)", self)
        export_pdf.triggered.connect(lambda: self.export_requested.emit('pdf', 0, 0))
        export_menu.addAction(export_pdf)
        
        menu.addSeparator()
        
        # Subtitle options
        options_action = QAction("Subtitle Options...", self)
        options_action.triggered.connect(self._show_options_dialog)
        menu.addAction(options_action)
        
        menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
        
    def _load_external_subtitle(self):
        """Load external subtitle file"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Subtitle", "",
            "Subtitle Files (*.srt *.ass *.ssa *.vtt *.sub);;All Files (*.*)"
        )
        
        if file_path:
            self.subtitle_manager.load_subtitle(file_path)
            self._update_track_list()
            
    def _update_track_list(self):
        """Update track combo box"""
        self.track_combo.blockSignals(True)
        self.track_combo.clear()
        self.track_combo.addItem("Select Subtitle...")
        
        # Add loaded subtitle
        if self.subtitle_manager.current_subtitle:
            self.track_combo.addItem(f"Loaded: {self.subtitle_manager.current_subtitle.path}")
            
        self.track_combo.blockSignals(False)
        
    def _on_subtitle_changed(self, text: str):
        """Handle current subtitle text change"""
        pass  # Handled by update timer
        
    def _on_external_sync_mode_changed(self, mode: str):
        """Handle external sync mode change"""
        index = self.sync_mode_combo.findData(mode)
        if index >= 0:
            self.sync_mode_combo.blockSignals(True)
            self.sync_mode_combo.setCurrentIndex(index)
            self.sync_mode_combo.blockSignals(False)
            
    def _update_current_text(self):
        """Update current subtitle text display"""
        if not self.subtitle_manager or not self.subtitle_manager.current_subtitle:
            self.current_text_label.setText("")
            return
            
        # Get current position from parent (would need to be set externally)
        # This is a placeholder - actual implementation would get position from media engine
        current_time = getattr(self, '_current_position', 0)
        
        text = self.subtitle_manager.get_current_text(current_time)
        if text:
            self.current_text_label.setText(text)
        else:
            self.current_text_label.setText("")
            
    def _show_options_dialog(self):
        """Show subtitle options dialog"""
        
        # Would need video path from parent
        pass
        
    def set_subtitle_manager(self, manager: SubtitleManager):
        """Set subtitle manager"""
        self.subtitle_manager = manager
        self._connect_signals()
        self._update_track_list()
        
    def set_current_position(self, position: float):
        """Update current position for subtitle display"""
        self._current_position = position
        self._update_current_text()
        
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        self.update_timer.start()
        self._update_track_list()
        
    def hideEvent(self, event):
        """Handle hide event"""
        super().hideEvent(event)
        self.update_timer.stop()