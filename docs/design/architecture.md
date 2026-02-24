# nsp-proselint Architecture

**Version**: 0.1.0 (Design Phase)
**Date**: 2026-02-23
**Status**: Design document, not yet implemented

---

## 1. Problem Statement

Large Language Models produce text with recurring formulaic patterns ("cliches" / "八股"):

- Chinese: `眼中闪过一丝`, `空气仿佛凝固了`, `不自觉地握紧了拳头`
- English: `raised an eyebrow`, `let out a breath she didn't know she was holding`

These patterns are:
- **Model-universal**: All major LLMs produce them (Claude, GPT, Gemini, Deepseek)
- **Language-specific**: Chinese and English have different cliche sets
- **Context-independent**: They appear regardless of character, genre, or setting
- **Density-variable**: Some outputs have 0%, others have 40%+ cliche clauses

Current mitigation approaches all have significant drawbacks:
- **Prompt engineering** (blacklist in system prompt): Weak enforcement, LLMs don't reliably obey
- **Rejection + retry**: Causes model degradation (outputs get shorter/more generic)
- **Post-generation deletion**: Destroys sentence structure, loses subject attribution

## 2. Solution: Sub-match Synonym Replacement

Replace only the cliche portion of each clause with a semantically equivalent synonym, preserving all surrounding context (subjects, objects, punctuation).

```
Original:  他不自觉地后退了一步
              ^^^^^^^^ cliche match
Replace:   他本能地后退了一步
              ^^^^ synonym
```

Key insight: cliches exist at different granularity levels, requiring different replacement strategies.

## 3. Architecture Overview

```
nsp-proselint/
  nsp_proselint/
    __init__.py              # Public API: lint(), replace(), validate()
    linter.py                # Core engine: detect + replace
    loader.py                # Dictionary loader (YAML -> compiled patterns)
    validators/
      __init__.py
      grammar.py             # Type-specific grammar validation
      semantic.py            # Semantic equivalence checks
      self_check.py          # Verify replacements aren't themselves cliches
    dictionaries/
      zh_CN.yaml             # Chinese cliche dictionary
      en.yaml                # English cliche dictionary
      _schema.yaml           # Dictionary entry schema definition
  docs/
    design/
      architecture.md        # This file
      dictionary-spec.md     # Dictionary format specification
      validation-rules.md    # Validation rules per type
  tests/
    test_linter.py
    test_loader.py
    test_validators.py
    test_zh_CN.py            # Chinese dictionary quality tests
    test_en.py               # English dictionary quality tests
  setup.py
```

## 4. Core API

```python
from nsp_proselint import ProseLinter

# Initialize with language-specific dictionary
linter = ProseLinter(lang="zh_CN")

# Mode 1: Detect cliches (for analysis/reporting)
results = linter.lint(text)
# Returns: [LintResult(clause, pattern_id, category, match_span, severity)]

# Mode 2: Replace cliches with synonyms
cleaned = linter.replace(text)
# Returns: replaced text with cliches swapped for synonyms

# Mode 3: Replace with diff tracking (for UI display)
cleaned, diffs = linter.replace_with_diff(text)
# Returns: (replaced_text, [Diff(original, replacement, span, pattern_id)])

# Mode 4: Validate a dictionary entry
from nsp_proselint.validators import validate_entry
report = validate_entry(entry, test_corpus)
# Returns: ValidationReport with pass/fail per test case
```

## 5. Integration Points

### nsp-roleplay (post-generation filter)
```python
# In context_injector.py or routes.py, after LLM response:
from nsp_proselint import ProseLinter
linter = ProseLinter(lang="zh_CN")
cleaned_response = linter.replace(raw_llm_response)
```

### nsp-analysis (manuscript cliche audit)
```python
# In analysis pipeline, per-chapter quality check:
from nsp_proselint import ProseLinter
linter = ProseLinter(lang="zh_CN")
for chapter in chapters:
    results = linter.lint(chapter.text)
    cliche_density = len(results) / total_clauses
    # Report: which chapters have high cliche density
    # Report: which patterns are most frequent
```

### nsp-analysis (AI continuation quality)
```python
# When AI generates continuation text for manuscripts:
cleaned = linter.replace(ai_continuation)
```

### nsp-edu (writing quality feedback)
```python
# In student writing analysis:
results = linter.lint(student_text)
# Provide feedback: "Your writing uses 3 common formulaic expressions..."
```

## 6. Pattern Replacement Types

Three fundamentally different replacement strategies based on regex match scope:

### Type A: Full-Consume (全量替换)

Regex matches the entire meaningful content of the clause. Replacement is an independent alternative expression.

```yaml
type: full
detect: "空气.*?(?:仿佛|似乎).*?(?:凝固|凝结|静止)"
replacements:
  - "周围安静下来"
  - "谁都没有先开口"
```

Mechanism: `clause.replace(regex, pick(replacements))`
The replacement stands alone; nothing from the original clause is reused.

### Type B: Prefix-Consume (前缀替换)

Regex matches the cliche prefix structure. The meaningful semantic content (emotion word, action word) follows the match and must be preserved.

```yaml
type: prefix
detect: "眼[中底里神].*?闪过一[丝抹道缕]"
suffix_type: emotion_word    # grammatical type of what follows
replacements:
  - "目光中多了几分"           # + 坚定 -> "目光中多了几分坚定" OK
  - "眼里有了一点"            # + 坚定 -> "眼里有了一点坚定" OK
```

Mechanism: `clause.replace(regex, pick(replacements))`
The replacement must syntactically accept the remaining suffix as its complement.

**Critical rule**: Every replacement must be tested with representative suffixes to verify grammatical compatibility.

### Type C: Modifier-Only (修饰语替换)

Regex matches just a modifier word/phrase within a larger clause. Subject, verb, and object are all preserved.

```yaml
type: modifier
detect: "(?:不自觉|不由自主|下意识)地"
replacements:
  - "本能地"
  - "条件反射般"
```

Mechanism: `clause.replace(regex, pick(replacements))`
The replacement is a same-position modifier; surrounding structure is untouched.

## 7. Validation Pipeline

### Phase 1: Dictionary Entry Validation (at dictionary build time)

For each entry:

1. **Regex compilation test**: Pattern compiles without error
2. **Coverage test**: Regex matches all provided test_cases inputs
3. **False positive test**: Regex does NOT match provided negative_cases
4. **Type-specific grammar test**:
   - Type A: Each replacement is a complete, standalone expression
   - Type B: Each replacement + each test suffix forms valid grammar
   - Type C: Each replacement fills the same grammatical slot
5. **Self-cliche test**: No replacement is itself matched by any pattern in the dictionary
6. **Diversity test**: Replacements are sufficiently different from each other

### Phase 2: Corpus Validation (periodic quality check)

Run dictionary against a corpus of real LLM outputs:

1. **Hit rate**: What percentage of cliche instances are detected?
2. **False positive rate**: What percentage of hits are actually not cliches?
3. **Replacement quality**: Sample N replaced outputs, manually rate naturalness
4. **Regression test**: Compare against golden test set of input->expected_output pairs

### Phase 3: Runtime Monitoring (in production)

Track per-session:
- Clauses processed / cliches detected / replaced
- Pattern hit frequency (identify over-triggering patterns)
- User feedback (if replacement sounds wrong, log for dictionary improvement)

## 8. Dictionary Lifecycle

```
Collect cliche instances from LLM outputs
    |
    v
Classify by Type (A/B/C) + write regex
    |
    v
Write replacements following type-specific rules
    |
    v
Write test_cases (positive + negative + suffix tests)
    |
    v
Run automated validation (Phase 1)
    |
    v
Fix failures, iterate
    |
    v
Human review: 5 random replacements per entry
    |
    v
Merge into dictionary YAML
    |
    v
Periodic corpus validation (Phase 2)
    |
    v
Runtime monitoring (Phase 3)
```

## 9. Design Decisions

### Why regex, not LLM?
- **Deterministic**: Same input always produces same detection
- **Fast**: <1ms per clause, no API call needed
- **Auditable**: Every pattern is explicit and reviewable
- **Offline**: Works without network access

LLM-based detection could catch more subtle cliches but adds latency, cost, and non-determinism. Regex handles the 80% of cliches that ARE formulaic patterns. The remaining 20% (semantic-level cliches like "not X but Y" with meaningful content) are marked as detection-only (no replacement).

### Why per-clause, not per-sentence?
Chinese text uses clause-level punctuation (，；) extensively. A sentence may contain 5+ clauses, only 1-2 of which are cliche. Per-clause processing allows surgical replacement without touching clean clauses.

### Why YAML dictionaries?
- Human-readable and editable
- Supports comments for rationale
- Easy to version control
- YAML is already the NSP universal interchange format

## 10. Scope Boundaries

**In scope**:
- Detection of formulaic patterns via regex
- Sub-match synonym replacement preserving context
- Dictionary format specification and validation
- Chinese (zh_CN) and English (en) dictionaries
- Integration API for NSP ecosystem packages

**Out of scope (future)**:
- LLM-assisted cliche detection (semantic-level)
- Style transfer (changing voice/tone, not just removing cliches)
- Grammar correction (fixing broken sentences)
- Real-time streaming replacement (current: batch text input)
- Dictionary crowd-sourcing platform
