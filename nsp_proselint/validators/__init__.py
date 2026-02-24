"""Validation tools for dictionary entries and replacement quality."""

from .grammar import (
    validate_entry,
    validate_dictionary,
    CheckResult,
    EntryValidationResult,
    DictionaryValidationReport,
)
from .self_check import (
    check_self_cliche,
    check_dictionary_self_cliche,
    SelfClicheWarning,
)
from .semantic import (
    check_diversity,
    DiversityResult,
)

__all__ = [
    "validate_entry",
    "validate_dictionary",
    "CheckResult",
    "EntryValidationResult",
    "DictionaryValidationReport",
    "check_self_cliche",
    "check_dictionary_self_cliche",
    "SelfClicheWarning",
    "check_diversity",
    "DiversityResult",
]
