"""Filesystem helpers that work both from source and when frozen by PyInstaller.

When the application is bundled, ``__file__`` no longer points at the project
tree, so resource locations must be resolved from ``sys._MEIPASS`` (onefile and
onedir) instead of being derived from the module path.
"""
import os
import sys
from pathlib import Path


def app_root() -> Path:
    """Return the directory that contains the ``resources`` folder.

    * Frozen: the PyInstaller extraction / install directory.
    * Source: the project root (the parent of the ``src`` package).
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # src/core/paths.py -> parents[2] == project root
    return Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    """Return an absolute path inside the application's ``resources`` folder."""
    return app_root().joinpath("resources", *parts)


def configure_bundled_vlc() -> bool:
    """Point python-vlc at a bundled libVLC, if one was packaged.

    Must be called *before* ``import vlc`` because python-vlc resolves the
    native library at import time.  Returns True when a bundled libVLC was
    found (the caller can then rely on it instead of a system install).
    """
    vlc_dir = resource_path("vlc")
    libvlc = vlc_dir / "libvlc.dll"
    plugins = vlc_dir / "plugins"
    if not libvlc.exists():
        return False

    os.environ.setdefault("PYTHON_VLC_LIB_PATH", str(libvlc))
    if plugins.is_dir():
        os.environ.setdefault("PYTHON_VLC_MODULE_PATH", str(plugins))
        os.environ.setdefault("VLC_PLUGIN_PATH", str(plugins))

    # Make libvlc's own dependencies resolve from the bundled folder.
    os.environ["PATH"] = str(vlc_dir) + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(str(vlc_dir))
        except Exception:
            pass
    return True
