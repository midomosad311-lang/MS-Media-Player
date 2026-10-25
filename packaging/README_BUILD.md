# MS Media Player — build, package and install

Everything needed to turn the Python sources into a single standalone Windows
executable and a multilingual installer.

## 1. Prerequisites

| Tool | Notes |
| --- | --- |
| Python 3.12 (64-bit) | `pip install -r requirements.txt` first |
| PyInstaller | `pip install pyinstaller` |
| Pillow | `pip install pillow` (only to regenerate the icon) |
| VLC 3.x | `C:\Program Files\VideoLAN\VLC` (its DLLs + plugins are bundled) |
| Inno Setup 6.3+ | needed only to build the installer (`ISCC.exe`) |

## 2. Build the standalone executable

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1
```

The script runs PyInstaller with `packaging/ms_media_player.spec`
(`--onefile`, `--noconsole`) and bundles:

* the Python runtime and every dependency (PySide6, python-vlc, yt-dlp,
  pysrt, pysubs2, python-docx, fpdf2, imageio-ffmpeg, …),
* `resources/translations` (all `.qm` catalogues) and `resources/icons`,
* Qt's own `.qm` catalogues (standard buttons/dialogs),
* **the complete VLC engine** (`libvlc.dll`, `libvlccore.dll` and the whole
  `plugins` tree) under `resources/vlc`, so no system VLC is required.

Useful parameters:

```powershell
packaging\build_exe.ps1 -DistPath D:\out\dist -WorkPath D:\out\build `
                        -VlcDir "C:\Program Files\VideoLAN\VLC"
```

Result: `<DistPath>\MSMediaPlayer.exe`.

## 2b. Regenerate the application icon (optional)

```
python tools/make_icon.py
```

Writes `resources/icons/app_icon.png` and `resources/icons/app_icon.ico`.

## 2c. Regenerate the embedded EULA (after editing EULA.txt)

```
python tools/make_eula_iss.py
```

Writes `packaging/eula_text.iss`, a generated Pascal procedure that loads the
agreement text into the installer's License page.  Embedding the text (instead
of reading `EULA.txt` from `{src}` at run time) guarantees the Arabic text is
always shown with the correct encoding and is always present, regardless of
where `Setup.exe` is launched from.

> Required only when `packaging/EULA.txt` changes.  `installer.iss` does
> `#include "eula_text.iss"`.

## 3. Build the installer

```
"D:\path\to\Inno Setup 6\ISCC.exe" /DExePath="<DistPath>\MSMediaPlayer.exe" packaging\installer.iss
```

`ExePath` defaults to `..\dist\MSMediaPlayer.exe`, so without `/DExePath` just
put the built exe in `dist\`. The installer is written to
`packaging\Output\MSMediaPlayer_Setup_<version>.exe`.

Installer features:

* **Language picker at start** — Arabic, English, Italian, Spanish, Portuguese
  (Brazil), Turkish (also `ShowLanguageDialog=auto`).
* **License Agreement page** with the full EULA — the memo scrolls with the
  arrow / Page Up / Page Down / Home / End keys, and the
  **“أوافق على الاتفاقية / I accept the agreement”** checkbox is checked
  automatically once the user navigates the text with the arrow keys.
  **Next** stays disabled until the agreement is accepted.
* Wizard order: `[language] → [license + accept] → [install folder] →
  [desktop shortcut] → install & finish`.

## 4. Automated post-build test

Both the sources and the built executable expose an end-to-end self-test that
writes a log and returns exit code 0 only when everything passes:

```
MSMediaPlayer.exe --selftest --selftest-log "%TEMP%\msmp_selftest.log"
echo Exit code: %ERRORLEVEL%
```

The self-test exercises: manager construction, main window, menu bar, VLC
initialisation, real audio playback (position/duration/pause/seek/volume/speed/
stop), the About dialog content (app name, developer credit, contact number),
live switching between all six languages, the keyboard shortcuts, and a 20 s
memory soak that fails if the working set grows by more than 120 MiB.

Run `packaging/test_installer.ps1` to install the already-built setup silently,
run the installed app's self-test and report the result:

```powershell
# install silently, run the installed self-test, then uninstall
powershell -ExecutionPolicy Bypass -File packaging\test_installer.ps1 `
    -Setup packaging\Output\MSMediaPlayer_Setup_1.0.0.exe

# same, but leave the application installed afterwards
powershell -ExecutionPolicy Bypass -File packaging\test_installer.ps1 `
    -Setup packaging\Output\MSMediaPlayer_Setup_1.0.0.exe -KeepInstalled
```

The script verifies the installed executable, `EULA.txt`, the desktop shortcut
and the uninstaller before running `--selftest` on the installed copy.

### Notes / gotchas

* The silent (`/SILENT`, `/VERYSILENT`) install still walks the wizard pages, so
  the License page accepts the agreement automatically when `WizardSilent` is
  true — otherwise the disabled **Next** button would block an unattended
  install.
* `PySide6.QtTest` **must not** be excluded from the PyInstaller build: the
  self-test uses `QTest.qWait` / `QTest.keyClick`.  Excluding it makes the
  frozen `--selftest` abort with no log.
* The self-test writes its log **line by line** while it runs, so even a hard
  native crash leaves the last completed step in the log file.
