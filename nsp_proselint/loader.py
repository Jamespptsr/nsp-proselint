"""Dictionary loader: YAML -> compiled patterns."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class TestCase:
    input: str
    valid_outputs: list[str]
    suffix: Optional[str] = None


@dataclass
class PatternEntry:
    id: str
    category: str
    type: str  # full | prefix | modifier
    severity: str  # replace | detect_only
    detect: str  # raw regex string
    compiled: re.Pattern  # compiled regex
    replacements: list[str]
    test_cases: list[TestCase]
    suffix_type: Optional[str] = None
    negative_cases: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    source: Optional[str] = None


@dataclass
class Dictionary:
    version: str
    language: str
    entries: list[PatternEntry]


class DictionaryLoader:

    @staticmethod
    def load(path: str | Path) -> Dictionary:
        """Load a dictionary from a YAML file path."""
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        entries = []
        for raw in data.get("entries", []):
            test_cases = []
            for tc in raw.get("test_cases", []):
                test_cases.append(TestCase(
                    input=tc["input"],
                    valid_outputs=tc.get("valid_outputs", []),
                    suffix=tc.get("suffix"),
                ))

            entry = PatternEntry(
                id=raw["id"],
                category=raw["category"],
                type=raw["type"],
                severity=raw["severity"],
                detect=raw["detect"],
                compiled=re.compile(raw["detect"]),
                replacements=raw.get("replacements", []),
                test_cases=test_cases,
                suffix_type=raw.get("suffix_type"),
                negative_cases=raw.get("negative_cases", []),
                notes=raw.get("notes"),
                source=raw.get("source"),
            )
            entries.append(entry)

        return Dictionary(
            version=data.get("version", "0.1.0"),
            language=data.get("language", "unknown"),
            entries=entries,
        )

    @staticmethod
    def load_builtin(lang: str) -> Dictionary:
        """Load a built-in dictionary by language code (e.g. 'zh_CN', 'en')."""
        dict_dir = Path(__file__).parent / "dictionaries"
        path = dict_dir / f"{lang}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"No built-in dictionary for language: {lang}")
        return DictionaryLoader.load(path)
