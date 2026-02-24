/**
 * DOCX handling: surgical patching + fallback generation.
 *
 * DocxPatcher: patches <w:t> text nodes in the original XML, preserving
 * all formatting, styles, images, etc. Only the replaced text changes.
 *
 * DocxWriter: fallback for generating new .docx from plain text paragraphs
 * (used when no docxData is available).
 */

const DocxPatcher = (() => {

    /**
     * Apply all replacements to the docx XML and export as new .docx file.
     * Only modifies <w:t> text content — everything else is untouched.
     *
     * @param {Object} file - App state file object with docxData
     * @param {string} filename - Output filename
     */
    async function patchAndExport(file, filename) {
        const { zip, xmlDoc, nodeMap } = file.docxData;

        // Collect all replacements grouped by paragraph
        const paraReplacements = _groupReplacementsByParagraph(file);

        // Apply each replacement to the XML DOM
        for (const [paraIndex, repls] of paraReplacements) {
            const paraMap = nodeMap[paraIndex];
            if (!paraMap) continue;

            // Sort by start offset descending (apply from end to preserve offsets)
            repls.sort((a, b) => b.start - a.start);

            for (const repl of repls) {
                _applyReplacement(paraMap.nodes, repl.start, repl.end, repl.text);
            }
        }

        // Serialize the modified XML back to string
        const serializer = new XMLSerializer();
        const newXmlString = serializer.serializeToString(xmlDoc);

        // Write back into the ZIP
        zip.file("word/document.xml", newXmlString);

        // Generate and download the new .docx
        const blob = await zip.generateAsync({
            type: "blob",
            mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            compression: "DEFLATE",
            compressionOptions: { level: 6 },
        });

        Files._download(blob, filename);
    }

    /**
     * Group replacements by paragraph index.
     * @returns {Map<number, Array<{start, end, text}>>}
     */
    function _groupReplacementsByParagraph(file) {
        const grouped = new Map();

        for (const [gi, replText] of file.replacements) {
            const hit = file.hits.find(h => h.globalIndex === gi);
            if (!hit) continue;

            if (!grouped.has(hit.paraIndex)) {
                grouped.set(hit.paraIndex, []);
            }
            grouped.get(hit.paraIndex).push({
                start: hit.start,
                end: hit.end,
                text: replText,
            });
        }

        return grouped;
    }

    /**
     * Apply a single text replacement across <w:t> nodes.
     * Handles the case where a hit spans multiple <w:t> nodes.
     *
     * @param {Array<{node, start, end}>} nodes - nodeMap nodes for this paragraph
     * @param {number} hitStart - hit start offset in paragraph text
     * @param {number} hitEnd - hit end offset in paragraph text
     * @param {string} replText - replacement text
     */
    function _applyReplacement(nodes, hitStart, hitEnd, replText) {
        // Find which nodes overlap with [hitStart, hitEnd)
        const affected = [];
        for (const n of nodes) {
            if (n.end > hitStart && n.start < hitEnd) {
                affected.push(n);
            }
        }

        if (affected.length === 0) return;

        if (affected.length === 1) {
            // Simple case: hit is within a single <w:t> node
            const n = affected[0];
            const text = n.node.textContent;
            const localStart = hitStart - n.start;
            const localEnd = hitEnd - n.start;
            n.node.textContent = text.substring(0, localStart) + replText + text.substring(localEnd);

            // Update offsets for subsequent nodes
            const delta = replText.length - (hitEnd - hitStart);
            _shiftOffsets(nodes, n, delta);
        } else {
            // Cross-run case: hit spans multiple <w:t> nodes
            // Strategy: put replacement in first node, clear matched portions in others

            const first = affected[0];
            const last = affected[affected.length - 1];

            // Modify first node: keep text before hit, add replacement
            const firstText = first.node.textContent;
            const firstLocalStart = hitStart - first.start;
            first.node.textContent = firstText.substring(0, firstLocalStart) + replText;

            // Clear middle nodes entirely
            for (let i = 1; i < affected.length - 1; i++) {
                affected[i].node.textContent = "";
            }

            // Modify last node: keep text after hit
            if (affected.length > 1) {
                const lastText = last.node.textContent;
                const lastLocalEnd = hitEnd - last.start;
                last.node.textContent = lastText.substring(lastLocalEnd);
            }

            // Update offsets
            const delta = replText.length - (hitEnd - hitStart);
            _shiftOffsets(nodes, first, delta);
        }
    }

    /**
     * Shift offsets of all nodes after the modified one.
     */
    function _shiftOffsets(nodes, modifiedNode, delta) {
        if (delta === 0) return;

        let found = false;
        for (const n of nodes) {
            if (n === modifiedNode) {
                // Update this node's end offset
                n.end = n.start + n.node.textContent.length;
                found = true;
                continue;
            }
            if (found) {
                n.start += delta;
                n.end = n.start + n.node.textContent.length;
            }
        }
    }

    return {
        patchAndExport,
    };
})();


const DocxWriter = (() => {
    let _docxLib = null;
    let _loading = false;

    /**
     * Ensure the docx library is loaded.
     */
    async function _ensureLoaded() {
        if (_docxLib) return;
        if (_loading) {
            while (_loading) {
                await new Promise(r => setTimeout(r, 50));
            }
            return;
        }

        _loading = true;
        try {
            await new Promise((resolve, reject) => {
                const script = document.createElement("script");
                script.src = "lib/docx.min.js";
                script.onload = resolve;
                script.onerror = () => reject(new Error("Failed to load docx.min.js"));
                document.head.appendChild(script);
            });
            _docxLib = window.docx;
        } finally {
            _loading = false;
        }
    }

    /**
     * Generate and download a .docx file from paragraph strings.
     * Fallback for when no original docx is available.
     */
    async function generateDocx(paragraphs, filename) {
        await _ensureLoaded();
        const { Document, Packer, Paragraph, TextRun, HeadingLevel } = _docxLib;

        const docParagraphs = paragraphs.map(text => {
            const h3Match = text.match(/^### (.+)$/);
            const h2Match = text.match(/^## (.+)$/);
            const h1Match = text.match(/^# (.+)$/);

            if (h3Match) {
                return new Paragraph({
                    heading: HeadingLevel.HEADING_3,
                    children: [new TextRun(h3Match[1])],
                });
            }
            if (h2Match) {
                return new Paragraph({
                    heading: HeadingLevel.HEADING_2,
                    children: [new TextRun(h2Match[1])],
                });
            }
            if (h1Match) {
                return new Paragraph({
                    heading: HeadingLevel.HEADING_1,
                    children: [new TextRun(h1Match[1])],
                });
            }

            return new Paragraph({
                children: text.trim() ? [new TextRun(text)] : [],
            });
        });

        const doc = new Document({
            sections: [{
                children: docParagraphs,
            }],
        });

        const blob = await Packer.toBlob(doc);
        Files._download(blob, filename);
    }

    return {
        generateDocx,
    };
})();
