"""Tests for the validation framework."""

import re
import pytest

from nsp_proselint.loader import PatternEntry, TestCase, Dictionary
from nsp_proselint.validators.grammar import (
    check_regex_compile,
    check_test_coverage,
    check_negative_cases,
    check_replacement_grammar,
    check_minimum_requirements,
    validate_entry,
    validate_dictionary,
)
from nsp_proselint.validators.self_check import (
    check_self_cliche,
    check_dictionary_self_cliche,
)
from nsp_proselint.validators.semantic import (
    check_diversity,
    _edit_distance,
    _normalized_distance,
)


def _make_entry(**kwargs) -> PatternEntry:
    """Helper to create a PatternEntry with defaults."""
    defaults = dict(
        id="test",
        category="test",
        type="full",
        severity="replace",
        detect="test pattern",
        compiled=re.compile("test pattern"),
        replacements=["alt one", "alt two"],
        test_cases=[
            TestCase(input="this is a test pattern here", valid_outputs=["this is a alt one here"]),
            TestCase(input="another test pattern", valid_outputs=["another alt one"]),
        ],
        negative_cases=["not a match"],
    )
    defaults.update(kwargs)
    if "compiled" not in kwargs and "detect" in kwargs:
        defaults["compiled"] = re.compile(kwargs["detect"])
    return PatternEntry(**defaults)


# ============================================================
# Regex Compilation
# ============================================================

class TestRegexCompile:

    def test_valid_regex(self):
        entry = _make_entry(detect="hello.*world")
        result = check_regex_compile(entry)
        assert result.passed

    def test_invalid_regex(self):
        entry = _make_entry(detect="hello[", compiled=re.compile("x"))
        # Override compiled to avoid error during entry creation
        entry.detect = "hello["
        result = check_regex_compile(entry)
        assert not result.passed
        assert "BLOCK" in result.detail


# ============================================================
# Test Coverage
# ============================================================

class TestTestCoverage:

    def test_all_match(self):
        entry = _make_entry()
        result = check_test_coverage(entry)
        assert result.passed

    def test_one_fails(self):
        entry = _make_entry(
            test_cases=[
                TestCase(input="test pattern", valid_outputs=[]),
                TestCase(input="no match here", valid_outputs=[]),
            ]
        )
        result = check_test_coverage(entry)
        assert not result.passed
        assert "no match here" in result.detail


# ============================================================
# Negative Cases
# ============================================================

class TestNegativeCases:

    def test_no_false_positives(self):
        entry = _make_entry(negative_cases=["unrelated text", "other stuff"])
        result = check_negative_cases(entry)
        assert result.passed

    def test_false_positive_detected(self):
        entry = _make_entry(negative_cases=["this has test pattern in it"])
        result = check_negative_cases(entry)
        assert not result.passed
        assert "WARN" in result.detail


# ============================================================
# Replacement Grammar
# ============================================================

class TestReplacementGrammar:

    def test_full_type_passes(self):
        entry = _make_entry(type="full", replacements=["good alternative", "another one"])
        result = check_replacement_grammar(entry)
        assert result.passed

    def test_full_type_too_short(self):
        entry = _make_entry(type="full", replacements=["x", "good one"])
        result = check_replacement_grammar(entry)
        assert not result.passed

    def test_prefix_type_passes(self):
        entry = _make_entry(
            type="prefix",
            detect="prefix ",
            compiled=re.compile("prefix "),
            replacements=["alt1 ", "alt2 "],
            test_cases=[
                TestCase(input="prefix suffix", suffix="suffix",
                         valid_outputs=["alt1 suffix", "alt2 suffix"]),
                TestCase(input="prefix other", suffix="other",
                         valid_outputs=["alt1 other", "alt2 other"]),
            ],
        )
        result = check_replacement_grammar(entry)
        assert result.passed

    def test_prefix_type_fails(self):
        entry = _make_entry(
            type="prefix",
            detect="prefix ",
            compiled=re.compile("prefix "),
            replacements=["alt1 ", "alt2 "],
            test_cases=[
                TestCase(input="prefix suffix", suffix="suffix",
                         valid_outputs=["alt1 suffix"]),  # missing alt2 suffix
                TestCase(input="prefix other", suffix="other",
                         valid_outputs=["alt1 other", "alt2 other"]),
            ],
        )
        result = check_replacement_grammar(entry)
        assert not result.passed

    def test_modifier_type_passes(self):
        entry = _make_entry(
            type="modifier",
            detect="badly",
            compiled=re.compile("badly"),
            replacements=["poorly", "terribly"],
            test_cases=[
                TestCase(input="he did badly today",
                         valid_outputs=["he did poorly today", "he did terribly today"]),
                TestCase(input="she sang badly",
                         valid_outputs=["she sang poorly", "she sang terribly"]),
            ],
        )
        result = check_replacement_grammar(entry)
        assert result.passed

    def test_detect_only_skipped(self):
        entry = _make_entry(severity="detect_only", replacements=[])
        result = check_replacement_grammar(entry)
        assert result.passed


# ============================================================
# Minimum Requirements
# ============================================================

class TestMinimumRequirements:

    def test_passes_with_good_entry(self):
        entry = _make_entry()
        result = check_minimum_requirements(entry)
        assert result.passed

    def test_fails_too_few_test_cases(self):
        entry = _make_entry(test_cases=[TestCase(input="one", valid_outputs=[])])
        result = check_minimum_requirements(entry)
        assert not result.passed

    def test_fails_too_few_replacements(self):
        entry = _make_entry(replacements=["only one"])
        result = check_minimum_requirements(entry)
        assert not result.passed

    def test_fails_no_negative_cases(self):
        entry = _make_entry(negative_cases=[])
        result = check_minimum_requirements(entry)
        assert not result.passed

    def test_detect_only_no_replacement_needed(self):
        entry = _make_entry(severity="detect_only", replacements=[])
        result = check_minimum_requirements(entry)
        assert result.passed


# ============================================================
# Self-Cliche Check
# ============================================================

class TestSelfCliche:

    def test_no_self_cliche(self):
        entries = [
            _make_entry(id="a", detect="pattern_a", compiled=re.compile("pattern_a"),
                        replacements=["clean_one", "clean_two"]),
            _make_entry(id="b", detect="pattern_b", compiled=re.compile("pattern_b"),
                        replacements=["safe_one", "safe_two"]),
        ]
        warnings = check_self_cliche(entries[0], entries)
        assert len(warnings) == 0

    def test_detects_self_cliche(self):
        entries = [
            _make_entry(id="a", detect="pattern_a", compiled=re.compile("pattern_a"),
                        replacements=["has pattern_b inside", "clean"]),
            _make_entry(id="b", detect="pattern_b", compiled=re.compile("pattern_b"),
                        replacements=["safe"]),
        ]
        warnings = check_self_cliche(entries[0], entries)
        assert len(warnings) == 1
        assert warnings[0].replacement == "has pattern_b inside"
        assert warnings[0].matched_by == "b"


# ============================================================
# Diversity Check
# ============================================================

class TestDiversity:

    def test_edit_distance_identical(self):
        assert _edit_distance("abc", "abc") == 0

    def test_edit_distance_one_change(self):
        assert _edit_distance("abc", "axc") == 1

    def test_edit_distance_different_lengths(self):
        assert _edit_distance("abc", "abcd") == 1

    def test_edit_distance_empty(self):
        assert _edit_distance("", "abc") == 3
        assert _edit_distance("abc", "") == 3

    def test_normalized_distance(self):
        assert _normalized_distance("abc", "abc") == 0.0
        assert _normalized_distance("abc", "xyz") == 1.0

    def test_diverse_replacements_pass(self):
        entry = _make_entry(replacements=["completely different", "another approach"])
        result = check_diversity(entry)
        assert result.passed

    def test_similar_replacements_fail(self):
        entry = _make_entry(replacements=["the cat sat", "the cat sat down"])
        result = check_diversity(entry, threshold=0.5)
        # normalized distance is small since they share most chars
        assert result.min_distance < 0.5

    def test_single_replacement_passes(self):
        entry = _make_entry(replacements=["only one"])
        result = check_diversity(entry)
        assert result.passed


# ============================================================
# Full Entry Validation
# ============================================================

class TestValidateEntry:

    def test_good_entry_passes(self):
        entry = _make_entry()
        result = validate_entry(entry)
        assert result.status == "pass"

    def test_bad_entry_blocks(self):
        entry = _make_entry(test_cases=[])  # too few test cases
        result = validate_entry(entry)
        assert result.status == "block"


# ============================================================
# Full Dictionary Validation
# ============================================================

class TestValidateDictionary:

    def test_validates_full_dictionary(self):
        entries = [
            _make_entry(id="entry1"),
            _make_entry(id="entry2"),
        ]
        d = Dictionary(version="0.1.0", language="test", entries=entries)
        report = validate_dictionary(d)
        assert report.entries_total == 2
        assert report.entries_passed == 2
        assert report.entries_blocked == 0
