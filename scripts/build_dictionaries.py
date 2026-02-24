#!/usr/bin/env python3
"""Build webapp dictionary JSON from YAML sources.

Strips test_cases, negative_cases, notes, source (not needed at runtime).
Keeps: id, category, type, severity, detect, replacements, suffix_type.
"""

import json
import sys
from pathlib import Path

# Add parent so nsp_proselint is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nsp_proselint.loader import DictionaryLoader


def build(lang: str, out_dir: Path) -> int:
    """Build JSON for one language. Returns entry count."""
    dictionary = DictionaryLoader.load_builtin(lang)
    entries = []
    for e in dictionary.entries:
        entry = {
            "id": e.id,
            "category": e.category,
            "type": e.type,
            "severity": e.severity,
            "detect": e.detect,
            "replacements": e.replacements,
        }
        if e.suffix_type:
            entry["suffix_type"] = e.suffix_type
        entries.append(entry)

    out_path = out_dir / f"{lang}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    return len(entries)


def main():
    out_dir = Path(__file__).resolve().parent.parent / "webapp" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    langs = ["zh_CN", "en"]
    for lang in langs:
        count = build(lang, out_dir)
        print(f"{lang}: {count} entries -> {out_dir / f'{lang}.json'}")

    print("Done.")


if __name__ == "__main__":
    main()
