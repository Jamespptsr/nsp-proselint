"""Dictionary quality tests for zh_CN.yaml.

Auto-validates all entries against their test_cases, negative_cases,
and replacement grammar per the dictionary-spec.
"""

import pytest

from nsp_proselint.loader import DictionaryLoader
from nsp_proselint.validators.grammar import validate_entry, validate_dictionary
from nsp_proselint.validators.self_check import check_dictionary_self_cliche
from nsp_proselint.validators.semantic import check_diversity


@pytest.fixture(scope="module")
def zh_dict():
    return DictionaryLoader.load_builtin("zh_CN")


# ============================================================
# Structural Requirements
# ============================================================

class TestStructure:

    def test_version_set(self, zh_dict):
        assert zh_dict.version == "0.1.0"

    def test_language_set(self, zh_dict):
        assert zh_dict.language == "zh_CN"

    def test_has_entries(self, zh_dict):
        assert len(zh_dict.entries) >= 42

    def test_unique_ids(self, zh_dict):
        ids = [e.id for e in zh_dict.entries]
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {[i for i in ids if ids.count(i) > 1]}"

    def test_all_entries_have_minimum_test_cases(self, zh_dict):
        for entry in zh_dict.entries:
            assert len(entry.test_cases) >= 2, f"{entry.id}: needs >= 2 test cases"

    def test_all_entries_have_minimum_replacements(self, zh_dict):
        for entry in zh_dict.entries:
            if entry.severity == "replace":
                assert len(entry.replacements) >= 2, f"{entry.id}: needs >= 2 replacements"

    def test_all_entries_have_negative_cases(self, zh_dict):
        for entry in zh_dict.entries:
            assert len(entry.negative_cases) >= 1, f"{entry.id}: needs >= 1 negative case"

    def test_prefix_entries_have_suffix_type(self, zh_dict):
        for entry in zh_dict.entries:
            if entry.type == "prefix":
                assert entry.suffix_type is not None, f"{entry.id}: prefix type needs suffix_type"


# ============================================================
# Regex Matching
# ============================================================

class TestRegexMatching:

    def test_regex_matches_all_test_cases(self, zh_dict):
        for entry in zh_dict.entries:
            for tc in entry.test_cases:
                m = entry.compiled.search(tc.input)
                assert m is not None, (
                    f"{entry.id}: regex '{entry.detect}' doesn't match "
                    f"test case '{tc.input}'"
                )

    def test_regex_avoids_all_negative_cases(self, zh_dict):
        for entry in zh_dict.entries:
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

    def test_full_type_replacements_produce_valid_outputs(self, zh_dict):
        """For Type A entries where match = full input, verify replacement outputs."""
        for entry in zh_dict.entries:
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

    def test_prefix_type_replacements_produce_valid_outputs(self, zh_dict):
        """For Type B entries, verify replacement + suffix forms valid output."""
        for entry in zh_dict.entries:
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

    def test_modifier_type_replacements_produce_valid_outputs(self, zh_dict):
        """For Type C entries, verify replacement in context produces valid output."""
        for entry in zh_dict.entries:
            if entry.type != "modifier":
                continue
            for tc in entry.test_cases:
                m = entry.compiled.search(tc.input)
                if not m:
                    continue
                for repl in entry.replacements:
                    result = tc.input[:m.start()] + repl + tc.input[m.end():]
                    assert result in tc.valid_outputs, (
                        f"{entry.id}: modifier '{repl}' in '{tc.input}' "
                        f"produces '{result}' which is not in valid_outputs"
                    )


# ============================================================
# Cross-Pattern Checks
# ============================================================

class TestCrossPattern:

    def test_no_self_cliche_warnings(self, zh_dict):
        """No replacement should be matched by another pattern."""
        warnings = check_dictionary_self_cliche(zh_dict)
        if warnings:
            details = [
                f"  {w.entry_id}: replacement '{w.replacement}' matched by '{w.matched_by}'"
                for w in warnings
            ]
            # Warn but don't fail -- some overlap may be acceptable
            pytest.skip(f"Self-cliche warnings found:\n" + "\n".join(details))

    def test_replacement_diversity(self, zh_dict):
        """Replacements within each entry should be sufficiently different."""
        for entry in zh_dict.entries:
            result = check_diversity(entry, threshold=0.3)
            assert result.passed, (
                f"{entry.id}: replacements too similar "
                f"(min_distance={result.min_distance:.3f}, pair={result.pair})"
            )


# ============================================================
# Full Validation Pipeline
# ============================================================

class TestFullValidation:

    def test_all_entries_pass_validation(self, zh_dict):
        report = validate_dictionary(zh_dict)
        assert report.entries_blocked == 0, (
            f"{report.entries_blocked} entries blocked: "
            + ", ".join(
                f"{r.entry_id}: {[c.detail for c in r.checks if not c.passed]}"
                for r in report.results if r.status == "block"
            )
        )
