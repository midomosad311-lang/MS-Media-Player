"""Build the application's translation catalogues from reviewable JSON files.

The application ships one *complete* catalogue per language instead of the
historical split between ``app_<locale>.qm`` (partial) and ``extra_<locale>.qm``
(fill-in).  A single catalogue per language guarantees that

  * every string exists in every language (no silent fall-back to English),
  * the same concept is always translated the same way (one file per language),
  * no language is treated as more complete than another.

Sources of truth
----------------
``resources/translations/msmp_<lang>.json``  (``{context: {source: translation}}``)

Commands
--------
``python tools/build_translations.py extract``
    Seed the JSON catalogues from the existing ``app_*.qm`` / ``extra_*.qm``
    catalogues (only creates entries that do not exist yet).

``python tools/build_translations.py report``
    Show how many strings each language is still missing.

``python tools/build_translations.py build``
    Generate ``msmp_<locale>.ts`` and compile ``msmp_<locale>.qm`` with
    ``pyside6-lrelease``.
"""

import json
import re
import subprocess
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

LRELEASE = Path(sys.executable).parent / "Scripts" / "pyside6-lrelease.exe"
if not LRELEASE.exists():
    LRELEASE = Path(sys.executable).parent / "pyside6-lrelease.exe"


def pascal_literal(tok: str) -> str:
    try:
        return eval(tok)
    except Exception:
        return ""


def collect_pairs():
    """Return ordered list of (context, source) for every tr() string."""
    pairs, seen = [], set()
    for py in sorted(SRC.rglob("*.py")):
        if py.name in SKIP_FILES:
            continue
        ctx = py.stem
        for line in py.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _class.match(line)
            if m:
                ctx = m.group(1)
            for mm in _tr.finditer(line):
                s = pascal_literal(mm.group(1))
                if not s.strip():
                    continue
                if (ctx, s) not in seen:
                    seen.add((ctx, s))
                    pairs.append((ctx, s))
    return pairs


def catalogue_path(lang: str) -> Path:
    return TRANS / f"msmp_{lang}.json"


def load_catalogue(lang: str) -> dict:
    p = catalogue_path(lang)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_catalogue(lang: str, data: dict) -> None:
    data = {ctx: dict(sorted(entries.items())) for ctx, entries in sorted(data.items())}
    catalogue_path(lang).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def existing_translators():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTranslator

    QApplication.instance() or QApplication(sys.argv)
    out = {}
    for lang, locale in LANGS.items():
        ts = []
        for prefix in ("app", "extra"):
            t = QTranslator()
            path = TRANS / f"{prefix}_{locale}.qm"
            if path.exists() and t.load(str(path)):
                ts.append(t)
        out[lang] = ts
    return out


def translate_from(ts, ctx: str, src: str) -> str:
    for t in reversed(ts):
        got = t.translate(ctx, src)
        if got:
            return got
    return ""


def cmd_extract():
    pairs = collect_pairs()
    translators = existing_translators()
    for lang in LANGS:
        data = load_catalogue(lang)
        added = 0
        for ctx, src in pairs:
            bucket = data.setdefault(ctx, {})
            if bucket.get(src):
                continue
            if lang == "en":
                value = src
            else:
                value = translate_from(translators[lang], ctx, src)
            if value:
                bucket[src] = value
                added += 1
        save_catalogue(lang, data)
        print(f"{lang}: +{added} entries extracted")
    print(f"total tr() strings: {len(pairs)}")


def _identity_sources() -> set:
    """Strings that are *deliberately* identical in every language.

    Technical names, protocols, video resolutions and international loan words
    (see tools/fill_translations.py) - they must not be reported as gaps.
    """
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import fill_translations  # noqa: WPS433
        return set(fill_translations.IDENTITY) | set(
            fill_translations.IDENTITY_WORDS["sources"]
        )
    except Exception:
        return set()


def cmd_report(verbose: bool = False):
    pairs = collect_pairs()
    identity = _identity_sources()
    for lang in LANGS:
        data = load_catalogue(lang)
        missing, untranslated = [], []
        for ctx, src in pairs:
            value = data.get(ctx, {}).get(src)
            if not value:
                missing.append((ctx, src))
            elif lang != "en" and value == src and src not in identity:
                # present but still in English -> a hidden translation gap
                untranslated.append((ctx, src))
        status = "complete" if not (missing or untranslated) else ""
        print(
            f"{lang}: {len(pairs) - len(missing)}/{len(pairs)}  "
            f"missing={len(missing)}  untranslated={len(untranslated)}  {status}"
        )
        if verbose:
            for ctx, src in missing:
                print(f"  MISSING      [{ctx}] {src!r}")
            for ctx, src in untranslated:
                print(f"  UNTRANSLATED [{ctx}] {src!r}")
    return pairs


def xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cmd_build():
    pairs = collect_pairs()
    wanted = set(pairs)
    ctx_order = []
    for ctx, _src in pairs:
        if ctx not in ctx_order:
            ctx_order.append(ctx)

    for lang, locale in LANGS.items():
        data = load_catalogue(lang)
        # Drop entries that no longer exist in the source (renamed/removed
        # strings) so the shipped catalogue only ever contains live strings.
        pruned = 0
        for ctx in list(data):
            for src in list(data[ctx]):
                if (ctx, src) not in wanted:
                    del data[ctx][src]
                    pruned += 1
            if not data[ctx]:
                del data[ctx]
        if pruned:
            save_catalogue(lang, data)

        lines = ['<?xml version="1.0" encoding="utf-8"?>', "<!DOCTYPE TS>", '<TS version="2.1">']
        count = 0
        for ctx in ctx_order:
            entries = data.get(ctx, {})
            msgs = []
            for src in entries:
                value = entries[src]
                space = ' xml:space="preserve"' if src != src.strip() else ""
                msgs.append(
                    "    <message>\n"
                    f"        <source{space}>{xml_escape(src)}</source>\n"
                    f"        <translation>{xml_escape(value)}</translation>\n"
                    "    </message>"
                )
                count += 1
            if msgs:
                lines.append(f"  <context>\n    <name>{ctx}</name>")
                lines.extend(msgs)
                lines.append("  </context>")
        lines.append("</TS>")
        ts_path = TRANS / f"msmp_{locale}.ts"
        ts_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        qm_path = TRANS / f"msmp_{locale}.qm"
        result = subprocess.run(
            [str(LRELEASE), str(ts_path), "-qm", str(qm_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"lrelease FAILED for {locale}:\n{result.stdout}\n{result.stderr}")
        else:
            extra = f", pruned {pruned} stale" if pruned else ""
            print(f"{lang}: {count} messages -> {qm_path.name} ({qm_path.stat().st_size} bytes){extra}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    if mode == "extract":
        cmd_extract()
    elif mode == "report":
        cmd_report()
    elif mode == "build":
        cmd_build()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
