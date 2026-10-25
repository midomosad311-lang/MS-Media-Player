"""Generate supplementary Qt translation files (extra_<locale>.ts/.qm).

The original ``app_<locale>.qm`` catalogues are incomplete: many UI strings
added later (bookmarks, equalizer, playlist manager, YouTube, subtitle
options, tooltips, ...) have no translation.  Rather than regenerating the
whole catalogue, this script builds a small *extra* catalogue per language
from the ``extra_<lang>.json`` files and compiles it with ``pyside6-lrelease``.
``TranslationManager`` installs it as a second translator, so the extra entries
take precedence for the strings the main catalogue is missing.

Usage:  python tools/gen_extra_ts.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANS_DIR = ROOT / "resources" / "translations"

# language code -> Qt locale suffix
LANGS = {
    "ar": "ar_SA",
    "it": "it_IT",
    "es": "es_ES",
    "pt": "pt_BR",
    "tr": "tr_TR",
    "en": "en_US",
}

LRELEASE = Path(sys.executable).parent / "Scripts" / "pyside6-lrelease.exe"
if not LRELEASE.exists():
    LRELEASE = Path(sys.executable).parent / "pyside6-lrelease.exe"


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def attr_space(text: str) -> str:
    # Preserve meaningful leading/trailing whitespace (e.g. "Playing: ").
    return ' xml:space="preserve"' if text != text.strip() else ""


def load_missing():
    """Map 'ctx\\x1fsource' -> set(locales) that are missing this string."""
    path = TRANS_DIR / "missing_strings.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: set(v) for k, v in data.items()}


def build_ts(lang: str, locale: str, messages: dict, missing: dict) -> Path:
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<!DOCTYPE TS>", '<TS version="2.1">']
    included = 0
    for context, entries in messages.items():
        ctx_lines = []
        for source, translation in entries.items():
            # Only emit messages that the main catalogue lacks, so we never
            # override an existing (good) translation.
            if missing is not None and lang != "en":
                key = f"{context}\x1f{source}"
                if locale not in missing.get(key, set()):
                    continue
            ctx_lines.append(
                f"    <message>\n"
                f"        <source{attr_space(source)}>{xml_escape(source)}</source>\n"
                f"        <translation>{xml_escape(translation)}</translation>\n"
                f"    </message>"
            )
            included += 1
        if ctx_lines:
            lines.append(f'  <context>\n    <name>{context}</name>')
            lines.extend(ctx_lines)
            lines.append("  </context>")
    lines.append("</TS>")
    ts_path = TRANS_DIR / f"extra_{locale}.ts"
    ts_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{ts_path.name}: {included} messages")
    return ts_path


def main():
    missing = load_missing()
    for lang, locale in LANGS.items():
        json_path = TRANS_DIR / f"extra_{lang}.json"
        if not json_path.exists():
            print(f"skip {lang}: {json_path.name} not found")
            continue
        messages = json.loads(json_path.read_text(encoding="utf-8"))
        ts_path = build_ts(lang, locale, messages, missing)
        qm_path = TRANS_DIR / f"extra_{locale}.qm"
        result = subprocess.run(
            [str(LRELEASE), str(ts_path), "-qm", str(qm_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  lrelease FAILED for {locale}:\n{result.stdout}\n{result.stderr}")
        else:
            print(f"  -> {qm_path.name} ({qm_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
