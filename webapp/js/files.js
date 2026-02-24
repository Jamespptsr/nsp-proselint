/**
 * File import and export.
 *
 * Import: .txt, .md (FileReader UTF-8), .docx (JSZip XML extraction + nodeMap)
 * Export: auto-detects format from original file extension.
 *   - .docx -> DocxPatcher (surgical XML patching, preserves all formatting)
 *   - .txt, .md, others -> plain text Blob
 */

const Files = (() => {

    /**
     * Read a File object and return file data.
     * For .docx: extracts text via XML parsing, builds nodeMap for surgical export.
     * For others: reads as plain text.
     *
     * @param {File} file
     * @returns {Promise<{name, ext, text, docxData?}>}
     */
    async function readFile(file) {
        const name = file.name;
        const ext = _getExt(name);

        if (ext === ".docx") {
            return await _readDocx(file, name, ext);
        }

        const text = await file.text();
        return { name, ext, text, docxData: null };
    }

    /**
     * Read a .docx file using JSZip + XML parsing.
     * Builds nodeMap for surgical patching on export.
     * Heading detection via <w:pStyle> — no mammoth needed.
     */
    async function _readDocx(file, name, ext) {
        const arrayBuffer = await file.arrayBuffer();

        // Load ZIP
        const zip = await JSZip.loadAsync(arrayBuffer);
        const docXmlEntry = zip.file("word/document.xml");
        if (!docXmlEntry) {
            throw new Error("Invalid .docx: missing word/document.xml");
        }

        // Parse XML
        const xmlString = await docXmlEntry.async("string");
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlString, "application/xml");

        // Extract paragraphs + build nodeMap (includes heading detection)
        const { paragraphs, nodeMap } = _extractFromXml(xmlDoc);

        const text = paragraphs.join("\n");

        return {
            name,
            ext,
            text,
            docxData: {
                zip,
                xmlDoc,
                nodeMap,  // [{paraIndex, nodes: [{node, start, end}], headingLevel}]
            },
        };
    }

    /**
     * Extract paragraph text and build nodeMap from parsed XML DOM.
     * nodeMap maps each paragraph to its <w:t> nodes with text offsets.
     * Also detects heading styles from <w:pStyle> for display formatting.
     */
    function _extractFromXml(xmlDoc) {
        const paragraphs = [];
        const nodeMap = [];

        // OOXML namespace
        const ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
        const wParagraphs = xmlDoc.getElementsByTagNameNS(ns, "p");

        for (let pi = 0; pi < wParagraphs.length; pi++) {
            const wP = wParagraphs[pi];
            const textNodes = [];
            let paraText = "";
            let offset = 0;

            // Detect heading level from <w:pPr><w:pStyle w:val="Heading1">
            let headingLevel = 0;
            const pPr = wP.getElementsByTagNameNS(ns, "pPr")[0];
            if (pPr) {
                const pStyle = pPr.getElementsByTagNameNS(ns, "pStyle")[0];
                if (pStyle) {
                    const styleVal = pStyle.getAttributeNS(ns, "val") || pStyle.getAttribute("w:val") || "";
                    const hMatch = styleVal.match(/^Heading(\d)$/i);
                    if (hMatch) {
                        headingLevel = parseInt(hMatch[1], 10);
                    }
                }
            }

            // Collect all <w:t> elements within this paragraph
            const wTs = wP.getElementsByTagNameNS(ns, "t");
            for (let ti = 0; ti < wTs.length; ti++) {
                const wT = wTs[ti];
                const nodeText = wT.textContent || "";
                if (nodeText.length > 0) {
                    textNodes.push({
                        node: wT,
                        start: offset,
                        end: offset + nodeText.length,
                    });
                    paraText += nodeText;
                    offset += nodeText.length;
                }
            }

            paragraphs.push(paraText);
            nodeMap.push({
                paraIndex: pi,
                nodes: textNodes,
                wP: wP,
                headingLevel: headingLevel,  // 0 = normal, 1-6 = h1-h6
            });
        }

        return { paragraphs, nodeMap };
    }

    /**
     * Smart export: routes by file's original extension.
     * .docx with docxData -> DocxPatcher (surgical), .docx without -> DocxWriter (generate)
     * .txt, .md -> plain text Blob
     * @param {Object} file - App state file object
     */
    async function exportFile(file) {
        if (file.ext === ".docx" && file.docxData) {
            // Surgical patching
            const outputName = _exportName(file.name, ".docx");
            await DocxPatcher.patchAndExport(file, outputName);
        } else if (file.ext === ".docx") {
            // Fallback: generate from scratch
            const text = _getModifiedText(file);
            const paragraphs = text.split("\n");
            const outputName = _exportName(file.name, ".docx");
            await DocxWriter.generateDocx(paragraphs, outputName);
        } else {
            const text = _getModifiedText(file);
            const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
            _download(blob, _exportName(file.name, file.ext));
        }
    }

    /**
     * Build modified text by applying all replacements to original paragraphs.
     */
    function _getModifiedText(file) {
        const lines = [];
        for (let pi = 0; pi < file.paragraphs.length; pi++) {
            lines.push(App.getModifiedParagraph(pi));
        }
        return lines.join("\n");
    }

    function _getExt(filename) {
        const dot = filename.lastIndexOf(".");
        return dot >= 0 ? filename.substring(dot).toLowerCase() : ".txt";
    }

    function _exportName(originalName, ext) {
        const base = originalName.replace(/\.[^.]+$/, "");
        return base + "_edited" + ext;
    }

    function _download(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    return {
        readFile,
        exportFile,
        _download,  // expose for DocxPatcher
    };
})();
