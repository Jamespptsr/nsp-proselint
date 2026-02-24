/**
 * Core linter engine (JS port of nsp_proselint/linter.py).
 *
 * Loads dictionary JSON, compiles regex strings to RegExp,
 * splits text into clauses, detects cliche patterns with
 * per-clause first-match logic.
 */

const Linter = (() => {
    // Compiled dictionaries: [{id, category, type, severity, detect, regex, replacements, suffix_type?}]
    let _dictionaries = [];

    // Split after Chinese/English clause-ending punctuation.
    // Keeps delimiter attached to preceding clause.
    const CLAUSE_SPLIT_RE = /(?<=[，。！？；、.!?;,])/;

    function splitClauses(text) {
        const parts = text.split(CLAUSE_SPLIT_RE);
        // Filter trailing empty string
        if (parts.length > 0 && parts[parts.length - 1] === "") {
            parts.pop();
        }
        return parts.length > 0 ? parts : [""];
    }

    /**
     * Load and compile a dictionary from JSON array.
     * @param {Array} entries - Raw entries from JSON
     * @returns {Array} Compiled entries with regex property
     */
    function compileDictionary(entries) {
        return entries.map(e => ({
            ...e,
            regex: new RegExp(e.detect),
        }));
    }

    /**
     * Load dictionaries from JSON URLs.
     * @param {string[]} urls - Array of JSON file URLs
     */
    async function loadDictionaries(urls) {
        _dictionaries = [];
        const results = await Promise.all(
            urls.map(url => fetch(url).then(r => r.json()))
        );
        for (const entries of results) {
            _dictionaries.push(...compileDictionary(entries));
        }
        return _dictionaries.length;
    }

    /**
     * Get loaded dictionaries.
     */
    function getDictionaries() {
        return _dictionaries;
    }

    /**
     * Lint a single paragraph, returning hits with paragraph-relative offsets.
     *
     * @param {string} para - One paragraph of text
     * @returns {Array} hits: [{entryId, category, type, severity, matchText,
     *                          start, end, replacements, suffixType, clauseIndex}]
     */
    function lintParagraph(para) {
        if (!para.trim()) return [];

        const hits = [];
        const clauses = splitClauses(para);
        let offset = 0; // cumulative offset for paragraph-relative positions

        for (let ci = 0; ci < clauses.length; ci++) {
            const clause = clauses[ci];
            if (!clause.trim()) {
                offset += clause.length;
                continue;
            }

            for (const entry of _dictionaries) {
                const m = entry.regex.exec(clause);
                if (m) {
                    // Skip if match ends with "的" followed by non-punctuation
                    // (attributive structure like "细微的弧度" — replacement would break syntax)
                    if (_isAttributiveContext(m[0])) {
                        continue;
                    }

                    hits.push({
                        entryId: entry.id,
                        category: entry.category,
                        type: entry.type,
                        severity: entry.severity,
                        matchText: m[0],
                        start: offset + m.index,
                        end: offset + m.index + m[0].length,
                        replacements: entry.replacements || [],
                        suffixType: entry.suffix_type || null,
                        clauseIndex: ci,
                    });
                    break; // first match per clause
                }
            }
            offset += clause.length;
        }

        return hits;
    }

    /**
     * Lint entire text (multiple paragraphs).
     * Returns array of {paraIndex, hits[]}, one per non-empty paragraph.
     */
    function lintText(paragraphs) {
        const results = [];
        for (let pi = 0; pi < paragraphs.length; pi++) {
            const hits = lintParagraph(paragraphs[pi]);
            if (hits.length > 0) {
                results.push({ paraIndex: pi, hits });
            }
        }
        return results;
    }

    /**
     * Check if a match is in attributive context: ends with "的".
     * When a greedy regex tail consumes into a modifier structure
     * (e.g. "极其细微的弧度", "极其细微的、"), a full replacement
     * would break sentence structure. Skip these hits.
     */
    function _isAttributiveContext(matchText) {
        return matchText.endsWith("的");
    }

    return {
        splitClauses,
        compileDictionary,
        loadDictionaries,
        getDictionaries,
        lintParagraph,
        lintText,
    };
})();
