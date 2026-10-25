#!/usr/bin/env python3
"""
MS Media Player - Launcher Script
This script ensures the application runs correctly regardless of the working directory.
It handles path setup, dependency checks, and proper initialization.
"""

import sys
import os
import subprocess
from pathlib import Path


def check_vlc_installed():
    """Check if VLC is installed and accessible."""
    # Common VLC installation paths on Windows
    vlc_paths = [
        r"C:\Program Files\VideoLAN\VLC",
        r"C:\Program Files (x86)\VideoLAN\VLC",
    ]
    
    for path in vlc_paths:
        if os.path.exists(os.path.join(path, "vlc.exe")):
            # Add VLC directory to PATH for python-vlc to find libvlc
            os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
            return True
    
    # Check if vlc is in PATH
    try:
        subprocess.run(["vlc", "--version"], capture_output=True, check=False)
        return True
    except FileNotFoundError:
        pass
    
    return False


def check_dependencies():
    """Check if required Python packages are installed."""
    required_packages = [
        "PySide6",
        "vlc",
        "platformdirs",
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing


def setup_environment():
    """Setup the environment for the application."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Change to the script directory to ensure relative paths work
    os.chdir(script_dir)
    
    # Add src to Python path
    src_path = script_dir / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
    
    # Add script directory to Python path as fallback
    sys.path.insert(0, str(script_dir))
    
    # Set up VLC path on Windows
    if sys.platform == "win32":
        if not check_vlc_installed():
            print("WARNING: VLC Media Player not found!")
            print("Please install VLC from https://www.videolan.org/vlc/")
            print("The application may not work without VLC.")
            print()


def main():
    """Main entry point."""
    print("=" * 60)
    print("MS Media Player - Launcher")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print("ERROR: Missing required packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nPlease install them with:")
        print("  pip install -r requirements.txt")
        print("\nAlso make sure VLC Media Player is installed:")
        print("  https://www.videolan.org/vlc/")
        input("\nPress Enter to exit...")
        return 1
    
    # Import and run the application
    try:
        from src.main import main as app_main
        print("Starting MS Media Player...")
        print("-" * 60)
        return app_main()
    except ImportError as e:
        print(f"ERROR: Failed to import application: {e}")
        print("Make sure you're running from the correct directory.")
        input("\nPress Enter to exit...")
        return 1
    except Exception as e:
        print(f"ERROR: Application failed to start: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        return 1


if __name__ == "__main__":
    sys.exit(main())