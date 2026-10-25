"""
Subtitle Options Dialog - Pre-playback subtitle configuration
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QGroupBox, QDialogButtonBox,
    QListWidget, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from media.subtitle_manager import SubtitleManager, SyncMode


class SubtitleOptionsDialog(QDialog):
    """Dialog for configuring subtitle options before playback"""
    
    # Signal emitted when user confirms settings
    settings_confirmed = Signal(dict)  # settings dict
    
    def __init__(self, subtitle_manager: SubtitleManager, video_path: str, parent=None):
        super().__init__(parent)
        self.subtitle_manager = subtitle_manager
        self.video_path = video_path
        self.detected_subtitle = None
        self.available_subtitles = []
        self.selected_subtitle_index = -1
        
        self.setWindowTitle(self.tr("Subtitle Options"))
        self.resize(500, 450)
        self.setModal(True)
        
        self._setup_ui()
        self._detect_subtitles()
        
    def _setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title_label = QLabel(self.tr("Subtitle Configuration"))
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Detected subtitle info
        self.subtitle_info_group = QGroupBox(self.tr("Detected Subtitle"))
        info_layout = QVBoxLayout(self.subtitle_info_group)
        
        self.subtitle_info_label = QLabel(self.tr("No subtitle detected"))
        self.subtitle_info_label.setWordWrap(True)
        info_layout.addWidget(self.subtitle_info_label)
        
        layout.addWidget(self.subtitle_info_group)
        
        # Subtitle selection (if multiple)
        self.subtitle_selection_group = QGroupBox(self.tr("Select Subtitle Track"))
        selection_layout = QVBoxLayout(self.subtitle_selection_group)
        
        self.subtitle_list = QListWidget()
        self.subtitle_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.subtitle_list.itemClicked.connect(self._on_subtitle_selected)
        selection_layout.addWidget(self.subtitle_list)
        
        self.subtitle_selection_group.setVisible(False)
        layout.addWidget(self.subtitle_selection_group)
        
        # Sync mode selection
        sync_group = QGroupBox(self.tr("Synchronization Mode"))
        sync_layout = QVBoxLayout(sync_group)
        
        self.sync_mode_combo = QComboBox()
        self.sync_mode_combo.addItem(
            self.tr("Real-time Sync (synchronized with speech)"),
            SyncMode.REAL_TIME.value
        )
        self.sync_mode_combo.addItem(
            self.tr("Paragraph by Paragraph (read paragraph by paragraph)"),
            SyncMode.PARAGRAPH_BY_PARAGRAPH.value
        )
        sync_layout.addWidget(self.sync_mode_combo)
        
        layout.addWidget(sync_group)
        
        # Options
        options_group = QGroupBox(self.tr("Options"))
        options_layout = QVBoxLayout(options_group)
        
        self.enable_subtitles_check = QCheckBox(self.tr("Enable subtitles"))
        self.enable_subtitles_check.setChecked(True)
        options_layout.addWidget(self.enable_subtitles_check)
        
        self.auto_load_check = QCheckBox(self.tr("Auto-load subtitles for future videos"))
        self.auto_load_check.setChecked(True)
        options_layout.addWidget(self.auto_load_check)
        
        layout.addWidget(options_group)
        
        # Subtitle offset
        offset_group = QGroupBox(self.tr("Sync Adjustment"))
        offset_layout = QHBoxLayout(offset_group)
        
        offset_layout.addWidget(QLabel(self.tr("Offset (seconds):")))
        from PySide6.QtWidgets import QDoubleSpinBox
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-60.0, 60.0)
        self.offset_spin.setSingleStep(0.5)
        self.offset_spin.setValue(0.0)
        self.offset_spin.setSuffix(" s")
        offset_layout.addWidget(self.offset_spin)
        
        layout.addWidget(offset_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def _detect_subtitles(self):
        """Auto-detect subtitle files"""
        # Check for local subtitle files
        self.detected_subtitle = self.subtitle_manager.auto_detect_subtitle(self.video_path)
        
        if self.detected_subtitle:
            # Load the detected subtitle
            if self.subtitle_manager.load_subtitle(self.detected_subtitle):
                sub = self.subtitle_manager.current_subtitle
                self.subtitle_info_label.setText(
                    self.tr("Found: {0}\nFormat: {1}\nEntries: {2}").format(
                        Path(self.detected_subtitle).name,
                        sub.format.upper(),
                        len(sub.entries),
                    )
                )
                
                # Check for alternative subtitle files
                self._find_alternative_subtitles()
        else:
            self.subtitle_info_label.setText(self.tr("No subtitle file found for this video"))
            
    def _find_alternative_subtitles(self):
        """Find alternative subtitle files in same directory"""
        video_dir = Path(self.video_path).parent
        video_stem = Path(self.video_path).stem
        
        subtitle_extensions = ['.srt', '.ass', '.ssa', '.vtt', '.sub']
        
        for ext in subtitle_extensions:
            for sub_file in video_dir.glob(f"{video_stem}*{ext}"):
                if str(sub_file) != self.detected_subtitle:
                    self.available_subtitles.append(str(sub_file))
                    
        if self.available_subtitles:
            self.subtitle_selection_group.setVisible(True)
            self.subtitle_list.addItem(f"Auto-detected: {Path(self.detected_subtitle).name}")
            self.selected_subtitle_index = 0
            
            for sub in self.available_subtitles:
                self.subtitle_list.addItem(f"Alternative: {Path(sub).name}")
                
    def _on_subtitle_selected(self, item):
        """Handle subtitle selection"""
        self.selected_subtitle_index = self.subtitle_list.row(item)
        
    def _on_accept(self):
        """Handle OK button"""
        settings = {
            'enabled': self.enable_subtitles_check.isChecked(),
            'auto_load': self.auto_load_check.isChecked(),
            'sync_mode': self.sync_mode_combo.currentData(),
            'offset': self.offset_spin.value(),
            'subtitle_path': self.detected_subtitle if self.selected_subtitle_index == 0 else 
                           (self.available_subtitles[self.selected_subtitle_index - 1] if self.selected_subtitle_index > 0 and self.available_subtitles else None)
        }
        
        self.settings_confirmed.emit(settings)
        self.accept()


class SubtitleExportDialog(QDialog):
    """Dialog for exporting subtitles"""
    
    export_requested = Signal(str, float, float)  # format, start_time, end_time
    
    def __init__(self, subtitle_manager, parent=None):
        super().__init__(parent)
        self.subtitle_manager = subtitle_manager
        
        self.setWindowTitle(self.tr("Export Subtitles"))
        self.resize(400, 300)
        self.setModal(True)
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title = QLabel(self.tr("Export Subtitles"))
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle info
        if self.subtitle_manager.current_subtitle:
            info = QLabel(
                self.tr("Subtitle: {0} entries\nDuration: {1}").format(
                    len(self.subtitle_manager.current_subtitle.entries),
                    self._format_time(self.subtitle_manager.current_subtitle.entries[-1].end_time if self.subtitle_manager.current_subtitle.entries else 0),
                )
            )
            info.setWordWrap(True)
            layout.addWidget(info)
        
        # Export format
        format_group = QGroupBox(self.tr("Export Format"))
        format_layout = QVBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Text (.txt)",
            "Word Document (.docx)",
            "PDF (.pdf)",
            "SRT (.srt)"
        ])
        format_layout.addWidget(self.format_combo)
        layout.addWidget(format_group)
        
        # Range selection
        range_group = QGroupBox(self.tr("Export Range"))
        range_layout = QVBoxLayout(range_group)
        
        self.range_combo = QComboBox()
        self.range_combo.addItems([
            self.tr("All subtitles"),
            self.tr("Up to current position"),
            self.tr("From current position to end"),
            self.tr("Custom range")
        ])
        range_layout.addWidget(self.range_combo)
        
        # Custom range inputs
        from PySide6.QtWidgets import QDoubleSpinBox
        self.custom_start = QDoubleSpinBox()
        self.custom_start.setRange(0, 86400)
        self.custom_start.setSuffix(" s")
        self.custom_start.setVisible(False)
        
        self.custom_end = QDoubleSpinBox()
        self.custom_end.setRange(0, 86400)
        self.custom_end.setSuffix(" s")
        self.custom_end.setVisible(False)
        
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel(self.tr("Start:")))
        custom_layout.addWidget(self.custom_start)
        custom_layout.addWidget(QLabel(self.tr("End:")))
        custom_layout.addWidget(self.custom_end)
        range_layout.addLayout(custom_layout)
        
        self.range_combo.currentIndexChanged.connect(self._on_range_changed)
        layout.addWidget(range_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def _on_range_changed(self, index):
        """Handle range selection change"""
        is_custom = index == 3
        self.custom_start.setVisible(is_custom)
        self.custom_end.setVisible(is_custom)
        
    def _on_accept(self):
        """Handle OK button"""
        format_map = {
            0: 'txt',
            1: 'docx',
            2: 'pdf',
            3: 'srt'
        }
        
        format_type = format_map[self.format_combo.currentIndex()]
        range_type = self.range_combo.currentIndex()
        
        start_time = 0
        end_time = None
        
        if range_type == 1:  # Up to current
            # Would need current position from parent
            pass
        elif range_type == 2:  # From current to end
            pass
        elif range_type == 3:  # Custom
            start_time = self.custom_start.value()
            end_time = self.custom_end.value()
            
        self.export_requested.emit(format_type, start_time, end_time)
        self.accept()
        
    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"