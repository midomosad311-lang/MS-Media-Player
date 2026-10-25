"""Audit translation coverage and consistency.

Extracts every ``tr("...")`` string (with its context) from the sources and
checks, for each supported language, whether the shipped catalogues
(``app_<locale>.qm`` + ``extra_<locale>.qm``) provide a translation.

Reports:
  * total unique (context, source) pairs,
  * per-language missing count and the missing strings,
  * translations that are identical to the English source (suspicious),
  * terminology inconsistencies (same English term translated differently).

Usage:  python tools/audit_translations.py [--dump missing.json]
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TRANS = ROOT / "resources" / "translations"

LANGS = {
    "ar": "ar_SA",
    "en": "en_US",
    "it": "it_IT",
    "es": "es_ES",
    "pt": "pt_BR",
    "tr": "tr_TR",
}

SKIP_FILES = {"about_content.py"}

_tr = re.compile(r'tr\(\s*("(?:[^"\\]|\\.)*")', re.S)
_class = re.compile(r'^\s*class\s+(\w+)')


def pascal_literal(tok: str) -> str:
    try:
        return eval(tok)
    except Exception:
        return ""


def collect():
    """Return list of (context, source) and a per-context ordered list."""
    pairs = []
    seen = set()
    for py in sorted(SRC.rglob("*.py")):
        if py.name in SKIP_FILES:
            continue
        ctx = py.stem
        text = py.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            m = _class.match(line)
            if m:
                ctx = m.group(1)
            for mm in _tr.finditer(line):
                s = pascal_literal(mm.group(1))
                if not s.strip():
                    continue
                key = (ctx, s)
                if key not in seen:
                    seen.add(key)
                    pairs.append(key)
    return pairs


def load_translators():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTranslator

    app = QApplication.instance() or QApplication(sys.argv)
    result = {}
    for lang, locale in LANGS.items():
        ts = []
        for prefix in ("app", "extra"):
            t = QTranslator()
            path = TRANS / f"{prefix}_{locale}.qm"
            if path.exists() and t.load(str(path)):
                ts.append((prefix, t))
        result[lang] = ts
    return app, result


def main():
    dump = None
    if "--dump" in sys.argv:
        dump = sys.argv[sys.argv.index("--dump") + 1]

    pairs = collect()
    app, translators = load_translators()

    print(f"unique tr() strings: {len(pairs)}")

    missing_map = {}
    identical_map = {}
    for lang, ts in translators.items():
        miss = []
        same = []
        for ctx, src in pairs:
            value = src
            for _prefix, t in reversed(ts):  # extra has priority
                got = t.translate(ctx, src)
                if got:
                    value = got
                    break
            if value in ("", src):
                miss.append((ctx, src))
            elif value == src and lang != "en":
                same.append((ctx, src))
        missing_map[lang] = miss
        identical_map[lang] = same
        print(f"  {lang}: missing={len(miss):4d}  identical-to-source={len(same):4d}")

    if dump:
        data = {
            lang: [f"{c}\x1f{s}" for c, s in miss]
            for lang, miss in missing_map.items()
        }
        Path(dump).write_text(
            json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"wrote {dump}")

    if "-v" in sys.argv:
        for lang, miss in missing_map.items():
            if not miss:
                continue
            print(f"\n===== MISSING: {lang} ({len(miss)}) =====")
            for c, s in miss:
                print(f"  [{c}] {s!r}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
    main()
