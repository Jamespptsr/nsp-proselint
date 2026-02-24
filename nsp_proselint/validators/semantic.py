"""Semantic validation: diversity check for replacements."""

from dataclasses import dataclass

from ..loader import PatternEntry


@dataclass
class DiversityResult:
    entry_id: str
    min_distance: float
    passed: bool
    pair: tuple[str, str] = ("", "")  # most similar pair


def _edit_distance(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    m, n = len(a), len(b)
    if m == 0:
        return n
    if n == 0:
        return m

    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp

    return dp[n]


def _normalized_distance(a: str, b: str) -> float:
    """Edit distance normalized by max length. Returns 0.0 (identical) to 1.0 (totally different)."""
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 0.0
    return _edit_distance(a, b) / max_len


def check_diversity(entry: PatternEntry, threshold: float = 0.3) -> DiversityResult:
    """Check that replacements are sufficiently different from each other.

    Uses normalized edit distance. Threshold default 0.3 per validation-rules.md.
    """
    if len(entry.replacements) < 2:
        return DiversityResult(
            entry_id=entry.id,
            min_distance=1.0,
            passed=True,
        )

    min_dist = 1.0
    min_pair = ("", "")

    for i in range(len(entry.replacements)):
        for j in range(i + 1, len(entry.replacements)):
            a, b = entry.replacements[i], entry.replacements[j]
            dist = _normalized_distance(a, b)
            if dist < min_dist:
                min_dist = dist
                min_pair = (a, b)

    return DiversityResult(
        entry_id=entry.id,
        min_distance=round(min_dist, 3),
        passed=min_dist >= threshold,
        pair=min_pair,
    )
