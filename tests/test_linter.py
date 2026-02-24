"""Tests for the core linter engine."""

import re
import pytest

from nsp_proselint.linter import ProseLinter, LintHit, Diff, _split_clauses
from nsp_proselint.loader import DictionaryLoader, Dictionary, PatternEntry, TestCase


# ============================================================
# Clause Splitting
# ============================================================

class TestClauseSplitting:

    def test_chinese_comma(self):
        result = _split_clauses("他走了，她留下了。")
        assert result == ["他走了，", "她留下了。"]

    def test_chinese_period(self):
        result = _split_clauses("天黑了。")
        assert result == ["天黑了。"]

    def test_chinese_multiple(self):
        result = _split_clauses("第一，第二，第三。")
        assert result == ["第一，", "第二，", "第三。"]

    def test_english_comma(self):
        result = _split_clauses("He walked, she stayed.")
        assert result == ["He walked,", " she stayed."]

    def test_english_period(self):
        result = _split_clauses("First sentence. Second sentence.")
        assert result == ["First sentence.", " Second sentence."]

    def test_chinese_semicolon(self):
        result = _split_clauses("前者如此；后者亦然。")
        assert result == ["前者如此；", "后者亦然。"]

    def test_no_punctuation(self):
        result = _split_clauses("没有标点符号")
        assert result == ["没有标点符号"]

    def test_empty_string(self):
        result = _split_clauses("")
        assert result == [""]

    def test_chinese_enumeration_comma(self):
        result = _split_clauses("苹果、橘子、香蕉。")
        assert result == ["苹果、", "橘子、", "香蕉。"]


# ============================================================
# Lint Detection
# ============================================================

class TestLintDetection:

    @pytest.fixture
    def zh_linter(self):
        return ProseLinter(lang="zh_CN")

    @pytest.fixture
    def en_linter(self):
        return ProseLinter(lang="en")

    def test_detects_chinese_cliche(self, zh_linter):
        text = "他的嘴角微微上扬。"
        hits = zh_linter.lint(text)
        assert len(hits) == 1
        assert hits[0].pattern_id == "generic_smile"
        assert hits[0].category == "generic_smile"

    def test_detects_english_cliche(self, en_linter):
        text = "He raised an eyebrow."
        hits = en_linter.lint(text)
        assert len(hits) == 1
        assert hits[0].pattern_id == "en_raised_eyebrow"

    def test_no_false_positive(self, zh_linter):
        text = "她拿起杯子喝了一口水。"
        hits = zh_linter.lint(text)
        assert len(hits) == 0

    def test_multiple_cliches_in_text(self, zh_linter):
        text = "嘴角微微上扬，眼中闪过一丝坚定。"
        hits = zh_linter.lint(text)
        assert len(hits) == 2
        ids = [h.pattern_id for h in hits]
        assert "generic_smile" in ids
        assert "emotion_flash" in ids

    def test_first_match_per_clause(self, zh_linter):
        # If a clause matches two patterns, only first should fire
        text = "攥紧了拳头。"
        hits = zh_linter.lint(text)
        assert len(hits) == 1

    def test_match_text_captured(self, zh_linter):
        text = "攥紧了拳头。"
        hits = zh_linter.lint(text)
        assert "攥紧了拳头" in hits[0].match_text

    def test_multiline_text(self, zh_linter):
        text = "嘴角微微上扬。\n\n攥紧了拳头。"
        hits = zh_linter.lint(text)
        assert len(hits) == 2

    def test_modifier_detected(self, zh_linter):
        text = "他不自觉地后退了一步。"
        hits = zh_linter.lint(text)
        assert len(hits) == 1
        assert hits[0].pattern_id == "auto_action"
        assert hits[0].match_text == "不自觉地"


# ============================================================
# Replace
# ============================================================

class TestReplace:

    @pytest.fixture
    def zh_linter(self):
        return ProseLinter(lang="zh_CN")

    def test_replace_returns_string(self, zh_linter):
        text = "嘴角微微上扬。"
        result = zh_linter.replace(text)
        assert isinstance(result, str)
        assert result != text  # should be changed

    def test_replace_preserves_non_cliche(self, zh_linter):
        text = "今天天气很好。"
        result = zh_linter.replace(text)
        assert result == text

    def test_replace_preserves_context(self, zh_linter):
        text = "他不自觉地后退了一步。"
        result = zh_linter.replace(text)
        # Subject "他" and action "后退了一步" should be preserved
        assert "后退了一步" in result
        assert result.startswith("他")
        assert "不自觉地" not in result

    def test_replace_with_diff_tracks_changes(self, zh_linter):
        text = "攥紧了拳头。"
        result, diffs = zh_linter.replace_with_diff(text)
        assert len(diffs) == 1
        assert diffs[0].pattern_id == "fist_clench"
        assert "攥紧了拳头" in diffs[0].original
        assert diffs[0].replacement in [
            "指甲掐进了掌心",
            "手指收紧了",
            "手背上青筋凸起",
            "十指扣在了一起",
            "两手攥成了铁锤",
        ]

    def test_replace_multiline(self, zh_linter):
        text = "嘴角微微上扬。\n\n他说了句话。"
        result = zh_linter.replace(text)
        lines = result.split("\n")
        assert len(lines) == 3
        assert lines[2] == "他说了句话。"  # non-cliche preserved

    def test_prefix_type_preserves_suffix(self, zh_linter):
        text = "眼中闪过一丝坚定。"
        result = zh_linter.replace(text)
        # Suffix "坚定" must be preserved
        assert "坚定" in result
        # Original prefix must be gone
        assert "闪过一丝" not in result


# ============================================================
# Custom Dictionary
# ============================================================

class TestCustomDictionary:

    def test_load_custom_dict(self):
        entry = PatternEntry(
            id="test_pattern",
            category="test",
            type="full",
            severity="replace",
            detect="hello world",
            compiled=re.compile("hello world"),
            replacements=["greetings earth"],
            test_cases=[],
        )
        d = Dictionary(version="0.1.0", language="test", entries=[entry])
        linter = ProseLinter(dictionary=d)
        assert linter.language == "test"

        result = linter.replace("say hello world please")
        assert result == "say greetings earth please"

    def test_detect_only_not_replaced(self):
        entry = PatternEntry(
            id="detect_only",
            category="test",
            type="full",
            severity="detect_only",
            detect="bad phrase",
            compiled=re.compile("bad phrase"),
            replacements=[],
            test_cases=[],
        )
        d = Dictionary(version="0.1.0", language="test", entries=[entry])
        linter = ProseLinter(dictionary=d)

        hits = linter.lint("this is a bad phrase here")
        assert len(hits) == 1

        result = linter.replace("this is a bad phrase here")
        assert result == "this is a bad phrase here"  # unchanged


# ============================================================
# Attributive Context Guard
# ============================================================

class TestAttributiveGuard:

    @pytest.fixture
    def zh_linter(self):
        return ProseLinter(lang="zh_CN")

    def test_attributive_skipped_with_enumeration(self, zh_linter):
        """Match ending with 的 before enumeration comma (parallel modifiers) should be skipped."""
        # User's actual case: 嘴角勾起一个极其细微的、近乎残忍的弧度
        # Clause split at 、 gives: "嘴角勾起一个极其细微的、"
        # Regex matches "嘴角勾起一个极其细微的" (ends with 的)
        text = "嘴角勾起一个极其细微的、近乎残忍的弧度。"
        hits = zh_linter.lint(text)
        smile_hits = [h for h in hits if h.category == "generic_smile"]
        assert len(smile_hits) == 0

    def test_non_attributive_detected(self, zh_linter):
        """Normal match (not ending with 的) should still be detected."""
        text = "嘴角微微上扬。"
        hits = zh_linter.lint(text)
        smile_hits = [h for h in hits if h.category == "generic_smile"]
        assert len(smile_hits) == 1

    def test_attributive_not_replaced(self, zh_linter):
        """Attributive match should not be replaced."""
        text = "嘴角勾起一个极其细微的、近乎残忍的弧度。"
        result = zh_linter.replace(text)
        assert result == text  # unchanged

    def test_normal_match_still_replaced(self, zh_linter):
        """Non-attributive match should still be replaced."""
        text = "嘴角微微上扬。"
        result = zh_linter.replace(text)
        assert result != text  # should be changed
