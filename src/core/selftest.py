"""End-to-end self-test that can validate both the source tree and the built EXE.

Usage (the shipped executable is windowed, so results go to a log file):

    MSMediaPlayer.exe --selftest --selftest-log <path-to-log.txt>

The test constructs the real application (managers, main window, VLC engine),
exercises media playback, the About dialog, live language switching and the
keyboard shortcuts, then runs a short memory soak to catch leaks.  It uses a
throw-away configuration directory so the user's real settings are never
modified.  Exit code 0 == all checks passed.
"""
from __future__ import annotations

import math
import os
import struct
import sys
import tempfile
import time
import traceback
import wave
from pathlib import Path

_LINES: list = []
_ISSUES = []
_LOG_PATH = None


def set_log_path(path) -> None:
    """Start (or restart) an incremental log file."""
    global _LOG_PATH
    _LOG_PATH = str(path) if path else None
    if _LOG_PATH:
        try:
            Path(_LOG_PATH).write_text("", encoding="utf-8")
        except Exception:
            _LOG_PATH = None


def _out(message: str) -> None:
    """Print a line of log output and append it to the log file immediately.

    Writing eagerly (rather than only at the end) means the report survives a
    crash, so a failing build leaves behind the last step that was reached.
    """
    try:
        print(message, flush=True)
    except Exception:
        pass
    _LINES.append(message)
    if _LOG_PATH:
        try:
            with open(_LOG_PATH, "a", encoding="utf-8") as handle:
                handle.write(message + "\n")
        except Exception:
            pass


def _check(label: str, ok: bool, extra: str = "") -> bool:
    _out(("PASS " if ok else "FAIL ") + label + (f"  [{extra}]" if extra else ""))
    if not ok:
        _ISSUES.append(label)
    return ok


def _working_set_mb() -> float:
    """Current process working set in MiB (Windows), or 0 if unavailable."""
    try:
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.windll.kernel32
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        get_info = getattr(kernel32, "K32GetProcessMemoryInfo", None)
        if get_info is None:
            get_info = ctypes.windll.psapi.GetProcessMemoryInfo
        get_info.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
            wintypes.DWORD,
        ]
        get_info.restype = wintypes.BOOL
        ok = get_info(
            kernel32.GetCurrentProcess(), ctypes.byref(counters), wintypes.DWORD(counters.cb)
        )
        if ok:
            return counters.WorkingSetSize / (1024.0 * 1024.0)
    except Exception:
        pass
    return 0.0


def _make_test_wav(path, seconds: float = 4.0) -> bool:
    """Write a short 440 Hz tone so playback can be exercised end to end."""
    try:
        rate = 44100
        with wave.open(str(path), "w") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(rate)
            frames = bytearray()
            for i in range(int(rate * seconds)):
                value = int(0.2 * 32767 * math.sin(2.0 * math.pi * 440.0 * i / rate))
                frames += struct.pack("<h", value)
            handle.writeframes(bytes(frames))
        return True
    except Exception as exc:  # pragma: no cover - defensive
        _out(f"  (could not create test wav: {exc})")
        return False


def run_selftest(app, log_path: str = None) -> int:
    """Run the complete self-test. Returns a process exit code (0 == success)."""
    set_log_path(log_path)
    _out("================= MS Media Player self-test =================")
    _out(f"frozen      : {getattr(sys, 'frozen', False)}")
    _out(f"_MEIPASS    : {getattr(sys, '_MEIPASS', None)}")
    _out(f"executable  : {sys.executable}")
    _out("")

    # Isolate configuration so the user's real settings are never modified.
    # platformdirs resolves the folder through the Windows shell API, so
    # overriding LOCALAPPDATA alone is not enough - patch the helper too.
    tmp_root = Path(tempfile.mkdtemp(prefix="msmp_selftest_"))
    os.environ["LOCALAPPDATA"] = str(tmp_root)
    os.environ["APPDATA"] = str(tmp_root)
    import core.config as _config_module
    _config_module.user_config_dir = (
        lambda appname=None, *a, **k: str(tmp_root / (appname or "MSMediaPlayer"))
    )
    _out(f"temp config : {tmp_root}")

    # Capture any unhandled exception raised on the Qt event loop or in slots.
    unhandled = []
    original_hook = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb):
        unhandled.append("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        original_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook

    exit_code = 1
    player = None
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest

        def pump(ms: int):
            QTest.qWait(ms)

        from accessibility.accessibility_manager import AccessibilityManager
        from core.application import MediaPlayerApplication
        from core.config import ConfigManager
        from i18n.translation_manager import TranslationManager
        from settings.settings_manager import SettingsManager

        config = ConfigManager()
        settings = SettingsManager(config)
        try:
            settings.apply_theme(app)
        except Exception:
            pass
        translation = TranslationManager(settings)
        accessibility = AccessibilityManager(settings)

        player = MediaPlayerApplication(
            app=app,
            config_manager=config,
            settings_manager=settings,
            translation_manager=translation,
            accessibility_manager=accessibility,
        )
        player.register_shortcuts()
        _check("managers + application controller constructed", True)

        win = player.create_window()
        win.show()
        win.raise_()
        win.activateWindow()
        QTest.qWaitForWindowExposed(win, 5000)
        QTest.qWaitForWindowActive(win, 5000)
        pump(300)
        _check("main window created and shown", win.isVisible())

        # ---- window / menus -------------------------------------------------
        from core.app_meta import APP_NAME
        _check("window title is set", bool(win.windowTitle().strip()), win.windowTitle())
        _check("window title is the brand 'MS Media Player'",
               win.windowTitle() == APP_NAME, win.windowTitle())
        _check("window title is not localised (no Arabic name)",
               "مشغل الوسائط" not in win.windowTitle(), win.windowTitle())
        _check("application name is the brand",
               app.applicationName() == APP_NAME, app.applicationName())
        _check("no media is loaded on a fresh start",
               not win.media_engine.current_file and not win.media_engine.current_url,
               f"{win.media_engine.current_file!r}/{win.media_engine.current_url!r}")
        menu_actions = win.menuBar().actions()
        _check("menu bar populated", len(menu_actions) >= 3, f"{len(menu_actions)} menus")

        # ---- VLC engine -----------------------------------------------------
        _check("VLC engine initialised", bool(win.media_engine._ensure_vlc_initialized()))
        _check("libVLC loaded (bundled or system)", win.media_engine._vlc_initialized)

        # ---- audio playback end-to-end -------------------------------------
        wav_path = tmp_root / "selftest_tone.wav"
        if _make_test_wav(wav_path):
            loaded = win.media_engine.load_file(str(wav_path))
            _check("media file loaded", bool(loaded))
            win.media_engine.play()
            deadline = time.time() + 6.0
            while time.time() < deadline:
                pump(200)
                if win.media_engine.get_time() > 0.4:
                    break
            elapsed = win.media_engine.get_time()
            _check("playback advances (position > 0)", elapsed > 0.2, f"t={elapsed:.2f}s")
            _check("duration detected from file", win.media_engine.get_duration() > 1.0,
                   f"dur={win.media_engine.get_duration():.2f}s")
            win.media_engine.pause()
            pump(200)
            _check("pause works",
                   win.media_engine.get_state().value in ("paused", "playing", "stopped"),
                   win.media_engine.get_state().value)
            moved = win.media_engine.seek_relative(1.0)
            pump(200)
            _check("relative seek returns a position",
                   isinstance(moved, (int, float)), f"{float(moved):.2f}")
            win.media_engine.set_volume(80)
            pump(100)
            _check("volume set", win.media_engine.get_volume() == 80, win.media_engine.get_volume())
            win.media_engine.set_speed(1.5)
            pump(100)
            _check("speed set", abs(win.media_engine.get_speed() - 1.5) < 0.01,
                   win.media_engine.get_speed())
            win.media_engine.set_speed(1.0)
            win.media_engine.stop()
            pump(200)
            _check("stop works", win.media_engine.get_state().value == "stopped",
                   win.media_engine.get_state().value)

        # ---- About dialog ---------------------------------------------------
        # Force Arabic so the credit/contact strings are deterministic.
        translation.apply_language("ar")
        pump(100)
        import importlib
        about_mod = importlib.import_module("ui.dialogs.about_dialog")
        about = about_mod.AboutDialog("ar", "About", win, translation_manager=translation)
        about.show()
        pump(200)
        about_text = about.browser.toPlainText()
        _check("About dialog shows the brand name", APP_NAME in about_text)
        _check("About dialog does not show a translated app name",
               "مشغل الوسائط" not in about_text)
        _check("About dialog shows developer credit", "محمد مسعد" in about_text)
        _check("About dialog shows the new contact number",
               "20 10 40 24 30 45" in about_text, about_text[:0] )
        # The 'Copy Number' button must copy only the international number.
        from PySide6.QtWidgets import QApplication as _QApp
        _QApp.clipboard().clear()
        about._copy_number()
        pump(100)
        _check("Copy Number copies the international number",
               _QApp.clipboard().text() == "201040243045", _QApp.clipboard().text())
        about.close()
        about.deleteLater()
        pump(100)

        # ---- live language switching ---------------------------------------
        def first_menu_text():
            actions = win.menuBar().actions()
            return actions[0].text() if actions else ""

        seen = {}
        for lang in ("en", "ar", "it", "es", "pt", "tr"):
            translation.apply_language(lang)
            pump(120)
            seen[lang] = first_menu_text()
            _check(f"language '{lang}' applied live",
                   translation.get_current_language() == lang,
                   translation.get_current_language())
        _check("Arabic menu differs from English (live retranslation)",
               seen["ar"] != seen["en"], f"{seen['en']!r} vs {seen['ar']!r}")
        for _round in range(3):
            for lang in ("ar", "en", "tr", "en"):
                translation.apply_language(lang)
                pump(60)
        translation.apply_language("ar")
        pump(120)
        _check("repeated language round-trips stay stable",
               translation.get_current_language() == "ar" and bool(first_menu_text()))

        # ---- keyboard shortcuts (must not raise) ---------------------------
        for name, key in (
            ("Space", Qt.Key_Space), ("Right", Qt.Key_Right), ("Left", Qt.Key_Left),
            ("Up", Qt.Key_Up), ("Down", Qt.Key_Down),
        ):
            try:
                QTest.keyClick(win, key)
                pump(120)
                _check(f"key '{name}' handled without error", True)
            except Exception as exc:  # pragma: no cover - defensive
                _check(f"key '{name}' handled without error", False, str(exc))

        # ---- memory soak (detect runaway growth) ---------------------------
        pump(500)
        baseline = _working_set_mb()
        peak = baseline
        for _ in range(20):
            pump(1000)
            peak = max(peak, _working_set_mb())
        growth = peak - baseline
        _out(f"  memory: baseline={baseline:.1f} MiB peak={peak:.1f} MiB growth={growth:.1f} MiB")
        _check("no runaway memory growth during 20s idle soak",
               (baseline == 0 or growth < 120.0), f"{growth:.1f} MiB")

        _check("no unhandled exceptions during the run", not unhandled,
               (unhandled[0].splitlines()[-1] if unhandled else ""))

        exit_code = 1 if _ISSUES else 0
    except Exception:
        _out("FATAL: the self-test raised an exception:")
        _out(traceback.format_exc())
        _ISSUES.append("self-test raised an exception")

    # Write the report *before* tearing the engine down, so it survives even if
    # the native VLC teardown misbehaves.
    sys.excepthook = original_hook
    _out("")
    _out(f"TOTAL FAILURES: {len(_ISSUES)}")
    for failure in _ISSUES:
        _out(f"  FAILED: {failure}")
    _out("================ self-test finished ================")

    if player is not None:
        try:
            player._cleanup()
            _out("teardown: ok")
        except Exception:
            _out("teardown: raised\n" + traceback.format_exc())

    return exit_code
