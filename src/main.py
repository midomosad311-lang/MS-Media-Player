"""
MS Media Player - Professional Media Player
Modern media player with full accessibility support
"""

import sys
import ctypes
import traceback
from pathlib import Path

# Add src to path - handle both direct execution and module execution
SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

# Initialize COM for VLC on Windows (prevents RPC_E_DISCONNECTED crashes on exit).
# IMPORTANT: the GUI thread MUST be an STA (COINIT_APARTMENTTHREADED == 0x2).
# If it is initialized as MTA (0x0), the native Windows "Common Item Dialog"
# used by File -> Open cannot be displayed, so the file picker never appears.
if sys.platform == "win32":
    try:
        ole32 = ctypes.windll.ole32
        COINIT_APARTMENTTHREADED = 0x2
        hr = ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
        # 0x0 (S_OK) = initialized now; 0x1 (S_FALSE) = already initialized on this thread.
        # RPC_E_CHANGED_MODE (0x80010106) means the thread was already MTA; nothing we can do,
        # but in our flow this call is the first one, so it succeeds as STA.
    except Exception:
        pass

# When running from a PyInstaller bundle, point python-vlc at the packaged
# libVLC *before* python-vlc is imported (it loads the native library on import).
try:
    from core.paths import configure_bundled_vlc
    if configure_bundled_vlc():
        print("Using bundled libVLC")
except Exception:
    pass


def show_error_dialog(title, message):
    """Show error dialog using Qt if available, otherwise print to console."""
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        # Create a minimal QApplication for the error dialog if not already created.
        if QApplication.instance() is None:
            QApplication(sys.argv)
        QMessageBox.critical(None, title, message)
    except Exception:
        print(f"ERROR: {title}")
        print(message)

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtGui import QIcon

    from core.app_meta import APP_NAME
    from core.application import MediaPlayerApplication
    from core.config import ConfigManager
    from settings.settings_manager import SettingsManager
    from i18n.translation_manager import TranslationManager
    from accessibility.accessibility_manager import AccessibilityManager

except ImportError as e:
    error_msg = f"Failed to import required modules:\n{e}\n\n"
    error_msg += "Please ensure:\n"
    error_msg += "1. All dependencies are installed: pip install -r requirements.txt\n"
    error_msg += "2. VLC Media Player is installed: https://www.videolan.org/vlc/\n"
    error_msg += "3. You're running from the correct directory"
    show_error_dialog("Import Error", error_msg)
    sys.exit(1)

# Single instance server name
SINGLE_INSTANCE_SERVER = "MSMediaPlayer_SingleInstance"

def send_to_existing_instance(args):
    """Send command-line arguments to existing instance via local socket."""
    socket = QLocalSocket()
    socket.connectToServer(SINGLE_INSTANCE_SERVER)
    if socket.waitForConnected(1000):
        data = "\0".join(args).encode('utf-8')
        socket.write(data)
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return True
    return False

def setup_single_instance_server(app, player_app):
    """Set up local server to receive files from other instances."""
    server = QLocalServer()
    # Remove any stale server
    QLocalServer.removeServer(SINGLE_INSTANCE_SERVER)
    
    if not server.listen(SINGLE_INSTANCE_SERVER):
        print(f"Warning: Could not start single instance server: {server.errorString()}")
        return None
    
    def on_new_connection():
        socket = server.nextPendingConnection()
        if socket:
            if socket.waitForReadyRead(1000):
                data = socket.readAll().data().decode('utf-8')
                args = data.split("\0")
                # Filter empty args
                args = [a for a in args if a]
                if args:
                    print(f"Received files from another instance: {args}")
                    player_app.handle_command_line_args(args)
                    # Load the file(s) in the current window or create a new one.
                    # open_media_files() also auto-adds every compatible media
                    # file from the same folder(s) to the playlist.
                    if hasattr(player_app, '_command_line_files') and player_app._command_line_files:
                        if player_app.windows:
                            player_app.windows[0].open_media_files(player_app._command_line_files)
                        else:
                            window = player_app.create_window()
                            window.open_media_files(player_app._command_line_files)
            socket.disconnectFromServer()
    
    server.newConnection.connect(on_new_connection)
    return server


def main():
    """Main application entry point"""
    print("Starting MS Media Player...")
    # Enable high DPI scaling (Qt6 handles this automatically)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    # The display name is what Windows / the task manager / screen readers show
    # next to the window; keep it identical to the brand in every language.
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("M S Media")
    app.setOrganizationDomain("msmedia.app")
    print("QApplication created")

    # Set application icon. Resources live next to the "src" package
    # (i.e. <app>/resources/icons), both when run from source and when
    # bundled by PyInstaller (where _MEIPASS/resources is used).
    base_dir = Path(getattr(sys, "_MEIPASS", SCRIPT_DIR.parent))
    icon_candidates = [
        base_dir / "resources" / "icons" / "app_icon.ico",
        base_dir / "resources" / "icons" / "app_icon.png",
        SCRIPT_DIR / "resources" / "icons" / "app_icon.png",
    ]
    for icon_path in icon_candidates:
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            print(f"Icon loaded: {icon_path}")
            break
    else:
        print(f"Icon not found (looked in: {icon_candidates})")

    # Automated self-test mode (used to validate a freshly built executable).
    if "--selftest" in sys.argv:
        log_path = None
        if "--selftest-log" in sys.argv:
            index = sys.argv.index("--selftest-log")
            if index + 1 < len(sys.argv):
                log_path = sys.argv[index + 1]
        from core.selftest import run_selftest

        try:
            return run_selftest(app, log_path)
        except Exception:
            details = traceback.format_exc()
            if log_path:
                try:
                    with open(log_path, "a", encoding="utf-8") as handle:
                        handle.write("FATAL (main):\n" + details + "\n")
                except Exception:
                    pass
            print(details)
            return 1

    # Check for existing instance BEFORE initializing managers
    # (but only if there are command-line args to pass)
    if len(sys.argv) > 1:
        if send_to_existing_instance(sys.argv[1:]):
            print("Sent file to existing instance, exiting.")
            return 0

    try:
        # Initialize core managers
        config_manager = ConfigManager()
        settings_manager = SettingsManager(config_manager)
        translation_manager = TranslationManager(settings_manager)
        accessibility_manager = AccessibilityManager(settings_manager)
        print("Managers initialized")

        # Apply initial theme
        settings_manager.apply_theme(app)
        print("Theme applied")

        # Create main application controller
        player_app = MediaPlayerApplication(
            app=app,
            config_manager=config_manager,
            settings_manager=settings_manager,
            translation_manager=translation_manager,
            accessibility_manager=accessibility_manager,
        )
        print("MediaPlayerApplication created")

        # Register global shortcuts
        player_app.register_shortcuts()
        print("Shortcuts registered")

        # Set up single instance server
        server = setup_single_instance_server(app, player_app)
        if server:
            print("Single instance server started")

        # Handle command-line arguments (file associations / double-click)
        player_app.handle_command_line_args(sys.argv[1:])
        print("Command line arguments processed")

        # Start application
        print("Running application...")
        result = player_app.run()
        
    except Exception as e:
        error_msg = f"Application failed to start:\n{e}\n\n"
        error_msg += "Full traceback:\n"
        error_msg += traceback.format_exc()
        show_error_dialog("Startup Error", error_msg)
        return 1
    
    # Uninitialize COM on Windows
    if sys.platform == "win32":
        try:
            ole32 = ctypes.windll.ole32
            ole32.CoUninitialize()
        except Exception:
            pass
    
    return result


if __name__ == "__main__":
    sys.exit(main())