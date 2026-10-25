"""
About Dialog - localized, detailed usage guide with credits & contact.
"""

from PySide6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QPushButton, QTextBrowser, QVBoxLayout,
)
from PySide6.QtCore import Qt, QTimer

from core.app_meta import APP_NAME, CONTACT_NUMBER, CONTACT_NUMBER_DISPLAY
from i18n.about_content import RTL_LANGUAGES, get_about_text


class AboutDialog(QDialog):
    """Localized, accessible About dialog with credits and contact details.

    The dialog shows a full usage guide, the developer credit and the support
    contact number, plus a dedicated *Copy Number* button that copies only the
    number (in international form) to the clipboard.
    """

    def __init__(self, language_code, app_title=None, parent=None,
                 translation_manager=None, accessibility_manager=None):
        super().__init__(parent)
        self.translation = translation_manager
        self.accessibility = accessibility_manager
        # The product name is never translated.
        self.app_title = APP_NAME

        self.setModal(True)
        self.resize(720, 640)

        layout = QVBoxLayout(self)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        layout.addWidget(self.browser)

        # Contact / copy-number row, then a Close button.
        button_layout = QHBoxLayout()

        self.copy_button = QPushButton()
        self.copy_button.setAutoDefault(False)
        self.copy_button.setDefault(False)
        self.copy_button.clicked.connect(self._copy_number)
        button_layout.addWidget(self.copy_button)

        button_layout.addStretch(1)

        self.close_button = QPushButton()
        self.close_button.setDefault(True)
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        self._reset_copy_timer = QTimer(self)
        self._reset_copy_timer.setSingleShot(True)
        self._reset_copy_timer.timeout.connect(self._reset_copy_button)

        self.retranslate()
        self.close_button.setFocus()

    # ------------------------------------------------------------------
    def _copy_number(self):
        """Copy only the contact number (international form) to the clipboard."""
        QApplication.clipboard().setText(CONTACT_NUMBER)
        self.copy_button.setText(self.tr("Number copied"))
        self.copy_button.setAccessibleName(self.tr("Number copied"))
        self._announce(self.tr("Number copied") + ": " + CONTACT_NUMBER_DISPLAY)
        self._reset_copy_timer.start(2000)

    def _reset_copy_button(self):
        self.copy_button.setText(self.tr("Copy Number"))
        self.copy_button.setAccessibleName(
            self.tr("Copy Number") + ": " + CONTACT_NUMBER_DISPLAY
        )

    def _announce(self, text: str):
        if self.accessibility is not None:
            try:
                self.accessibility.announce(text)
                return
            except Exception:
                pass
        # Fallback: let the platform accessibility layer know something changed
        # so tools that poll the focused widget can still read it.
        try:
            from PySide6.QtGui import QAccessible
            QAccessible.updateAccessibility(self.copy_button, QAccessible.Event.NameChanged)
        except Exception:
            pass

    # ------------------------------------------------------------------
    def retranslate(self, *args):
        """(Re)apply all localized strings for the current language."""
        if self.translation is not None:
            try:
                self.language_code = self.translation.get_current_language()
            except Exception:
                pass
        else:
            self.language_code = getattr(self, "language_code", "en")

        # Right-to-left languages (Arabic) render the document and buttons RTL.
        if self.language_code in RTL_LANGUAGES:
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)

        self.browser.setHtml(get_about_text(self.language_code))
        self.browser.setAccessibleName(self.app_title)
        # Expose the contact information to screen readers too.
        self.browser.setAccessibleDescription(
            f"{self.tr('Contact number')}: {CONTACT_NUMBER_DISPLAY}"
        )

        self.copy_button.setText(self.tr("Copy Number"))
        self.copy_button.setAccessibleName(
            self.tr("Copy Number") + ": " + CONTACT_NUMBER_DISPLAY
        )
        self.copy_button.setToolTip(self.tr("Copy Number") + ": " + CONTACT_NUMBER_DISPLAY)
        self.close_button.setText(self.tr("Close"))
        self.setWindowTitle(self.app_title)
