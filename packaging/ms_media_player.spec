# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for MS Media Player.

Builds a single self-contained Windows executable (``--onefile``,
``--noconsole``) that bundles:

* the whole Python interpreter and every third-party dependency,
* the PySide6 Qt libraries actually used by the application,
* all Qt ``.qm`` translations needed by the app AND by Qt itself,
* a full copy of the VLC engine (``libvlc.dll`` + ``libvlccore.dll`` +
  the complete ``plugins`` tree) so no system VLC/Python is required,
* the application icon and its translation resources.

Run from the project root with:

    pyinstaller packaging/ms_media_player.spec --noconfirm

The VLC installation directory can be overridden with the ``MSMP_VLC_DIR``
environment variable (defaults to ``C:\\Program Files\\VideoLAN\\VLC``).
"""
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

PROJECT_ROOT = Path(SPECPATH).resolve().parent
SRC = PROJECT_ROOT / "src"
RES = PROJECT_ROOT / "resources"
VLC_DIR = Path(os.environ.get("MSMP_VLC_DIR", r"C:\Program Files\VideoLAN\VLC"))

# ---------------------------------------------------------------------------
# Data files (translations, icons)
# ---------------------------------------------------------------------------
# Only the compiled .qm catalogues are needed at run time; the JSON/TS sources
# stay in the repository but are not shipped.
trans_datas = [
    (str(p), "resources/translations")
    for p in sorted((RES / "translations").glob("*.qm"))
]
datas = [
    (str(RES / "icons"), "resources/icons"),
]
datas += trans_datas

# Bundle Qt's own catalogues (standard buttons / dialogs) if available.
try:
    import PySide6  # noqa: F401
    qt_translations = Path(PySide6.__file__).parent / "translations"
    if qt_translations.is_dir():
        datas.append((str(qt_translations), "PySide6/translations"))
except Exception:
    pass

# ---------------------------------------------------------------------------
# Native libraries: bundled VLC engine
# ---------------------------------------------------------------------------
binaries = []
if (VLC_DIR / "libvlc.dll").exists():
    binaries.append((str(VLC_DIR / "libvlc.dll"), "resources/vlc"))
    binaries.append((str(VLC_DIR / "libvlccore.dll"), "resources/vlc"))
    plugins_root = VLC_DIR / "plugins"
    if plugins_root.is_dir():
        for root, _dirs, files in os.walk(plugins_root):
            for fname in files:
                if fname.lower().endswith(".dll"):
                    src_file = Path(root) / fname
                    rel_parent = src_file.relative_to(VLC_DIR).parent
                    binaries.append((str(src_file), str(Path("resources/vlc") / rel_parent)))
    print(f"[spec] Bundling VLC from {VLC_DIR} ({len(binaries)} native files)")
else:
    print(f"[spec] WARNING: libvlc.dll not found in {VLC_DIR}; "
          f"the build will rely on a system VLC install.")

# ---------------------------------------------------------------------------
# Hidden imports (modules imported lazily/in try-blocks that analysis misses)
# ---------------------------------------------------------------------------
hiddenimports = [
    "vlc",
    "pysrt",
    "pysubs2",
    "docx",
    "fpdf",
    "imageio_ffmpeg",
    "ui.dialogs.about_dialog",
    "ui.dialogs.settings_dialog",
    "ui.dialogs.shortcuts_dialog",
    "ui.dialogs.url_dialog",
    "ui.dialogs.bookmark_dialog",
    "ui.dialogs.equalizer_dialog",
    "ui.dialogs.playlist_manager_dialog",
    "ui.dialogs.subtitle_options_dialog",
]

# yt-dlp resolves its extractors dynamically -> collect everything.
try:
    hiddenimports += collect_submodules("yt_dlp")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Exclusions - drop unused heavyweight Qt modules to keep the exe lean
# ---------------------------------------------------------------------------
excludes = [
    "tkinter", "_tkinter",
    "numpy", "matplotlib", "scipy", "pandas", "IPython",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick", "PySide6.QtWebEngineQuickWidgets",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets",
    "PySide6.QtQuick3D", "PySide6.QtQuickControls2",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras", "PySide6.Qt3DInput", "PySide6.Qt3DLogic",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
    "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtUiTools",
    "PySide6.QtBluetooth", "PySide6.QtNfc", "PySide6.QtPositioning",
    "PySide6.QtSql", "PySide6.QtCharts",
    "PySide6.QtDataVisualization", "PySide6.QtSerialPort",
    "PySide6.QtWebChannel", "PySide6.QtWebSockets", "PySide6.QtSpatialAudio",
    "PySide6.QtTextToSpeech", "PySide6.QtRemoteObjects", "PySide6.QtScxml",
    "PySide6.QtStateMachine", "PySide6.QtSensors", "PySide6.QtSerialBus",
]

block_cipher = None

a = Analysis(
    [str(SRC / "main.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MSMediaPlayer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(RES / "icons" / "app_icon.ico"),
)
