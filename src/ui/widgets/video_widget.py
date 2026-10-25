"""
Video Widget - Video display widget with VLC integration
"""

import sys
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QPaintEvent, QResizeEvent
from media.media_engine import MediaEngine


class VideoWidget(QWidget):
    """Video display widget with VLC integration"""

    def __init__(self, media_engine: MediaEngine = None):
        super().__init__()
        self.media_engine = media_engine
        self.setMinimumSize(320, 180)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        # Don't force native window - let Qt handle it naturally
        # This prevents crashes on Windows when showing window with loaded media
        self.setAttribute(Qt.WA_DontCreateNativeAncestors, True)
        self.setStyleSheet("background-color: #000000;")

        # Overlay text
        self.overlay_text = ""
        self.show_overlay = False

        # Connect to media engine if provided
        if media_engine:
            self.set_media_engine(media_engine)

    def set_media_engine(self, engine: MediaEngine):
        """Set media engine and connect video output"""
        self.media_engine = engine
        if engine and hasattr(engine, 'player') and engine.player:
            # Set video output to this widget's native window handle
            self._attach_video_output()

    def _attach_video_output(self):
        """Attach VLC video output to this widget"""
        if not self.media_engine or not self.media_engine.player:
            return

        try:
            # Ensure widget has a valid native window handle
            self.winId()  # Force creation of native window
            
            if sys.platform == "win32":
                # Windows: use HWND
                self.media_engine.player.set_hwnd(int(self.winId()))
            elif sys.platform == "darwin":
                # macOS: use NSView
                self.media_engine.player.set_nsobject(int(self.winId()))
            else:
                # Linux: use XWindow
                self.media_engine.player.set_xwindow(int(self.winId()))
        except Exception as e:
            print(f"Failed to attach video output: {e}")

    def paintEvent(self, event: QPaintEvent):
        """Paint video frame or placeholder"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))

        if self.show_overlay and self.overlay_text:
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Arial", 14)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, self.overlay_text)

    def resizeEvent(self, event: QResizeEvent):
        """Handle resize"""
        super().resizeEvent(event)
        # Video output automatically resizes with the widget

    def set_overlay_text(self, text: str, show: bool = True):
        """Set overlay text"""
        self.overlay_text = text
        self.show_overlay = show
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(640, 360)

    def minimumSizeHint(self) -> QSize:
        return QSize(320, 180)

    def mouseDoubleClickEvent(self, event):
        """Handle double click for fullscreen"""
        if event.button() == Qt.LeftButton:
            window = self.window()
            if hasattr(window, 'toggle_fullscreen'):
                window.toggle_fullscreen()

    def mouseMoveEvent(self, event):
        """Handle mouse move"""
        # Show controls on hover
        window = self.window()
        if hasattr(window, 'control_panel'):
            window.control_panel.set_mouse_over(True)

    def leaveEvent(self, event):
        """Handle mouse leave"""
        window = self.window()
        if hasattr(window, 'control_panel'):
            window.control_panel.set_mouse_over(False)