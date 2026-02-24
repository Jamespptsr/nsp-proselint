# Validation Rules

**Version**: 0.1.0
**Date**: 2026-02-23

---

## 1. Validation Phases

```
Dictionary Entry Created
    |
    v
Phase 1: Static Validation (automated, at build time)
    |
    v
Phase 2: Corpus Validation (automated, periodic)
    |
    v
Phase 3: Human Review (manual, before release)
    |
    v
Phase 4: Runtime Monitoring (automated, in production)
```

## 2. Phase 1: Static Validation

Run on every dictionary entry before it can be merged.

### 1.1 Regex Compilation
```
Input:  entry.detect
Check:  re.compile(entry.detect) succeeds
Fail:   BLOCK — invalid regex cannot be used
```

### 1.2 Test Case Coverage
```
For each test_case in entry.test_cases:
  Check: re.search(entry.detect, test_case.input) matches
  Fail:  BLOCK — regex doesn't match its own test case
```

### 1.3 Negative Case Check
```
For each neg in entry.negative_cases:
  Check: re.search(entry.detect, neg) is None
  Fail:  WARN — regex has false positive on known negative
```

### 1.4 Replacement Grammar (Type-Specific)

**Type A (full)**:
```
For each replacement R:
  Check: len(R) >= 4 characters (not trivially short)
  Check: R does not end with a conjunction (e.g., 但是, 不过)
  Check: R forms a complete expression
```

**Type B (prefix)**:
```
For each replacement R, for each test_case T:
  suffix = T.suffix
  result = R + suffix
  Check: result appears in T.valid_outputs OR
         result reads as valid Chinese (manual tag)
  Fail:  BLOCK — replacement + suffix grammar broken
```

**Type C (modifier)**:
```
For each replacement R, for each test_case T:
  result = T.input.replace(regex_match, R)
  Check: result appears in T.valid_outputs OR
         subject and verb from original are preserved
  Fail:  BLOCK — modifier doesn't fit grammatical slot
```

### 1.5 Self-Cliche Check
```
For each replacement R in entry:
  For each OTHER_entry in dictionary:
    Check: re.search(OTHER_entry.detect, R) is None
    Fail:  WARN — replacement is itself a cliche
           (allowed with explicit override flag)
```

### 1.6 Diversity Check
```
For replacements [R1, R2, R3, ...]:
  For each pair (Ri, Rj):
    Check: edit_distance(Ri, Rj) / max(len(Ri), len(Rj)) > 0.3
    Fail:  WARN — replacements too similar to each other
```

### 1.7 Minimum Requirements
```
Check: len(entry.test_cases) >= 2
Check: len(entry.replacements) >= 2  (if severity == "replace")
Check: len(entry.negative_cases) >= 1
Fail:  BLOCK — insufficient test coverage
```

## 3. Phase 2: Corpus Validation

Run against a corpus of real LLM outputs (100+ passages per language).

### 2.1 Detection Rate
```
For each known cliche instance in corpus:
  Check: at least one pattern detects it
Report: total_detected / total_known_cliches (target: >= 80%)
```

### 2.2 False Positive Rate
```
For each detection hit:
  Manually classify: true_positive or false_positive
Report: false_positives / total_hits (target: <= 5%)
```

### 2.3 Replacement Naturalness
```
For N random replacement outputs:
  Human rates on 1-5 scale:
    1 = broken grammar / nonsensical
    2 = grammatically OK but meaning changed
    3 = OK but slightly awkward
    4 = natural, meaning preserved
    5 = excellent, reads better than original
Report: average score (target: >= 3.5)
```

### 2.4 Context Preservation
```
For each replacement:
  Check: subject from original clause appears in result
  Check: semantic intent (emotion/action/atmosphere) is preserved
  Fail:  WARN — context or meaning lost
```

## 4. Phase 3: Human Review

Before each dictionary release:

1. **Sample review**: For each entry, generate 5 random replacements using test case inputs. A human reviewer checks each for naturalness and semantic equivalence.

2. **Edge case review**: For each Type B (prefix) entry, test with uncommon suffixes (not just the test case suffixes) to find boundary failures.

3. **Cross-pattern review**: Check that no replacement text introduced by one pattern would trigger a different pattern (cascading replacement).

4. **Reading test**: Take a full passage, apply all replacements, read the result as prose. Flag anything that feels unnatural in context.

## 5. Phase 4: Runtime Monitoring

Metrics to track in production:

| Metric | What to Watch | Action |
|--------|---------------|--------|
| `hits_per_pattern` | Which patterns fire most often | Investigate if one pattern dominates (>30% of hits) |
| `replacement_rate` | What % of detected cliches get replaced | Low rate suggests many detect_only patterns |
| `cliche_density` | Cliches per 100 clauses, per model | Compare across models, track over time |
| `user_feedback` | If user reports a bad replacement | Log for dictionary improvement queue |

## 6. Validation Report Format

```yaml
report:
  dictionary: "zh_CN.yaml"
  version: "0.1.0"
  timestamp: "2026-02-23T22:00:00Z"
  entries_total: 27
  entries_passed: 24
  entries_warned: 2
  entries_blocked: 1

  results:
    - id: "emotion_flash"
      status: "pass"
      checks:
        regex_compile: pass
        test_coverage: pass (3/3)
        negative_coverage: pass (1/1)
        grammar_check: pass (9/9 combinations)
        self_cliche: pass
        diversity: pass (min_distance: 0.65)

    - id: "auto_action"
      status: "warn"
      checks:
        regex_compile: pass
        test_coverage: pass (2/2)
        negative_coverage: pass (1/1)
        grammar_check: pass
        self_cliche: warn
          detail: "replacement '本能地' partial match with new_pattern_xyz"
        diversity: pass

    - id: "broken_entry"
      status: "block"
      checks:
        regex_compile: pass
        test_coverage: fail
          detail: "test case '他心中涌起一股暖意' not matched by regex"
```

## 7. Automation Strategy

### What can be fully automated:
- Regex compilation test
- Test case matching
- Negative case checking
- Self-cliche cross-check
- Diversity score computation
- Report generation

### What needs human input:
- Naturalness rating (Phase 2.3)
- Edge case suffix testing (Phase 3.2)
- Full-passage reading test (Phase 3.4)

### What can be LLM-assisted:
- Grammar validation for Type B (prefix + suffix combinations)
- Generating additional test cases from existing patterns
- Suggesting new replacements for existing patterns
- Identifying potential false positives in corpus

LLM-assisted validation is optional enhancement, not a dependency. The core pipeline works with regex + human review alone.
