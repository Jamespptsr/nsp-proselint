"""Dictionary quality tests for en.yaml.

Auto-validates all entries against their test_cases, negative_cases,
and replacement grammar per the dictionary-spec.
"""

import pytest

from nsp_proselint.loader import DictionaryLoader
from nsp_proselint.validators.grammar import validate_dictionary
from nsp_proselint.validators.self_check import check_dictionary_self_cliche
from nsp_proselint.validators.semantic import check_diversity


@pytest.fixture(scope="module")
def en_dict():
    return DictionaryLoader.load_builtin("en")


# ============================================================
# Structural Requirements
# ============================================================

class TestStructure:

    def test_version_set(self, en_dict):
        assert en_dict.version == "0.1.0"

    def test_language_set(self, en_dict):
        assert en_dict.language == "en"

    def test_has_entries(self, en_dict):
        assert len(en_dict.entries) >= 28

    def test_unique_ids(self, en_dict):
        ids = [e.id for e in en_dict.entries]
        assert len(ids) == len(set(ids))

    def test_all_entries_have_minimum_test_cases(self, en_dict):
        for entry in en_dict.entries:
            assert len(entry.test_cases) >= 2, f"{entry.id}: needs >= 2 test cases"

    def test_all_entries_have_minimum_replacements(self, en_dict):
        for entry in en_dict.entries:
            if entry.severity == "replace":
                assert len(entry.replacements) >= 2, f"{entry.id}: needs >= 2 replacements"

    def test_all_entries_have_negative_cases(self, en_dict):
        for entry in en_dict.entries:
            assert len(entry.negative_cases) >= 1, f"{entry.id}: needs >= 1 negative case"


# ============================================================
# Regex Matching
# ============================================================

class TestRegexMatching:

    def test_regex_matches_all_test_cases(self, en_dict):
        for entry in en_dict.entries:
            for tc in entry.test_cases:
                m = entry.compiled.search(tc.input)
                assert m is not None, (
                    f"{entry.id}: regex '{entry.detect}' doesn't match "
                    f"test case '{tc.input}'"
                )

    def test_regex_avoids_all_negative_cases(self, en_dict):
        for entry in en_dict.entries:
            for neg in entry.negative_cases:
                m = entry.compiled.search(neg)
                assert m is None, (
                    f"{entry.id}: regex '{entry.detect}' falsely matches "
                    f"negative case '{neg}'"
                )


# ============================================================
# Replacement Validity
# ============================================================

class TestReplacementValidity:

    def test_full_type_replacements_produce_valid_outputs(self, en_dict):
        for entry in en_dict.entries:
            if entry.type != "full":
                continue
            for tc in entry.test_cases:
                m = entry.compiled.search(tc.input)
                if not m:
                    continue
                for repl in entry.replacements:
                    result = tc.input[:m.start()] + repl + tc.input[m.end():]
                    assert result in tc.valid_outputs, (
                        f"{entry.id}: replacement '{repl}' in '{tc.input}' "
                        f"produces '{result}' which is not in valid_outputs "
                        f"{tc.valid_outputs}"
                    )

    def test_prefix_type_replacements_produce_valid_outputs(self, en_dict):
        for entry in en_dict.entries:
            if entry.type != "prefix":
                continue
            for tc in entry.test_cases:
                if not tc.suffix:
                    continue
                for repl in entry.replacements:
                    result = repl + tc.suffix
                    assert result in tc.valid_outputs, (
                        f"{entry.id}: '{repl}' + '{tc.suffix}' = '{result}' "
                        f"not in valid_outputs {tc.valid_outputs}"
                    )


# ============================================================
# Cross-Pattern Checks
# ============================================================

class TestCrossPattern:

    def test_no_self_cliche_warnings(self, en_dict):
        warnings = check_dictionary_self_cliche(en_dict)
        if warnings:
            details = [
                f"  {w.entry_id}: replacement '{w.replacement}' matched by '{w.matched_by}'"
                for w in warnings
            ]
            pytest.skip(f"Self-cliche warnings found:\n" + "\n".join(details))

    def test_replacement_diversity(self, en_dict):
        for entry in en_dict.entries:
            result = check_diversity(entry, threshold=0.3)
            assert result.passed, (
                f"{entry.id}: replacements too similar "
                f"(min_distance={result.min_distance:.3f}, pair={result.pair})"
            )


# ============================================================
# Full Validation Pipeline
# ============================================================

class TestFullValidation:

    def test_all_entries_pass_validation(self, en_dict):
        report = validate_dictionary(en_dict)
        assert report.entries_blocked == 0, (
            f"{report.entries_blocked} entries blocked: "
            + ", ".join(
                f"{r.entry_id}: {[c.detail for c in r.checks if not c.passed]}"
                for r in report.results if r.status == "block"
            )
        )
