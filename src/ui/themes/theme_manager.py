"""
Theme Manager - Handles application themes (Light, Dark, High Contrast)
"""

from typing import Dict
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


class ThemeManager:
    """Manages application themes"""

    LIGHT_THEME = {
        "window": "#FFFFFF",
        "window_text": "#000000",
        "base": "#FFFFFF",
        "alternate_base": "#F5F5F5",
        "tool_tip_base": "#FFFFDC",
        "tool_tip_text": "#000000",
        "text": "#000000",
        "button": "#E0E0E0",
        "button_text": "#000000",
        "bright_text": "#FFFFFF",
        "link": "#0066CC",
        "highlight": "#0078D7",
        "highlighted_text": "#FFFFFF",
        "disabled_text": "#808080",
        "disabled_button_text": "#808080",
        "border": "#CCCCCC",
        "focus": "#0078D7",
        "progress_bg": "#E0E0E0",
        "progress_fg": "#0078D7",
        "slider_groove": "#CCCCCC",
        "slider_handle": "#0078D7",
        "menu_bg": "#FFFFFF",
        "menu_text": "#000000",
        "menu_selected_bg": "#0078D7",
        "menu_selected_text": "#FFFFFF",
    }

    DARK_THEME = {
        "window": "#1E1E1E",
        "window_text": "#FFFFFF",
        "base": "#2D2D2D",
        "alternate_base": "#383838",
        "tool_tip_base": "#333333",
        "tool_tip_text": "#FFFFFF",
        "text": "#FFFFFF",
        "button": "#3C3C3C",
        "button_text": "#FFFFFF",
        "bright_text": "#FFFFFF",
        "link": "#4DA6FF",
        "highlight": "#0078D7",
        "highlighted_text": "#FFFFFF",
        "disabled_text": "#808080",
        "disabled_button_text": "#808080",
        "border": "#555555",
        "focus": "#0078D7",
        "progress_bg": "#3C3C3C",
        "progress_fg": "#0078D7",
        "slider_groove": "#555555",
        "slider_handle": "#0078D7",
        "menu_bg": "#2D2D2D",
        "menu_text": "#FFFFFF",
        "menu_selected_bg": "#0078D7",
        "menu_selected_text": "#FFFFFF",
    }

    HIGH_CONTRAST_LIGHT = {
        "window": "#FFFFFF",
        "window_text": "#000000",
        "base": "#FFFFFF",
        "alternate_base": "#FFFF00",
        "tool_tip_base": "#FFFF00",
        "tool_tip_text": "#000000",
        "text": "#000000",
        "button": "#000000",
        "button_text": "#FFFFFF",
        "bright_text": "#FFFFFF",
        "link": "#0000FF",
        "highlight": "#0000FF",
        "highlighted_text": "#FFFFFF",
        "disabled_text": "#808080",
        "disabled_button_text": "#808080",
        "border": "#000000",
        "focus": "#FF0000",
        "progress_bg": "#000000",
        "progress_fg": "#FFFF00",
        "slider_groove": "#000000",
        "slider_handle": "#FFFF00",
        "menu_bg": "#FFFFFF",
        "menu_text": "#000000",
        "menu_selected_bg": "#0000FF",
        "menu_selected_text": "#FFFFFF",
    }

    HIGH_CONTRAST_DARK = {
        "window": "#000000",
        "window_text": "#FFFFFF",
        "base": "#000000",
        "alternate_base": "#FFFF00",
        "tool_tip_base": "#FFFF00",
        "tool_tip_text": "#000000",
        "text": "#FFFFFF",
        "button": "#FFFFFF",
        "button_text": "#000000",
        "bright_text": "#FFFF00",
        "link": "#FFFF00",
        "highlight": "#FFFF00",
        "highlighted_text": "#000000",
        "disabled_text": "#808080",
        "disabled_button_text": "#808080",
        "border": "#FFFFFF",
        "focus": "#FFFF00",
        "progress_bg": "#FFFFFF",
        "progress_fg": "#FFFF00",
        "slider_groove": "#FFFFFF",
        "slider_handle": "#FFFF00",
        "menu_bg": "#000000",
        "menu_text": "#FFFFFF",
        "menu_selected_bg": "#FFFF00",
        "menu_selected_text": "#000000",
    }

    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.current_theme = "dark"
        self.high_contrast = False

    def apply_theme(self, theme: str, high_contrast: bool = False, app: QApplication = None):
        """Apply theme to application"""
        self.current_theme = theme
        self.high_contrast = high_contrast

        if high_contrast:
            if theme == "light":
                colors = self.HIGH_CONTRAST_LIGHT
            else:
                colors = self.HIGH_CONTRAST_DARK
        else:
            if theme == "light":
                colors = self.LIGHT_THEME
            else:
                colors = self.DARK_THEME

        if app:
            self._apply_palette(app, colors)
            self._apply_stylesheet(app, colors)

    def apply_high_contrast(self, enabled: bool):
        """Toggle high contrast mode"""
        theme = self.settings.get_theme()
        self.apply_theme(theme, enabled)

    def _apply_palette(self, app: QApplication, colors: Dict[str, str]):
        """Apply color palette"""
        palette = QPalette()

        palette.setColor(QPalette.Window, QColor(colors["window"]))
        palette.setColor(QPalette.WindowText, QColor(colors["window_text"]))
        palette.setColor(QPalette.Base, QColor(colors["base"]))
        palette.setColor(QPalette.AlternateBase, QColor(colors["alternate_base"]))
        palette.setColor(QPalette.ToolTipBase, QColor(colors["tool_tip_base"]))
        palette.setColor(QPalette.ToolTipText, QColor(colors["tool_tip_text"]))
        palette.setColor(QPalette.Text, QColor(colors["text"]))
        palette.setColor(QPalette.Button, QColor(colors["button"]))
        palette.setColor(QPalette.ButtonText, QColor(colors["button_text"]))
        palette.setColor(QPalette.BrightText, QColor(colors["bright_text"]))
        palette.setColor(QPalette.Link, QColor(colors["link"]))
        palette.setColor(QPalette.Highlight, QColor(colors["highlight"]))
        palette.setColor(QPalette.HighlightedText, QColor(colors["highlighted_text"]))

        # Disabled colors
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(colors["disabled_text"]))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors["disabled_button_text"]))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(colors["disabled_text"]))
        palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(colors["highlight"]))

        app.setPalette(palette)

    def _apply_stylesheet(self, app: QApplication, colors: Dict[str, str]):
        """Apply custom stylesheet"""
        stylesheet = f"""
        QWidget {{
            background-color: {colors['window']};
            color: {colors['window_text']};
            border: 1px solid {colors['border']};
        }}

        QMainWindow {{
            background-color: {colors['window']};
        }}

        QPushButton {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            border: 2px solid {colors['border']};
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            min-height: 32px;
            min-width: 80px;
        }}

        QPushButton:hover {{
            background-color: {colors['highlight']};
            color: {colors['highlighted_text']};
            border-color: {colors['focus']};
        }}

        QPushButton:pressed {{
            background-color: {colors['focus']};
        }}

        QPushButton:disabled {{
            background-color: {colors['button']};
            color: {colors['disabled_button_text']};
            border-color: {colors['disabled_text']};
        }}

        QPushButton:focus {{
            border: 3px solid {colors['focus']};
            outline: none;
        }}

        QSlider::groove:horizontal {{
            border: 1px solid {colors['slider_groove']};
            height: 8px;
            background: {colors['slider_groove']};
            border-radius: 4px;
        }}

        QSlider::handle:horizontal {{
            background: {colors['slider_handle']};
            border: 2px solid {colors['focus']};
            width: 18px;
            height: 18px;
            margin: -5px 0;
            border-radius: 9px;
        }}

        QSlider::handle:horizontal:hover {{
            background: {colors['focus']};
        }}

        QSlider::handle:horizontal:focus {{
            border: 3px solid {colors['focus']};
        }}

        QSlider::sub-page:horizontal {{
            background: {colors['progress_fg']};
            border-radius: 4px;
        }}

        QProgressBar {{
            border: 2px solid {colors['border']};
            border-radius: 4px;
            background-color: {colors['progress_bg']};
            text-align: center;
            color: {colors['text']};
            font-weight: bold;
            height: 20px;
        }}

        QProgressBar::chunk {{
            background-color: {colors['progress_fg']};
            border-radius: 2px;
        }}

        QMenuBar {{
            background-color: {colors['menu_bg']};
            color: {colors['menu_text']};
            border-bottom: 1px solid {colors['border']};
        }}

        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
        }}

        QMenuBar::item:selected {{
            background-color: {colors['menu_selected_bg']};
            color: {colors['menu_selected_text']};
        }}

        QMenu {{
            background-color: {colors['menu_bg']};
            color: {colors['menu_text']};
            border: 1px solid {colors['border']};
        }}

        QMenu::item {{
            padding: 8px 24px;
        }}

        QMenu::item:selected {{
            background-color: {colors['menu_selected_bg']};
            color: {colors['menu_selected_text']};
        }}

        QMenu::separator {{
            height: 1px;
            background: {colors['border']};
            margin: 4px 8px;
        }}

        QComboBox {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            border: 2px solid {colors['border']};
            border-radius: 4px;
            padding: 6px 12px;
            min-height: 28px;
        }}

        QComboBox:hover {{
            border-color: {colors['focus']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {colors['menu_bg']};
            color: {colors['menu_text']};
            selection-background-color: {colors['menu_selected_bg']};
            selection-color: {colors['menu_selected_text']};
            border: 1px solid {colors['border']};
        }}

        QSpinBox, QDoubleSpinBox {{
            background-color: {colors['base']};
            color: {colors['text']};
            border: 2px solid {colors['border']};
            border-radius: 4px;
            padding: 4px 8px;
            min-height: 28px;
        }}

        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {colors['focus']};
        }}

        QGroupBox {{
            border: 2px solid {colors['border']};
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: bold;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: {colors['window_text']};
        }}

        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors['window']};
        }}

        QTabBar::tab {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            border: 1px solid {colors['border']};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}

        QTabBar::tab:selected {{
            background-color: {colors['window']};
            border-bottom-color: {colors['window']};
        }}

        QTabBar::tab:hover {{
            background-color: {colors['highlight']};
            color: {colors['highlighted_text']};
        }}

        QListWidget, QTreeWidget, QTableWidget {{
            background-color: {colors['base']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            alternate-background-color: {colors['alternate_base']};
            selection-background-color: {colors['highlight']};
            selection-color: {colors['highlighted_text']};
        }}

        QListWidget::item:focus, QTreeWidget::item:focus, QTableWidget::item:focus {{
            border: 2px solid {colors['focus']};
        }}

        QScrollBar:vertical {{
            background: {colors['window']};
            width: 12px;
            border: none;
        }}

        QScrollBar::handle:vertical {{
            background: {colors['slider_groove']};
            border-radius: 6px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {colors['focus']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        QScrollBar:horizontal {{
            background: {colors['window']};
            height: 12px;
            border: none;
        }}

        QScrollBar::handle:horizontal {{
            background: {colors['slider_groove']};
            border-radius: 6px;
            min-width: 20px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {colors['focus']};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}

        QToolTip {{
            background-color: {colors['tool_tip_base']};
            color: {colors['tool_tip_text']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 4px 8px;
        }}

        QStatusBar {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            border-top: 1px solid {colors['border']};
        }}

        QDockWidget {{
            titlebar-close-icon: url(close.png);
            titlebar-normal-icon: url(undock.png);
        }}

        QDockWidget::title {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            padding: 6px;
        }}

        QCheckBox, QRadioButton {{
            spacing: 8px;
            color: {colors['text']};
        }}

        QCheckBox::indicator, QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {colors['border']};
            border-radius: 4px;
        }}

        QCheckBox::indicator:checked {{
            background-color: {colors['highlight']};
            border-color: {colors['focus']};
            image: url(check.png);
        }}

        QRadioButton::indicator {{
            border-radius: 9px;
        }}

        QRadioButton::indicator:checked {{
            background-color: {colors['highlight']};
            border-color: {colors['focus']};
        }}

        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors['base']};
            color: {colors['text']};
            border: 2px solid {colors['border']};
            border-radius: 4px;
            padding: 6px;
            selection-background-color: {colors['highlight']};
            selection-color: {colors['highlighted_text']};
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {colors['focus']};
        }}

        QLabel {{
            color: {colors['text']};
        }}

        QHeaderView::section {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            border: 1px solid {colors['border']};
            padding: 6px;
            font-weight: bold;
        }}
        """

        app.setStyleSheet(stylesheet)

    def get_stylesheet(self, theme: str = None, high_contrast: bool = None) -> str:
        """Get stylesheet for theme"""
        theme = theme or self.current_theme
        high_contrast = high_contrast if high_contrast is not None else self.high_contrast

        if high_contrast:
            colors = self.HIGH_CONTRAST_LIGHT if theme == "light" else self.HIGH_CONTRAST_DARK
        else:
            colors = self.LIGHT_THEME if theme == "light" else self.DARK_THEME

        # Return minimal stylesheet for external use
        return f"""
        QWidget {{
            background-color: {colors['window']};
            color: {colors['window_text']};
        }}
        QPushButton {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            border: 2px solid {colors['border']};
            border-radius: 4px;
            padding: 8px 16px;
        }}
        QPushButton:hover {{
            background-color: {colors['highlight']};
            color: {colors['highlighted_text']};
        }}
        QSlider::groove:horizontal {{
            background: {colors['slider_groove']};
            height: 8px;
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background: {colors['slider_handle']};
            width: 18px;
            height: 18px;
            border-radius: 9px;
        }}
        QProgressBar {{
            background-color: {colors['progress_bg']};
            border: 2px solid {colors['border']};
            border-radius: 4px;
        }}
        QProgressBar::chunk {{
            background-color: {colors['progress_fg']};
        }}
        """