/**
 * Text display and replacement popup.
 *
 * Renders paragraphs with highlighted hit spans,
 * positions popup on span click, handles replacement/skip/revert.
 */

const Editor = (() => {
    const _els = {};
    let _onReplace = null;   // callback(hitGlobalIndex, replacementText)
    let _onSkip = null;      // callback(hitGlobalIndex)
    let _onRevert = null;    // callback(hitGlobalIndex)
    let _activeHitIndex = null;

    function init({ onReplace, onSkip, onRevert }) {
        _onReplace = onReplace;
        _onSkip = onSkip;
        _onRevert = onRevert;

        _els.display = document.getElementById("text-display");
        _els.popup = document.getElementById("replace-popup");
        _els.popupCategory = document.getElementById("popup-category");
        _els.popupMatch = document.getElementById("popup-match");
        _els.popupReplacements = document.getElementById("popup-replacements");
        _els.popupCustomInput = document.getElementById("popup-custom-input");
        _els.popupCustomApply = document.getElementById("popup-custom-apply");
        _els.popupSkip = document.getElementById("popup-skip");
        _els.popupRevert = document.getElementById("popup-revert");

        // Popup button handlers
        _els.popupSkip.addEventListener("click", () => {
            if (_activeHitIndex !== null && _onSkip) {
                _onSkip(_activeHitIndex);
            }
        });

        _els.popupRevert.addEventListener("click", () => {
            if (_activeHitIndex !== null && _onRevert) {
                _onRevert(_activeHitIndex);
            }
        });

        _els.popupCustomApply.addEventListener("click", () => {
            const text = _els.popupCustomInput.value.trim();
            if (text && _activeHitIndex !== null && _onReplace) {
                _onReplace(_activeHitIndex, text);
            }
        });

        _els.popupCustomInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                _els.popupCustomApply.click();
            }
            if (e.key === "Escape") {
                hidePopup();
            }
        });

        // Close popup on outside click
        document.addEventListener("click", (e) => {
            if (_els.popup.style.display !== "none" &&
                !_els.popup.contains(e.target) &&
                !e.target.classList.contains("hit-span")) {
                hidePopup();
            }
        });

        // Double-click to edit paragraph
        _els.display.addEventListener("dblclick", (e) => {
            const paraEl = e.target.closest(".para");
            if (paraEl && !paraEl.querySelector(".para-edit-area")) {
                const paraIndex = parseInt(paraEl.dataset.paraIndex, 10);
                if (!isNaN(paraIndex)) {
                    enterEditMode(paraEl, paraIndex);
                }
            }
        });
    }

    /**
     * Render file content with highlighted hit spans.
     * For docx files, applies heading styles from nodeMap.
     * @param {Object} file - App.state file object
     */
    function renderFile(file) {
        hidePopup();
        _els.display.innerHTML = "";

        if (!file || !file.paragraphs) {
            _els.display.innerHTML = '<div class="empty-state"><p>No content</p></div>';
            return;
        }

        for (let pi = 0; pi < file.paragraphs.length; pi++) {
            const para = file.paragraphs[pi];
            const div = document.createElement("div");

            if (!para.trim()) {
                div.className = "para empty-para";
                div.innerHTML = "&nbsp;";
            } else {
                // Detect heading level from nodeMap (docx files only)
                let headingClass = "";
                if (file.docxData && file.docxData.nodeMap[pi]) {
                    const hl = file.docxData.nodeMap[pi].headingLevel;
                    if (hl >= 1 && hl <= 6) {
                        headingClass = " docx-h" + hl;
                    }
                }
                div.className = "para" + headingClass;
                div.innerHTML = _buildParaHTML(file, pi);
            }

            div.dataset.paraIndex = pi;
            _els.display.appendChild(div);
        }

        _attachSpanListeners();
    }

    /**
     * Build HTML for one paragraph with hit spans inserted.
     */
    function _buildParaHTML(file, paraIndex) {
        const text = file.paragraphs[paraIndex];
        // Gather hits for this paragraph, sorted by start offset
        const paraHits = [];
        for (let gi = 0; gi < file.hits.length; gi++) {
            const hit = file.hits[gi];
            if (hit.paraIndex === paraIndex) {
                paraHits.push({ ...hit, globalIndex: gi });
            }
        }

        if (paraHits.length === 0) {
            return _escapeHTML(text);
        }

        // Sort by start position
        paraHits.sort((a, b) => a.start - b.start);

        // Build HTML by interleaving text and spans
        let html = "";
        let cursor = 0;

        for (const hit of paraHits) {
            const replacement = file.replacements.get(hit.globalIndex);
            const isReplaced = replacement !== undefined && replacement !== null;
            const isSkipped = file.skipped.has(hit.globalIndex);
            const isDetectOnly = hit.severity === "detect_only";

            // Text before this hit
            if (hit.start > cursor) {
                html += _escapeHTML(text.substring(cursor, hit.start));
            }

            // Determine span class
            let cls = "hit-span";
            if (isReplaced) cls += " replaced";
            else if (isSkipped) cls += " skipped";
            else if (isDetectOnly) cls += " detect-only";

            // Display text: show replacement if replaced, else original match
            const displayText = isReplaced ? replacement : hit.matchText;

            html += `<span class="${cls}" data-hit-index="${hit.globalIndex}" title="${_escapeAttr(hit.entryId)}">${_escapeHTML(displayText)}</span>`;
            cursor = hit.end;
        }

        // Remaining text after last hit
        if (cursor < text.length) {
            html += _escapeHTML(text.substring(cursor));
        }

        return html;
    }

    /**
     * Attach click listeners to all .hit-span elements.
     */
    function _attachSpanListeners() {
        const spans = _els.display.querySelectorAll(".hit-span");
        spans.forEach(span => {
            span.addEventListener("click", (e) => {
                e.stopPropagation();
                const gi = parseInt(span.dataset.hitIndex, 10);
                showPopup(gi, span);
            });
        });
    }

    /**
     * Show replacement popup positioned below the span.
     */
    function showPopup(hitGlobalIndex, spanEl) {
        const file = App.getActiveFile();
        if (!file) return;

        const hit = file.hits[hitGlobalIndex];
        if (!hit) return;

        // Remove previous active
        _els.display.querySelectorAll(".hit-span.active").forEach(s => s.classList.remove("active"));
        spanEl.classList.add("active");
        _activeHitIndex = hitGlobalIndex;

        // Fill popup content
        _els.popupCategory.textContent = hit.category;
        _els.popupMatch.textContent = `"${hit.matchText}"`;

        // Replacement chips
        _els.popupReplacements.innerHTML = "";
        if (hit.replacements && hit.replacements.length > 0) {
            hit.replacements.forEach(repl => {
                const chip = document.createElement("span");
                chip.className = "replacement-chip";
                chip.textContent = repl;
                chip.addEventListener("click", () => {
                    if (_onReplace) _onReplace(hitGlobalIndex, repl);
                });
                _els.popupReplacements.appendChild(chip);
            });
        } else {
            _els.popupReplacements.innerHTML = '<span style="color:var(--text-meta);font-size:11px;">No suggestions (detect only)</span>';
        }

        // Show/hide revert button
        const isReplaced = file.replacements.has(hitGlobalIndex);
        _els.popupRevert.style.display = isReplaced ? "" : "none";
        _els.popupSkip.style.display = isReplaced ? "none" : "";

        // Clear custom input
        _els.popupCustomInput.value = "";

        // Position popup below the span
        const spanRect = spanEl.getBoundingClientRect();
        const containerRect = _els.display.closest(".center-panel").getBoundingClientRect();
        let top = spanRect.bottom - containerRect.top + 4;
        let left = spanRect.left - containerRect.left;

        // Keep popup within bounds
        const popupWidth = 340;
        if (left + popupWidth > containerRect.width) {
            left = containerRect.width - popupWidth - 8;
        }
        if (left < 8) left = 8;

        _els.popup.style.top = top + "px";
        _els.popup.style.left = left + "px";
        _els.popup.style.display = "";

        // Also highlight in hit list
        App.highlightHitInList(hitGlobalIndex);
    }

    function hidePopup() {
        _els.popup.style.display = "none";
        _activeHitIndex = null;
        _els.display.querySelectorAll(".hit-span.active").forEach(s => s.classList.remove("active"));
    }

    /**
     * Scroll to a specific hit in the text display.
     */
    function scrollToHit(hitGlobalIndex) {
        const span = _els.display.querySelector(`[data-hit-index="${hitGlobalIndex}"]`);
        if (span) {
            span.scrollIntoView({ behavior: "smooth", block: "center" });
            // Brief flash effect
            span.classList.add("active");
            setTimeout(() => {
                if (_activeHitIndex !== hitGlobalIndex) {
                    span.classList.remove("active");
                }
            }, 1500);
        }
    }

    /**
     * Re-render a single paragraph (after replacement or edit).
     */
    function rerenderParagraph(file, paraIndex) {
        const paraEl = _els.display.querySelector(`[data-para-index="${paraIndex}"]`);
        if (!paraEl) return;

        const text = file.paragraphs[paraIndex];
        if (!text.trim()) {
            paraEl.className = "para empty-para";
            paraEl.innerHTML = "&nbsp;";
        } else {
            let headingClass = "";
            if (file.docxData && file.docxData.nodeMap[paraIndex]) {
                const hl = file.docxData.nodeMap[paraIndex].headingLevel;
                if (hl >= 1 && hl <= 6) {
                    headingClass = " docx-h" + hl;
                }
            }
            paraEl.className = "para" + headingClass;
            paraEl.innerHTML = _buildParaHTML(file, paraIndex);
        }

        // Re-attach listeners for this paragraph
        paraEl.querySelectorAll(".hit-span").forEach(span => {
            span.addEventListener("click", (e) => {
                e.stopPropagation();
                const gi = parseInt(span.dataset.hitIndex, 10);
                showPopup(gi, span);
            });
        });
    }

    /**
     * Enter inline edit mode for a paragraph.
     */
    function enterEditMode(paraEl, paraIndex) {
        hidePopup();
        const file = App.getActiveFile();
        if (!file) return;

        // Get modified text for this paragraph
        const text = App.getModifiedParagraph(paraIndex);

        const textarea = document.createElement("textarea");
        textarea.className = "para-edit-area";
        textarea.value = text;
        textarea.rows = Math.max(2, Math.ceil(text.length / 60));

        paraEl.innerHTML = "";
        paraEl.appendChild(textarea);
        textarea.focus();

        const exitEdit = () => {
            const newText = textarea.value;
            if (newText !== file.paragraphs[paraIndex]) {
                // Text was manually edited: update paragraph and re-scan
                App.updateParagraph(paraIndex, newText);
            } else {
                // No change, just re-render
                rerenderParagraph(file, paraIndex);
            }
        };

        textarea.addEventListener("blur", exitEdit);
        textarea.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                textarea.removeEventListener("blur", exitEdit);
                rerenderParagraph(file, paraIndex);
            }
        });
    }

    function showEmptyState() {
        _els.display.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="#808080" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M28 6H12a2 2 0 00-2 2v30a2 2 0 002 2h24a2 2 0 002-2V16L28 6z"/>
                        <path d="M28 6v10h10M16 24h16M16 30h10"/>
                    </svg>
                </div>
                <p>Drop files here or click Import</p>
                <p class="empty-hint">Supports .txt, .md, .docx</p>
            </div>`;
    }

    function _escapeHTML(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function _escapeAttr(str) {
        return str.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }

    return {
        init,
        renderFile,
        rerenderParagraph,
        showPopup,
        hidePopup,
        scrollToHit,
        showEmptyState,
    };
})();
