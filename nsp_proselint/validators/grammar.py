"""Type-specific grammar validation for dictionary entries."""

import re
from dataclasses import dataclass, field

from ..loader import Dictionary, PatternEntry, TestCase


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class EntryValidationResult:
    entry_id: str
    status: str  # "pass", "warn", "block"
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, check: CheckResult):
        self.checks.append(check)
        if not check.passed:
            if self.status != "block":
                self.status = "block" if "BLOCK" in check.detail else "warn"


@dataclass
class DictionaryValidationReport:
    dictionary: str
    version: str
    entries_total: int = 0
    entries_passed: int = 0
    entries_warned: int = 0
    entries_blocked: int = 0
    results: list[EntryValidationResult] = field(default_factory=list)


def check_regex_compile(entry: PatternEntry) -> CheckResult:
    """1.1: Verify regex compiles without error."""
    try:
        re.compile(entry.detect)
        return CheckResult("regex_compile", True)
    except re.error as e:
        return CheckResult("regex_compile", False, f"BLOCK: {e}")


def check_test_coverage(entry: PatternEntry) -> CheckResult:
    """1.2: Verify regex matches all test case inputs."""
    failures = []
    for tc in entry.test_cases:
        if not entry.compiled.search(tc.input):
            failures.append(tc.input)
    if failures:
        return CheckResult(
            "test_coverage", False,
            f"BLOCK: regex doesn't match {len(failures)} test case(s): {failures}"
        )
    total = len(entry.test_cases)
    return CheckResult("test_coverage", True, f"{total}/{total}")


def check_negative_cases(entry: PatternEntry) -> CheckResult:
    """1.3: Verify regex does NOT match negative cases."""
    false_positives = []
    for neg in entry.negative_cases:
        if entry.compiled.search(neg):
            false_positives.append(neg)
    if false_positives:
        return CheckResult(
            "negative_coverage", False,
            f"WARN: regex matches {len(false_positives)} negative case(s): {false_positives}"
        )
    total = len(entry.negative_cases)
    return CheckResult("negative_coverage", True, f"{total}/{total}")


def check_replacement_grammar(entry: PatternEntry) -> CheckResult:
    """1.4: Type-specific replacement grammar validation."""
    if entry.severity == "detect_only":
        return CheckResult("grammar_check", True, "detect_only, skipped")

    if entry.type == "full":
        return _check_full_grammar(entry)
    elif entry.type == "prefix":
        return _check_prefix_grammar(entry)
    elif entry.type == "modifier":
        return _check_modifier_grammar(entry)
    else:
        return CheckResult("grammar_check", False, f"BLOCK: unknown type '{entry.type}'")


def _check_full_grammar(entry: PatternEntry) -> CheckResult:
    """Type A: each replacement is a complete standalone expression."""
    failures = []
    for repl in entry.replacements:
        if len(repl) < 2:
            failures.append(f"'{repl}' too short (< 2 chars)")
    if failures:
        return CheckResult("grammar_check", False, f"BLOCK: {'; '.join(failures)}")
    return CheckResult("grammar_check", True)


def _check_prefix_grammar(entry: PatternEntry) -> CheckResult:
    """Type B: each replacement + each test suffix forms valid output."""
    failures = []
    combos_checked = 0
    for tc in entry.test_cases:
        if not tc.suffix:
            continue
        for repl in entry.replacements:
            result = repl + tc.suffix
            if result not in tc.valid_outputs:
                failures.append(f"'{repl}' + '{tc.suffix}' = '{result}' not in valid_outputs")
            combos_checked += 1
    if failures:
        return CheckResult("grammar_check", False, f"BLOCK: {'; '.join(failures)}")
    return CheckResult("grammar_check", True, f"{combos_checked}/{combos_checked} combinations")


def _check_modifier_grammar(entry: PatternEntry) -> CheckResult:
    """Type C: replacement in context preserves surrounding structure."""
    failures = []
    combos_checked = 0
    for tc in entry.test_cases:
        m = entry.compiled.search(tc.input)
        if not m:
            continue
        for repl in entry.replacements:
            result = tc.input[:m.start()] + repl + tc.input[m.end():]
            if result not in tc.valid_outputs:
                failures.append(f"'{repl}' in '{tc.input}' = '{result}' not in valid_outputs")
            combos_checked += 1
    if failures:
        return CheckResult("grammar_check", False, f"BLOCK: {'; '.join(failures)}")
    return CheckResult("grammar_check", True, f"{combos_checked}/{combos_checked} combinations")


def check_minimum_requirements(entry: PatternEntry) -> CheckResult:
    """1.7: Minimum test coverage and replacement count."""
    issues = []
    if len(entry.test_cases) < 2:
        issues.append(f"needs >= 2 test cases, has {len(entry.test_cases)}")
    if entry.severity == "replace" and len(entry.replacements) < 2:
        issues.append(f"needs >= 2 replacements, has {len(entry.replacements)}")
    if len(entry.negative_cases) < 1:
        issues.append("needs >= 1 negative case")
    if issues:
        return CheckResult("minimum_requirements", False, f"BLOCK: {'; '.join(issues)}")
    return CheckResult("minimum_requirements", True)


def validate_entry(entry: PatternEntry) -> EntryValidationResult:
    """Run all Phase 1 static validation checks on a single entry."""
    result = EntryValidationResult(entry_id=entry.id, status="pass")

    result.add(check_regex_compile(entry))
    result.add(check_test_coverage(entry))
    result.add(check_negative_cases(entry))
    result.add(check_replacement_grammar(entry))
    result.add(check_minimum_requirements(entry))

    return result


def validate_dictionary(dictionary: Dictionary) -> DictionaryValidationReport:
    """Run Phase 1 validation on an entire dictionary."""
    report = DictionaryValidationReport(
        dictionary=dictionary.language,
        version=dictionary.version,
        entries_total=len(dictionary.entries),
    )

    for entry in dictionary.entries:
        entry_result = validate_entry(entry)
        report.results.append(entry_result)

        if entry_result.status == "pass":
            report.entries_passed += 1
        elif entry_result.status == "warn":
            report.entries_warned += 1
        else:
            report.entries_blocked += 1

    return report
