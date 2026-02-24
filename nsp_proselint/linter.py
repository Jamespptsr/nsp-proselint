"""Core linter engine: detect + replace cliche patterns."""

import re
import random
from dataclasses import dataclass
from typing import Optional

from .loader import DictionaryLoader, Dictionary, PatternEntry


@dataclass
class LintHit:
    clause: str
    pattern_id: str
    category: str
    match_text: str
    match_start: int
    match_end: int
    severity: str


@dataclass
class Diff:
    original: str
    replacement: str
    pattern_id: str
    clause_index: int


# Split after Chinese/English clause-ending punctuation.
# Keeps the delimiter attached to the preceding clause.
_CLAUSE_SPLIT_RE = re.compile(r"(?<=[，。！？；、.!?;,])")


def _is_attributive_context(match_text: str, clause: str, match_start: int) -> bool:
    """Check if match is in attributive context (ends with 的).

    When a regex match ends with "的", the greedy tail has consumed into a
    modifier structure (e.g. "极其细微的弧度", "极其细微的、近乎残忍的").
    A full replacement would break sentence structure. Skip these hits.
    """
    return match_text.endswith("的")


def _split_clauses(text: str) -> list[str]:
    """Split text into clauses by punctuation boundaries."""
    parts = _CLAUSE_SPLIT_RE.split(text)
    # Filter trailing empty string from split after final punctuation
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts if parts else [""]


class ProseLinter:

    def __init__(self, lang: str = "zh_CN", dictionary: Optional[Dictionary] = None):
        if dictionary:
            self._dict = dictionary
        else:
            self._dict = DictionaryLoader.load_builtin(lang)

    @property
    def language(self) -> str:
        return self._dict.language

    @property
    def entries(self) -> list[PatternEntry]:
        return self._dict.entries

    def lint(self, text: str) -> list[LintHit]:
        """Detect cliches without replacing. Returns list of hits."""
        hits = []
        for para in text.split("\n"):
            if not para.strip():
                continue
            for clause in _split_clauses(para):
                if not clause.strip():
                    continue
                for entry in self._dict.entries:
                    m = entry.compiled.search(clause)
                    if m:
                        if _is_attributive_context(m.group(0), clause, m.start()):
                            continue
                        hits.append(LintHit(
                            clause=clause,
                            pattern_id=entry.id,
                            category=entry.category,
                            match_text=m.group(0),
                            match_start=m.start(),
                            match_end=m.end(),
                            severity=entry.severity,
                        ))
                        break  # first match per clause

        return hits

    def replace(self, text: str) -> str:
        """Detect and replace cliches. Returns cleaned text."""
        result, _ = self.replace_with_diff(text)
        return result

    def replace_with_diff(self, text: str) -> tuple[str, list[Diff]]:
        """Detect and replace cliches, tracking all changes.

        Returns (replaced_text, list_of_diffs).
        """
        diffs = []
        result_paragraphs = []
        clause_index = 0

        for para in text.split("\n"):
            if not para.strip():
                result_paragraphs.append(para)
                continue

            clauses = _split_clauses(para)
            result_clauses = []

            for clause in clauses:
                if not clause.strip():
                    result_clauses.append(clause)
                    continue

                replaced = False
                for entry in self._dict.entries:
                    m = entry.compiled.search(clause)
                    if m:
                        if _is_attributive_context(m.group(0), clause, m.start()):
                            continue
                        if entry.severity == "replace" and entry.replacements:
                            repl = random.choice(entry.replacements)
                            new_clause = clause[:m.start()] + repl + clause[m.end():]
                            diffs.append(Diff(
                                original=m.group(0),
                                replacement=repl,
                                pattern_id=entry.id,
                                clause_index=clause_index,
                            ))
                            result_clauses.append(new_clause)
                            replaced = True
                        # First match per clause, whether replaced or not
                        break

                if not replaced:
                    result_clauses.append(clause)
                clause_index += 1

            result_paragraphs.append("".join(result_clauses))

        return "\n".join(result_paragraphs), diffs
