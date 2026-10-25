"""
URL Dialog - Open network stream
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDialogButtonBox, QComboBox, QCheckBox,
    QWidget, QFormLayout
)


class UrlDialog(QDialog):
    """Open URL dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Open Network Stream"))
        self.resize(500, 150)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)

        # URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel(self.tr("URL:")))

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText(self.tr("Enter media URL (http://, rtsp://, rtmp://, etc.)"))
        url_layout.addWidget(self.url_edit)

        layout.addLayout(url_layout)

        # Options
        options_layout = QHBoxLayout()

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            self.tr("Auto Detect"),
            self.tr("HTTP/HTTPS"),
            self.tr("RTSP"),
            self.tr("RTMP"),
            self.tr("MMS"),
            self.tr("RTP"),
            self.tr("HLS (.m3u8)"),
            self.tr("DASH (.mpd)")
        ])
        options_layout.addWidget(QLabel(self.tr("Stream Type:")))
        options_layout.addWidget(self.type_combo)

        layout.addLayout(options_layout)

        # Advanced options
        self.advanced_check = QCheckBox(self.tr("Advanced Options"))
        self.advanced_check.toggled.connect(self._toggle_advanced)
        layout.addWidget(self.advanced_check)

        self.advanced_widget = QWidget()
        advanced_layout = QFormLayout(self.advanced_widget)

        self.user_agent_edit = QLineEdit()
        self.user_agent_edit.setPlaceholderText(self.tr("Custom User Agent"))
        advanced_layout.addRow(self.tr("User Agent:"), self.user_agent_edit)

        self.referer_edit = QLineEdit()
        self.referer_edit.setPlaceholderText(self.tr("Referer"))
        advanced_layout.addRow(self.tr("Referer:"), self.referer_edit)

        self.cookies_edit = QLineEdit()
        self.cookies_edit.setPlaceholderText(self.tr("Cookies"))
        advanced_layout.addRow(self.tr("Cookies:"), self.cookies_edit)

        self.headers_edit = QLineEdit()
        self.headers_edit.setPlaceholderText(self.tr("Custom Headers (JSON)"))
        advanced_layout.addRow(self.tr("Headers:"), self.headers_edit)

        self.advanced_widget.setVisible(False)
        layout.addWidget(self.advanced_widget)

        # Recent URLs
        recent_layout = QHBoxLayout()
        recent_layout.addWidget(QLabel(self.tr("Recent:")))
        self.recent_combo = QComboBox()
        self.recent_combo.addItem(self.tr("Select recent URL"))
        self.recent_combo.currentTextChanged.connect(self._on_recent_selected)
        recent_layout.addWidget(self.recent_combo)
        layout.addLayout(recent_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _toggle_advanced(self, checked: bool):
        """Toggle advanced options"""
        self.advanced_widget.setVisible(checked)

    def _on_recent_selected(self, text: str):
        """Handle recent URL selection"""
        if text and text != self.tr("Select recent URL"):
            self.url_edit.setText(text)

    def get_url(self) -> str:
        """Get entered URL"""
        return self.url_edit.text().strip()

    def get_options(self) -> dict:
        """Get stream options"""
        return {
            "type": self.type_combo.currentText(),
            "user_agent": self.user_agent_edit.text(),
            "referer": self.referer_edit.text(),
            "cookies": self.cookies_edit.text(),
            "headers": self.headers_edit.text()
        }