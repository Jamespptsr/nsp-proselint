/**
 * App state, initialization, and orchestration.
 *
 * Manages file list, scanning, replacement state, and UI coordination.
 */

const App = (() => {
    const state = {
        files: [],
        // Each file: {id, name, ext, originalText, paragraphs[], hits[], replacements: Map, skipped: Set}
        activeFileId: null,
        nextFileId: 1,
    };

    const _els = {};

    // ---- Initialization ----

    async function init() {
        _els.fileInput = document.getElementById("file-input");
        _els.btnImport = document.getElementById("btn-import");
        _els.btnExport = document.getElementById("btn-export");
        _els.fileList = document.getElementById("file-list");
        _els.fileName = document.getElementById("file-name");
        _els.statsDisplay = document.getElementById("stats-display");
        _els.hitList = document.getElementById("hit-list");
        _els.filterCategory = document.getElementById("filter-category");
        _els.activityLog = document.getElementById("activity-log");
        _els.btnClearLog = document.getElementById("btn-clear-log");
        _els.textDisplay = document.getElementById("text-display");
        _els.rightPanel = document.getElementById("right-panel");
        _els.btnCollapseRight = document.getElementById("btn-collapse-right");
        _els.btnExpandRight = document.getElementById("btn-expand-right");

        // Initialize editor
        Editor.init({
            onReplace: handleReplace,
            onSkip: handleSkip,
            onRevert: handleRevert,
        });

        // Load dictionaries
        log("Loading dictionaries...", "info");
        try {
            const count = await Linter.loadDictionaries([
                "data/zh_CN.json",
                "data/en.json",
            ]);
            log(`Loaded ${count} patterns (zh_CN + en)`, "ok");
        } catch (err) {
            log(`Failed to load dictionaries: ${err.message}`, "warn");
            return;
        }

        // Event listeners
        _els.btnImport.addEventListener("click", () => _els.fileInput.click());
        _els.fileInput.addEventListener("change", handleFileInput);
        _els.btnExport.addEventListener("click", handleExport);
        _els.btnClearLog.addEventListener("click", () => {
            _els.activityLog.innerHTML = "";
        });
        _els.filterCategory.addEventListener("change", () => renderHitList());

        // Right panel collapse/expand
        _els.btnCollapseRight.addEventListener("click", () => {
            _els.rightPanel.classList.add("collapsed");
            _els.btnExpandRight.style.display = "";
        });
        _els.btnExpandRight.addEventListener("click", () => {
            _els.rightPanel.classList.remove("collapsed");
            _els.btnExpandRight.style.display = "none";
        });

        // Drag and drop
        _els.textDisplay.addEventListener("dragover", (e) => {
            e.preventDefault();
            _els.textDisplay.classList.add("drag-over");
        });
        _els.textDisplay.addEventListener("dragleave", () => {
            _els.textDisplay.classList.remove("drag-over");
        });
        _els.textDisplay.addEventListener("drop", (e) => {
            e.preventDefault();
            _els.textDisplay.classList.remove("drag-over");
            if (e.dataTransfer.files.length > 0) {
                importFiles(e.dataTransfer.files);
            }
        });

        // Keyboard shortcuts
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                Editor.hidePopup();
            }
        });

        log("Ready.", "ok");
    }

    // ---- File Management ----

    async function handleFileInput(e) {
        if (e.target.files.length > 0) {
            await importFiles(e.target.files);
            e.target.value = ""; // Reset to allow re-import same file
        }
    }

    async function importFiles(fileList) {
        for (const rawFile of fileList) {
            try {
                const { name, ext, text, docxData } = await Files.readFile(rawFile);
                const file = createFileState(name, ext, text, docxData);
                state.files.push(file);
                log(`Imported: ${name}`, "ok");

                // Auto-scan
                scanFile(file);
            } catch (err) {
                log(`Failed to import ${rawFile.name}: ${err.message}`, "warn");
            }
        }

        renderFileList();

        // Auto-select first file if none active
        if (!state.activeFileId && state.files.length > 0) {
            selectFile(state.files[0].id);
        }
    }

    function createFileState(name, ext, text, docxData) {
        const id = state.nextFileId++;
        const paragraphs = text.split("\n");
        return {
            id,
            name,
            ext,
            originalText: text,
            paragraphs,
            hits: [],          // flat array of all hits with paraIndex
            replacements: new Map(), // hitGlobalIndex -> replacementText
            skipped: new Set(),      // hitGlobalIndex set
            docxData: docxData || null,  // {zip, xmlDoc, nodeMap, displayParas}
        };
    }

    function selectFile(fileId) {
        state.activeFileId = fileId;
        const file = getActiveFile();
        if (!file) return;

        renderFileList();
        _els.fileName.textContent = file.name;
        updateStats();
        updateExportButtons();
        renderHitList();
        populateCategoryFilter();
        Editor.renderFile(file);
    }

    function getActiveFile() {
        return state.files.find(f => f.id === state.activeFileId) || null;
    }

    // ---- Scanning ----

    function scanFile(file) {
        file.hits = [];
        file.replacements = new Map();
        file.skipped = new Set();

        const results = Linter.lintText(file.paragraphs);
        let globalIndex = 0;

        for (const { paraIndex, hits } of results) {
            for (const hit of hits) {
                file.hits.push({
                    ...hit,
                    paraIndex,
                    globalIndex,
                });
                globalIndex++;
            }
        }

        const hitCount = file.hits.length;
        if (hitCount > 0) {
            log(`${file.name}: ${hitCount} hit${hitCount > 1 ? "s" : ""} found`, "ok");
        } else {
            log(`${file.name}: no cliches detected`, "info");
        }
    }

    /**
     * Re-scan a single paragraph after manual edit.
     */
    function rescanParagraph(file, paraIndex) {
        // Remove old hits for this paragraph
        const oldHits = file.hits.filter(h => h.paraIndex === paraIndex);
        for (const h of oldHits) {
            file.replacements.delete(h.globalIndex);
            file.skipped.delete(h.globalIndex);
        }
        file.hits = file.hits.filter(h => h.paraIndex !== paraIndex);

        // Re-scan
        const newHits = Linter.lintParagraph(file.paragraphs[paraIndex]);
        const baseIndex = file.hits.length > 0 ? Math.max(...file.hits.map(h => h.globalIndex)) + 1 : 0;

        for (let i = 0; i < newHits.length; i++) {
            file.hits.push({
                ...newHits[i],
                paraIndex,
                globalIndex: baseIndex + i,
            });
        }
    }

    // ---- Replacement Actions ----

    function handleReplace(hitGlobalIndex, replacementText) {
        const file = getActiveFile();
        if (!file) return;

        const hit = file.hits.find(h => h.globalIndex === hitGlobalIndex);
        if (!hit) return;

        file.replacements.set(hitGlobalIndex, replacementText);
        file.skipped.delete(hitGlobalIndex);

        log(`Replaced: ${hit.entryId} -> "${_truncate(replacementText, 20)}"`, "ok");

        Editor.hidePopup();
        Editor.rerenderParagraph(file, hit.paraIndex);
        updateStats();
        renderHitList();
    }

    function handleSkip(hitGlobalIndex) {
        const file = getActiveFile();
        if (!file) return;

        const hit = file.hits.find(h => h.globalIndex === hitGlobalIndex);
        if (!hit) return;

        file.skipped.add(hitGlobalIndex);
        file.replacements.delete(hitGlobalIndex);

        log(`Skipped: ${hit.entryId}`, "info");

        Editor.hidePopup();
        Editor.rerenderParagraph(file, hit.paraIndex);
        updateStats();
        renderHitList();
    }

    function handleRevert(hitGlobalIndex) {
        const file = getActiveFile();
        if (!file) return;

        const hit = file.hits.find(h => h.globalIndex === hitGlobalIndex);
        if (!hit) return;

        file.replacements.delete(hitGlobalIndex);
        file.skipped.delete(hitGlobalIndex);

        log(`Reverted: ${hit.entryId}`, "info");

        Editor.hidePopup();
        Editor.rerenderParagraph(file, hit.paraIndex);
        updateStats();
        renderHitList();
    }

    // ---- Paragraph Edit ----

    function updateParagraph(paraIndex, newText) {
        const file = getActiveFile();
        if (!file) return;

        file.paragraphs[paraIndex] = newText;
        rescanParagraph(file, paraIndex);
        Editor.rerenderParagraph(file, paraIndex);
        updateStats();
        renderHitList();
        populateCategoryFilter();
        log(`Edited paragraph ${paraIndex + 1}, re-scanned`, "info");
    }

    /**
     * Get the modified text for a paragraph with replacements applied.
     */
    function getModifiedParagraph(paraIndex) {
        const file = getActiveFile();
        if (!file) return "";

        let text = file.paragraphs[paraIndex];

        // Gather replacements for this paragraph, sorted by start desc
        const paraRepls = [];
        for (const [gi, replText] of file.replacements) {
            const hit = file.hits.find(h => h.globalIndex === gi);
            if (hit && hit.paraIndex === paraIndex) {
                paraRepls.push({ start: hit.start, end: hit.end, replText });
            }
        }

        // Apply in reverse order to preserve offsets
        paraRepls.sort((a, b) => b.start - a.start);
        for (const { start, end, replText } of paraRepls) {
            text = text.substring(0, start) + replText + text.substring(end);
        }

        return text;
    }

    // ---- Export ----

    async function handleExport() {
        const file = getActiveFile();
        if (!file) return;
        try {
            await Files.exportFile(file);
            log(`Exported: ${file.name} (${file.ext})`, "ok");
        } catch (err) {
            log(`Export failed: ${err.message}`, "warn");
        }
    }

    function updateExportButtons() {
        const hasFile = !!getActiveFile();
        _els.btnExport.disabled = !hasFile;
    }

    // ---- UI Rendering ----

    function renderFileList() {
        _els.fileList.innerHTML = "";
        for (const file of state.files) {
            const div = document.createElement("div");
            div.className = "file-item" + (file.id === state.activeFileId ? " active" : "");

            const nameSpan = document.createElement("span");
            nameSpan.textContent = file.name;
            div.appendChild(nameSpan);

            const meta = document.createElement("span");
            const hitCount = file.hits.length;
            const replCount = file.replacements.size;
            meta.className = "file-hits";
            if (hitCount > 0) {
                meta.textContent = replCount > 0 ? `${hitCount} / ${replCount}` : `${hitCount}`;
            }
            div.appendChild(meta);

            div.addEventListener("click", () => selectFile(file.id));
            _els.fileList.appendChild(div);
        }
    }

    function updateStats() {
        const file = getActiveFile();
        if (!file) {
            _els.statsDisplay.textContent = "";
            return;
        }

        const total = file.hits.length;
        const replaced = file.replacements.size;
        const skipped = file.skipped.size;
        const pending = total - replaced - skipped;

        const parts = [];
        parts.push(`${total} hit${total !== 1 ? "s" : ""}`);
        if (replaced > 0) parts.push(`${replaced} replaced`);
        if (skipped > 0) parts.push(`${skipped} skipped`);
        if (pending > 0 && pending < total) parts.push(`${pending} pending`);

        _els.statsDisplay.textContent = parts.join(" | ");
    }

    function renderHitList() {
        const file = getActiveFile();
        _els.hitList.innerHTML = "";
        if (!file || file.hits.length === 0) {
            _els.hitList.innerHTML = '<div style="padding:12px;color:var(--text-meta);font-size:12px;">No hits</div>';
            return;
        }

        const filterCat = _els.filterCategory.value;

        for (const hit of file.hits) {
            if (filterCat && hit.category !== filterCat) continue;

            const isReplaced = file.replacements.has(hit.globalIndex);
            const isSkipped = file.skipped.has(hit.globalIndex);
            const isDetectOnly = hit.severity === "detect_only";

            const div = document.createElement("div");
            div.className = "hit-item";
            if (isReplaced) div.className += " replaced-item";
            if (isSkipped) div.className += " skipped-item";
            div.dataset.hitIndex = hit.globalIndex;

            // Entry ID line
            const idEl = document.createElement("div");
            idEl.className = "hit-entry-id";
            if (isReplaced) {
                idEl.className += " replaced-id";
                idEl.textContent = `${hit.category} (replaced)`;
            } else if (isSkipped) {
                idEl.className += " skipped-id";
                idEl.textContent = `${hit.category} (skipped)`;
            } else if (isDetectOnly) {
                idEl.className += " detect-only-id";
                idEl.textContent = `${hit.category} (detect only)`;
            } else {
                idEl.textContent = hit.category;
            }
            div.appendChild(idEl);

            // Match text
            const matchEl = document.createElement("div");
            matchEl.className = "hit-match-text" + (isReplaced ? " replaced-text" : "");
            matchEl.textContent = `"${_truncate(hit.matchText, 30)}"`;
            div.appendChild(matchEl);

            // Info line
            const infoEl = document.createElement("div");
            infoEl.className = "hit-replacement-info";
            if (isReplaced) {
                infoEl.className += " replaced-info";
                infoEl.textContent = `-> ${_truncate(file.replacements.get(hit.globalIndex), 30)}`;
            } else if (isDetectOnly) {
                infoEl.textContent = "No auto-replacements";
            } else {
                infoEl.textContent = `${hit.replacements.length} replacement${hit.replacements.length !== 1 ? "s" : ""}`;
            }
            div.appendChild(infoEl);

            // Click to scroll to hit in text
            div.addEventListener("click", () => {
                Editor.scrollToHit(hit.globalIndex);
            });

            _els.hitList.appendChild(div);
        }
    }

    function highlightHitInList(hitGlobalIndex) {
        _els.hitList.querySelectorAll(".hit-item.active").forEach(el => el.classList.remove("active"));
        const el = _els.hitList.querySelector(`[data-hit-index="${hitGlobalIndex}"]`);
        if (el) {
            el.classList.add("active");
            el.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
    }

    function populateCategoryFilter() {
        const file = getActiveFile();
        const currentVal = _els.filterCategory.value;
        _els.filterCategory.innerHTML = '<option value="">All categories</option>';

        if (!file) return;

        const categories = new Set();
        for (const hit of file.hits) {
            categories.add(hit.category);
        }

        const sorted = [...categories].sort();
        for (const cat of sorted) {
            const opt = document.createElement("option");
            opt.value = cat;
            opt.textContent = cat;
            _els.filterCategory.appendChild(opt);
        }

        _els.filterCategory.value = currentVal;
    }

    // ---- Logging ----

    function log(msg, level = "info") {
        const entry = document.createElement("div");
        entry.className = "log-entry";
        if (level === "ok") entry.className += " log-ok";
        else if (level === "warn") entry.className += " log-warn";
        else if (level === "info") entry.className += " log-info";
        entry.textContent = msg;
        _els.activityLog.appendChild(entry);
        _els.activityLog.scrollTop = _els.activityLog.scrollHeight;
    }

    function _truncate(str, max) {
        if (!str) return "";
        return str.length > max ? str.substring(0, max) + "..." : str;
    }

    // ---- Boot ----

    document.addEventListener("DOMContentLoaded", init);

    return {
        getActiveFile,
        getModifiedParagraph,
        updateParagraph,
        highlightHitInList,
        selectFile,
        log,
    };
})();
