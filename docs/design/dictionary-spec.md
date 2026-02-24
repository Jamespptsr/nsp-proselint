# Dictionary Specification

**Version**: 0.1.0
**Date**: 2026-02-23

---

## 1. Entry Schema

Each dictionary is a YAML file containing a list of pattern entries:

```yaml
version: "0.1.0"
language: "zh_CN"
entries:
  - id: "emotion_flash"
    category: "facial_expression"
    type: "prefix"               # full | prefix | modifier
    severity: "replace"          # replace | detect_only
    detect: "眼[中底里神].*?闪过一[丝抹道缕]"
    suffix_type: "emotion_word"  # only for type: prefix
    replacements:
      - "目光中多了几分"
      - "眼里有了一点"
      - "带着几分"
    test_cases:
      - input: "眼中闪过一丝坚定"
        suffix: "坚定"
        valid_outputs:
          - "目光中多了几分坚定"
          - "眼里有了一点坚定"
          - "带着几分坚定"
      - input: "眼神里闪过一抹复杂"
        suffix: "复杂"
        valid_outputs:
          - "目光中多了几分复杂"
    negative_cases:
      - "他的眼睛闪闪发光"         # NOT a cliche, should not match
    notes: "Matches the stereotypical 'flash of emotion in eyes' pattern"
```

## 2. Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier, snake_case |
| `category` | string | Grouping category (see Section 3) |
| `type` | enum | `full`, `prefix`, or `modifier` |
| `severity` | enum | `replace` (has replacements) or `detect_only` (detection without replacement) |
| `detect` | string | Regex pattern (Python `re` compatible) |
| `replacements` | list[string] | Synonym alternatives. Empty list for `detect_only` |
| `test_cases` | list[object] | At least 2 test cases per entry |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `suffix_type` | string | For `prefix` type: grammatical category of remaining suffix |
| `negative_cases` | list[string] | Strings that should NOT match the regex |
| `notes` | string | Human-readable explanation |
| `source` | string | Where this pattern was first observed (model name, corpus) |

### Test Case Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `input` | string | Yes | Full clause containing the cliche |
| `suffix` | string | prefix type only | The semantic content after the regex match |
| `valid_outputs` | list[string] | Yes | Expected results after replacement |

## 3. Categories

Standard category taxonomy:

| Category | Description | Examples |
|----------|-------------|---------|
| `thinking_gesture` | Hand/finger movements indicating thought | Drumming fingers, stroking cup |
| `generic_posture` | Formulaic body positions | Arms crossed, hands in pockets |
| `generic_smile` | Stereotypical smile descriptions | Corner of mouth rises |
| `generic_brow` | Stereotypical brow movements | Brow furrows, eyebrow raises |
| `emotion_flash` | Flash of emotion in eyes | A glint of X appeared |
| `pupil_cliche` | Pupil contraction/dilation | Pupils contracted |
| `inner_feeling` | Vague internal sensation | A feeling welled up inside |
| `auto_action` | Unconscious/involuntary modifier | Unconsciously, instinctively |
| `poetic_filler` | Decorative but empty prose | As if telling a story |
| `vague_emotion` | Indescribable emotion hedge | An indescribable feeling |
| `frozen_air` | Air/atmosphere freezing | The air seemed to freeze |
| `spreading_silence` | Silence spreading description | Silence spread between them |
| `atmosphere_shift` | Atmosphere suddenly changing | The atmosphere became tense |
| `spine_chill` | Cold sensation on spine | A chill ran up the spine |
| `throat_bob` | Adam's apple movement | Adam's apple bobbed |
| `fist_clench` | Fist clenching | Clenched fists |
| `formulaic_structure` | Sentence-level patterns | Not X but Y, rather than X |

## 4. Type-Specific Replacement Rules

### Type `full` (Full-Consume)

**Definition**: The regex match covers the entire meaningful content of the clause.

**Replacement rule**: Each replacement must be a complete, standalone expression that can replace the entire match.

**Validation**:
```
For each replacement R:
  assert R is a grammatically complete expression
  assert R is NOT matched by any other pattern in the dictionary
  assert R conveys similar semantic weight (e.g., "atmosphere" -> "atmosphere")
```

**Example**:
```yaml
type: full
detect: "空气.*?(?:仿佛|似乎).*?(?:凝固|凝结)"
replacements:
  - "周围安静下来"         # complete expression
  - "谁都没有先开口"       # complete expression
```

### Type `prefix` (Prefix-Consume)

**Definition**: The regex matches the cliche prefix. Meaningful content (emotion/action word) follows the match and must be preserved by the replacement.

**Replacement rule**: Each replacement must syntactically accept the remaining suffix as its complement. The replacement is a grammatical prefix that connects to the semantic content after the match.

**Validation**:
```
For each replacement R, for each test suffix S:
  result = R + S
  assert result is grammatically valid Chinese/English
  assert result conveys the same meaning as original
  assert grammatical relationship between R and S is correct
    (e.g., "目光中多了几分" + "坚定" = valid attributive)
```

**Common suffix types and compatible prefix patterns**:

| suffix_type | Examples | Valid prefix endings |
|-------------|----------|---------------------|
| `emotion_word` | 坚定, 复杂, 悲伤 | ...多了几分, ...有了一点, ...带着 |
| `action_word` | 握紧, 后退 | ...地 (adverb ending) |
| `abstract_noun` | 感觉, 情绪 | ...的, ...种 |

**Critical anti-pattern**: The replacement must NOT be a complete sentence that doesn't need a suffix.
```
BAD:  "视线微微移开又回来" + "坚定" = broken grammar
GOOD: "目光中多了几分" + "坚定" = natural Chinese
```

### Type `modifier` (Modifier-Only)

**Definition**: The regex matches just a modifier word/phrase within a clause. All surrounding structure (subject, verb, object) is preserved.

**Replacement rule**: Each replacement must be a modifier of the same grammatical class (adverb->adverb, adjective->adjective) that fits the same syntactic slot.

**Validation**:
```
For each test case with input I and replacement R:
  result = I.replace(regex_match, R)
  assert result is grammatically valid
  assert subject and verb of original are preserved in result
  assert R fills same grammatical role as the matched text
```

**Example**:
```yaml
type: modifier
detect: "(?:不自觉|不由自主|下意识)地"
replacements:
  - "本能地"              # adverb -> adverb
  - "条件反射般"           # adverb equivalent
```

## 5. Dictionary Quality Metrics

A production-ready dictionary entry must pass:

| Metric | Threshold | Description |
|--------|-----------|-------------|
| `test_coverage` | >= 2 cases | At least 2 positive test cases per entry |
| `negative_coverage` | >= 1 case | At least 1 negative case (should NOT match) |
| `replacement_count` | >= 2 | At least 2 replacement options for diversity |
| `grammar_pass_rate` | 100% | All replacement + suffix combinations are grammatically valid |
| `self_cliche_check` | 0 hits | No replacement is itself matched by any dictionary pattern |
| `diversity_score` | >= 0.5 | Replacements are sufficiently different from each other (edit distance) |

## 6. Severity Levels

| Severity | Behavior | Use Case |
|----------|----------|----------|
| `replace` | Detect AND replace with synonym | Patterns with good replacement options |
| `detect_only` | Detect and report, but do NOT replace | Complex patterns (e.g., `不是X而是Y`) where safe replacement requires NLU |

`detect_only` entries are still valuable:
- nsp-analysis can report cliche density including these
- nsp-roleplay can log detection for quality metrics
- Future LLM-assisted replacement can handle these

## 7. File Naming Convention

```
dictionaries/
  zh_CN.yaml       # Simplified Chinese
  zh_TW.yaml       # Traditional Chinese (if needed, can inherit zh_CN with character conversion)
  en.yaml          # English
  ja.yaml          # Japanese (future)
  _schema.yaml     # Entry schema definition for validation
```
