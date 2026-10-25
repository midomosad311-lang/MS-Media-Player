# MS Media Player

**مشغّل وسائط احترافي لنظام Windows — متاح بالكامل لذوي الاحتياجات الخاصة.**

[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11%20x64-0078D6?logo=windows&logoColor=white)](https://github.com/midomosad311-lang/MS-Media-Player/releases/latest)
[![Latest release](https://img.shields.io/github/v/release/midomosad311-lang/MS-Media-Player?label=latest)](https://github.com/midomosad311-lang/MS-Media-Player/releases/latest)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)

> مشغّل وسائط مجاني ومستقل لنظام Windows، مبني بـ **Python + PySide6 + محرّك VLC**، مع دعم كامل لقارئات الشاشة (NVDA / JAWS / Narrator)، وتنقّل كامل بلوحة المفاتيح، وواجهة بستّ لغات منها **العربية** باتجاه RTL. لا يحتاج Python ولا تثبيت VLC — المحرّك محزوم داخل البرنامج.

---

## التحميل

| النسخة | الملف | الحجم |
|---|---|---|
| **المثبّت (موصى به)** | [`MSMediaPlayer_Setup_1.0.0.exe`](https://github.com/midomosad311-lang/MS-Media-Player/releases/latest/download/MSMediaPlayer_Setup_1.0.0.exe) | ‎≈ 156 م.ب |
| **النسخة المحمولة** | [`MSMediaPlayer.exe`](https://github.com/midomosad311-lang/MS-Media-Player/releases/latest/download/MSMediaPlayer.exe) | ‎≈ 157 م.ب |

- **النظام المطلوب:** Windows 10 أو 11 (64-bit).
- **لا يحتاج:** Python، ولا VLC، ولا أي مكتبات خارجية.
- المثبّت يدعم ستّ لغات، ويعرض اتفاقية الترخيص، وينشئ اختصارًا على سطح المكتب، ويتضمّن مُلغِي تثبيت كاملًا.

### التحقق من سلامة الملفات (SHA-256)

```
MSMediaPlayer.exe
13FE8379F8DD777B104FA924B7CC4F2DB5963FAC7E60D308622D0D9EE026C30F

MSMediaPlayer_Setup_1.0.0.exe
AEB789C385153EF4D0A389D1DEDAB38557718D3D9C78D1CB69096D529B34094E
```

---

## المزايا

- **ستّ لغات:** العربية، الإنجليزية، الإيطالية، الإسبانية، البرتغالية (البرازيل)، التركية — مع تبديل فوري دون إعادة تشغيل، واتجاه RTL تلقائي للعربية.
- **إتاحة كاملة:** توافق مع NVDA وJAWS وNarrator، وإعلان أسماء الأزرار واختصاراتها، وتنقّل كامل بلوحة المفاتيح، وثيمات عالية التباين.
- **تشغيل متقدّم:** سرعة من 0.25× إلى 4×، تقديم/تأخير قابل للضبط، تكرار A-B، علامات مرجعية (Bookmarks)، واستئناف التشغيل من حيث توقفت.
- **قوائم تشغيل:** دعم M3U، خلط عشوائي، تكرار، وإدارة قوائم متعددة.
- **صوت وفيديو:** مُعادل صوتي، مزامنة الصوت، ترجمات (SRT/ASS…)، تسريع عتاد، وتعديل حجم/لون الترجمة.
- **بثّ شبكي:** HTTP وRTSP وRTMP وHLS وDASH، مع دعم روابط يوتيوب عبر yt-dlp.
- **واجهة حديثة:** ثيمات فاتحة وداكنة وعالية التباين، وأزرار كبيرة مناسبة لضعاف البصر.
- **مستقل تمامًا:** محرّك VLC كامل (DLLs + plugins) داخل الملف التنفيذي.

---

## التثبيت والتشغيل

### الطريقة 1: المثبّت (الأسهل)

1. نزّل `MSMediaPlayer_Setup_1.0.0.exe` من [صفحة الإصدارات](https://github.com/midomosad311-lang/MS-Media-Player/releases/latest).
2. شغّله واختر اللغة، ثم وافق على اتفاقية الترخيص.
3. اختر مجلد التثبيت، ثم اضغط **تثبيت**.
4. شغّل **MS Media Player** من سطح المكتب أو قائمة ابدأ.

### الطريقة 2: النسخة المحمولة

نزّل `MSMediaPlayer.exe` وشغّله مباشرة — لا تثبيت ولا صلاحيات مدير.

### الطريقة 3: من المصدر

يتطلّب Python 3.9+ وVLC 3.x مثبّتًا على الجهاز:

```bash
git clone https://github.com/midomosad311-lang/MS-Media-Player.git
cd MS-Media-Player
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

أو ببساطة انقر `launch.bat` بعد تثبيت المتطلّبات.

---

## بناء الملف التنفيذي والمثبّت

يتطلّب: Python 3.12 (64-bit)، PyInstaller، VLC 3.x، وInno Setup 6.3+ (للمثبّت فقط).

```powershell
# 1) بناء MSMediaPlayer.exe في مجلد dist
powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1

# 2) بناء المثبّت
ISCC.exe /DExePath="dist\MSMediaPlayer.exe" packaging\installer.iss

# 3) اختبار ذاتي كامل للملف التنفيذي
dist\MSMediaPlayer.exe --selftest --selftest-log "%TEMP%\msmp_selftest.log"
```

التفاصيل الكاملة في [`packaging/README_BUILD.md`](packaging/README_BUILD.md).

---

## اختصارات لوحة المفاتيح

| الإجراء | الاختصار |
|---|---|
| تشغيل / إيقاف مؤقت | `Space` |
| إيقاف | `S` |
| التالي / السابق | `Ctrl+Right` / `Ctrl+Left` |
| تقديم / تأخير | `Right` / `Left` |
| رفع / خفض الصوت | `Up` / `Down` |
| كتم الصوت | `M` |
| ملء الشاشة | `F` |
| زيادة / خفض السرعة | `]` / `[` |
| السرعة الطبيعية | `\` |
| تكرار / خلط | `R` / `H` |
| فتح ملف | `Ctrl+O` |
| فتح رابط | `Ctrl+U` |
| الإعدادات | `Ctrl+P` |
| خروج | `Ctrl+Q` |

---

## الإتاحة (Accessibility)

- دعم كامل لقارئات الشاشة: **NVDA، JAWS، Narrator**.
- كل عنصر يعلن اسمه واختصاره ووصفه.
- ترتيب Tab واضح ومنطقي، وشريط التمرير عنصر مستقل يعلن المدة والمنقضي والمتبقي بالكلمات.
- ثيمات عالية التباين وخطوط قابلة للتكبير.
- لا يعتمد على السحب والإفلات (لتجنّب تعارضه مع قارئات الشاشة).

---

## اللغات

| اللغة | الرمز |
|---|---|
| العربية | `ar` |
| English | `en` |
| Italiano | `it` |
| Español | `es` |
| Português (Brasil) | `pt` |
| Türkçe | `tr` |

---

## بنية المشروع

```
src/
├── main.py                 # نقطة الدخول + وضع --selftest
├── core/                   # منطق التطبيق، الإعدادات، المسارات، الاختبار الذاتي
├── settings/               # إدارة الإعدادات
├── i18n/                   # الترجمة ومحتوى نافذة «حول»
├── accessibility/          # دعم قارئات الشاشة
├── media/                  # محرّك VLC، قوائم التشغيل، الترجمات، يوتيوب
├── ui/                     # الثيمات، العناصر، النوافذ، الحوارات
└── utils/
packaging/                  # PyInstaller + Inno Setup + اختبار المثبّت
resources/                  # الأيقونات وملفات الترجمة
tools/                      # أدوات توليد الأيقونة والترجمة والاتفاقية
```

---

## الترخيص والدعم

هذا المشروع **برنامج مجاني احتكاري** (Freeware — All Rights Reserved). الكود منشور للاطّلاع والمراجعة فقط، ولا يُسمح بنسخه أو تعديله أو إعادة توزيعه أو بيعه دون إذن كتابي مسبق. راجع [`LICENSE`](LICENSE) واتفاقية المستخدم النهائي [`packaging/EULA.txt`](packaging/EULA.txt).

- **المطوّر:** محمد مسعد — Mohamed Mosad
- **واتساب / تليجرام:** [+20 10 40 24 30 45](https://wa.me/201040243045)
- **الاقتراحات والبلاغات:** [GitHub Issues](https://github.com/midomosad311-lang/MS-Media-Player/issues)

---

# English

**MS Media Player** is a professional, fully accessible media player for Windows, built with **Python, PySide6 and the VLC engine**. It ships with a complete VLC runtime, so neither Python nor VLC needs to be installed.

[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11%20x64-0078D6?logo=windows&logoColor=white)](https://github.com/midomosad311-lang/MS-Media-Player/releases/latest)
[![Latest release](https://img.shields.io/github/v/release/midomosad311-lang/MS-Media-Player?label=latest)](https://github.com/midomosad311-lang/MS-Media-Player/releases/latest)

## Download

| Edition | File | Size |
|---|---|---|
| **Installer (recommended)** | [`MSMediaPlayer_Setup_1.0.0.exe`](https://github.com/midomosad311-lang/MS-Media-Player/releases/latest/download/MSMediaPlayer_Setup_1.0.0.exe) | ≈ 156 MB |
| **Portable** | [`MSMediaPlayer.exe`](https://github.com/midomosad311-lang/MS-Media-Player/releases/latest/download/MSMediaPlayer.exe) | ≈ 157 MB |

- **Requires:** Windows 10 or 11 (64-bit).
- **Does not require:** Python, VLC, or any external runtime.
- The installer is multilingual, shows the licence agreement, creates a desktop shortcut, and includes a full uninstaller.

### SHA-256 checksums

```
MSMediaPlayer.exe
13FE8379F8DD777B104FA924B7CC4F2DB5963FAC7E60D308622D0D9EE026C30F

MSMediaPlayer_Setup_1.0.0.exe
AEB789C385153EF4D0A389D1DEDAB38557718D3D9C78D1CB69096D529B34094E
```

## Features

- **Six languages:** Arabic, English, Italian, Spanish, Portuguese (Brazil) and Turkish — switched live, with automatic RTL for Arabic.
- **Full accessibility:** NVDA, JAWS and Narrator support; every control announces its name and shortcut; complete keyboard navigation; high-contrast themes.
- **Advanced playback:** 0.25×–4× speed, configurable seek intervals, A-B loop, bookmarks, and resume-where-you-left-off.
- **Playlists:** M3U support, shuffle, repeat, and multiple playlist windows.
- **Audio & video:** equalizer, audio sync, subtitles (SRT/ASS…), hardware acceleration, subtitle size/colour controls.
- **Network streaming:** HTTP, RTSP, RTMP, HLS, DASH, plus YouTube links via yt-dlp.
- **Modern UI:** light, dark and high-contrast themes with large accessible controls.
- **Fully standalone:** the complete VLC engine (DLLs + plugins) is bundled inside the executable.

## Install & run

### Installer (easiest)

1. Download `MSMediaPlayer_Setup_1.0.0.exe` from the [releases page](https://github.com/midomosad311-lang/MS-Media-Player/releases/latest).
2. Run it, choose a language, and accept the licence agreement.
3. Pick an install folder and click **Install**.
4. Launch **MS Media Player** from the desktop or Start menu.

### Portable

Download `MSMediaPlayer.exe` and run it directly — no installation or administrator rights required.

### From source

Requires Python 3.9+ and VLC 3.x installed:

```bash
git clone https://github.com/midomosad311-lang/MS-Media-Player.git
cd MS-Media-Player
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Or simply run `launch.bat` after installing the requirements.

## Build the executable and installer

Requires Python 3.12 (64-bit), PyInstaller, VLC 3.x, and Inno Setup 6.3+ (installer only).

```powershell
# 1) Build dist\MSMediaPlayer.exe
powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1

# 2) Build the installer
ISCC.exe /DExePath="dist\MSMediaPlayer.exe" packaging\installer.iss

# 3) Full self-test of the built executable
dist\MSMediaPlayer.exe --selftest --selftest-log "%TEMP%\msmp_selftest.log"
```

See [`packaging/README_BUILD.md`](packaging/README_BUILD.md) for details.

## Keyboard shortcuts

| Action | Shortcut |
|---|---|
| Play / pause | `Space` |
| Stop | `S` |
| Next / previous | `Ctrl+Right` / `Ctrl+Left` |
| Seek forward / backward | `Right` / `Left` |
| Volume up / down | `Up` / `Down` |
| Mute | `M` |
| Fullscreen | `F` |
| Speed up / down | `]` / `[` |
| Normal speed | `\` |
| Repeat / shuffle | `R` / `H` |
| Open file | `Ctrl+O` |
| Open URL | `Ctrl+U` |
| Settings | `Ctrl+P` |
| Quit | `Ctrl+Q` |

## Accessibility

- Full screen-reader support: **NVDA, JAWS, Narrator**.
- Every control announces its name, shortcut and description.
- Logical Tab order; the seek slider is its own Tab stop and announces elapsed, total and remaining time in words.
- High-contrast themes and scalable fonts.
- No drag-and-drop dependency (avoids screen-reader conflicts).

## Project structure

```
src/
├── main.py                 # Entry point (also handles --selftest)
├── core/                   # Application controller, config, paths, self-test
├── settings/               # Settings manager
├── i18n/                   # Translation manager and About content
├── accessibility/          # Screen-reader support
├── media/                  # VLC engine, playlists, subtitles, YouTube
├── ui/                     # Themes, widgets, windows, dialogs
└── utils/
packaging/                  # PyInstaller + Inno Setup + installer tests
resources/                  # Icons and translation catalogues
tools/                      # Icon, translation and EULA generators
```

## Licence & support

This is **proprietary freeware** (All Rights Reserved). The source is published for viewing and review only; copying, modifying, redistributing or selling it requires prior written permission. See [`LICENSE`](LICENSE) and the end-user licence agreement in [`packaging/EULA.txt`](packaging/EULA.txt).

- **Developer:** Mohamed Mosad (محمد مسعد)
- **WhatsApp / Telegram:** [+20 10 40 24 30 45](https://wa.me/201040243045)
- **Feedback & bug reports:** [GitHub Issues](https://github.com/midomosad311-lang/MS-Media-Player/issues)
