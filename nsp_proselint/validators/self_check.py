"""Cross-pattern self-cliche check: verify no replacement is matched by another pattern."""

from dataclasses import dataclass

from ..loader import Dictionary, PatternEntry


@dataclass
class SelfClicheWarning:
    entry_id: str
    replacement: str
    matched_by: str  # pattern id that matches the replacement


def check_self_cliche(entry: PatternEntry, all_entries: list[PatternEntry]) -> list[SelfClicheWarning]:
    """Check if any replacement of this entry is itself matched by another pattern.

    Returns list of warnings (empty = clean).
    """
    warnings = []
    for repl in entry.replacements:
        for other in all_entries:
            if other.id == entry.id:
                continue
            if other.compiled.search(repl):
                warnings.append(SelfClicheWarning(
                    entry_id=entry.id,
                    replacement=repl,
                    matched_by=other.id,
                ))
    return warnings


def check_dictionary_self_cliche(dictionary: Dictionary) -> list[SelfClicheWarning]:
    """Run self-cliche check across all entries in a dictionary.

    Returns list of all warnings found.
    """
    all_warnings = []
    for entry in dictionary.entries:
        warnings = check_self_cliche(entry, dictionary.entries)
        all_warnings.extend(warnings)
    return all_warnings
