"""Report which UI strings have no translation in the shipped .qm catalogues.

Writes ``resources/translations/missing_strings.json`` mapping
``"<Context>\\x1f<source>"`` -> list of locales that lack the string.  This file
is consumed by ``tools/gen_extra_ts.py`` so that only genuinely missing strings
are added to the supplementary catalogues.

Usage:  python tools/gen_missing.py
"""

import re
import sys
import json
from collections import Counter
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator

ROOT = Path(__file__).resolve().parent.parent
TRANS_DIR = ROOT / "resources" / "translations"
SRC_DIR = ROOT / "src"

LANGS = ["ar_SA", "it_IT", "es_ES", "pt_BR", "tr_TR"]


def main():
    app = QApplication(sys.argv)  # noqa: F841 - required for QTranslator
    translators = {}
    for code in LANGS:
        t = QTranslator()
        t.load(str(TRANS_DIR / f"app_{code}.qm"))
        translators[code] = t

    pat = re.compile(r'tr\(("(?:[^"\\]|\\.)*")\)')
    class_pat = re.compile(r'^\s*class\s+(\w+)')

    items = []
    seen = set()
    for py in SRC_DIR.rglob("*.py"):
        if py.name in ("about_content.py",):
            continue
        ctx = py.stem
        for line in py.read_text(encoding="utf-8", errors="replace").splitlines():
            m = class_pat.match(line)
            if m:
                ctx = m.group(1)
            for mm in pat.finditer(line):
                try:
                    s = eval(mm.group(1))
                except Exception:
                    continue
                if not s.strip():
                    continue
                key = (ctx, s)
                if key not in seen:
                    seen.add(key)
                    items.append(key)

    missing = {}
    for ctx, s in items:
        langs = [c for c in LANGS if translators[c].translate(ctx, s) in ("", s)]
        if langs:
            missing[f"{ctx}\x1f{s}"] = langs

    out = TRANS_DIR / "missing_strings.json"
    out.write_text(json.dumps(missing, ensure_ascii=False, indent=1), encoding="utf-8")
    print("unique tr strings:", len(items))
    print("missing in >=1 lang:", len(missing))
    counts = Counter(k.split("\x1f")[0] for k in missing)
    for ctx, n in counts.most_common():
        print(f"  {ctx}: {n}")


if __name__ == "__main__":
    main()
