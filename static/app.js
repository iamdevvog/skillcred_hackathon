/**
 * Frontend application logic for Policy Document Comparison System.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const textV1 = document.getElementById("text-v1");
  const textV2 = document.getElementById("text-v2");
  const fileV1 = document.getElementById("file-v1");
  const fileV2 = document.getElementById("file-v2");
  const statusV1 = document.getElementById("status-v1");
  const statusV2 = document.getElementById("status-v2");
  const dropAreaV1 = document.getElementById("drop-area-v1");
  const dropAreaV2 = document.getElementById("drop-area-v2");

  const slider = document.getElementById("similarity-slider");
  const thresholdVal = document.getElementById("threshold-val");

  const btnLoadSample = document.getElementById("btn-load-sample");
  const btnCompare = document.getElementById("btn-compare");
  const btnExportJson = document.getElementById("btn-export-json");
  const btnEval = document.getElementById("btn-eval");
  const modalEval = document.getElementById("modal-eval");
  const btnModalClose = document.getElementById("btn-modal-close");
  const btnEvalClose = document.getElementById("btn-eval-close");

  const resultsContainer = document.getElementById("results-container");
  const searchInput = document.getElementById("search-input");
  const filterPills = document.getElementById("filter-pills");
  const sectionList = document.getElementById("section-list");

  // Metrics
  const metricTotal = document.getElementById("metric-total");
  const metricAdded = document.getElementById("metric-added");
  const metricRemoved = document.getElementById("metric-removed");
  const metricModified = document.getElementById("metric-modified");
  const metricUnchanged = document.getElementById("metric-unchanged");

  // Detail Inspector Elements
  const detailEmpty = document.getElementById("detail-empty");
  const detailActive = document.getElementById("detail-active");
  const detailChangeType = document.getElementById("detail-change-type");
  const detailTitle = document.getElementById("detail-title");
  const detailCategory = document.getElementById("detail-category");
  const detailSimilarity = document.getElementById("detail-similarity");
  const detailMethod = document.getElementById("detail-method");

  const bannerVerified = document.getElementById("detail-verification-banner");
  const bannerTitle = document.getElementById("banner-title");
  const bannerDesc = document.getElementById("banner-desc");

  const entityCardsContainer = document.getElementById("entity-cards-container");
  const entitiesCount = document.getElementById("entities-count");

  const tabWordDiff = document.getElementById("tab-word-diff");
  const tabSplitDiff = document.getElementById("tab-split-diff");
  const panelWordDiff = document.getElementById("panel-word-diff");
  const panelSplitDiff = document.getElementById("panel-split-diff");
  const wordDiffDisplay = document.getElementById("word-diff-display");
  const splitTextV1 = document.getElementById("split-text-v1");
  const splitTextV2 = document.getElementById("split-text-v2");
  const splitV1Lines = document.getElementById("split-v1-lines");
  const splitV2Lines = document.getElementById("split-v2-lines");
  const btnCopyEvidence = document.getElementById("btn-copy-evidence");

  // App State
  let currentSummary = null;
  let selectedIndex = -1;
  let activeFilter = "all";
  let searchQuery = "";

  // -------------------------------------------------------------
  // Slider Threshold Display
  // -------------------------------------------------------------
  slider.addEventListener("input", (e) => {
    thresholdVal.textContent = parseFloat(e.target.value).toFixed(2);
  });

  // -------------------------------------------------------------
  // Drag & Drop Setup
  // -------------------------------------------------------------
  function setupDropzone(dropArea, fileInput, textArea, statusElem, label) {
    dropArea.addEventListener("click", () => fileInput.click());

    ["dragenter", "dragover"].forEach((eventName) => {
      dropArea.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropArea.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropArea.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropArea.classList.remove("dragover");
      });
    });

    dropArea.addEventListener("drop", (e) => {
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        readFile(files[0], textArea, statusElem);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (fileInput.files.length > 0) {
        readFile(fileInput.files[0], textArea, statusElem);
      }
    });
  }

  function readFile(file, textArea, statusElem) {
    statusElem.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    const reader = new FileReader();
    reader.onload = (e) => {
      textArea.value = e.target.result;
    };
    reader.readAsText(file);
  }

  setupDropzone(dropAreaV1, fileV1, textV1, statusV1, "Version 1");
  setupDropzone(dropAreaV2, fileV2, textV2, statusV2, "Version 2");

  // -------------------------------------------------------------
  // 1-Click Sample Policy Loader
  // -------------------------------------------------------------
  btnLoadSample.addEventListener("click", async () => {
    btnLoadSample.disabled = true;
    btnLoadSample.textContent = "Loading...";
    try {
      const res = await fetch("/api/sample");
      if (!res.ok) throw new Error("Failed to load sample documents");
      const data = await res.json();

      textV1.value = data.policy_v1;
      textV2.value = data.policy_v2;
      statusV1.textContent = "policy_v1.txt (Sample)";
      statusV2.textContent = "policy_v2.txt (Sample)";

      // Auto-trigger comparison
      btnCompare.click();
    } catch (err) {
      alert("Error loading sample policies: " + err.message);
    } finally {
      btnLoadSample.disabled = false;
      btnLoadSample.innerHTML = '<span class="icon">📄</span> Load Sample Policy (V1 vs V2)';
    }
  });

  // -------------------------------------------------------------
  // Execute Comparison Pipeline
  // -------------------------------------------------------------
  btnCompare.addEventListener("click", async () => {
    const v1Content = textV1.value.trim();
    const v2Content = textV2.value.trim();

    if (!v1Content || !v2Content) {
      alert("Please provide text for both Document Version 1 and Version 2.");
      return;
    }

    btnCompare.disabled = true;
    btnCompare.innerHTML = '<span class="icon">⏳</span> Analyzing & Aligning Sections...';

    try {
      const payload = {
        text_v1: v1Content,
        text_v2: v2Content,
        min_similarity_threshold: parseFloat(slider.value),
      };

      const res = await fetch("/api/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Comparison failed");
      }

      currentSummary = await res.json();
      renderComparisonResults(currentSummary);
      btnExportJson.disabled = false;
    } catch (err) {
      alert("Comparison failed: " + err.message);
    } finally {
      btnCompare.disabled = false;
      btnCompare.innerHTML = '<span class="icon">⚡</span> Run Deterministic & Semantic Comparison';
    }
  });

  // -------------------------------------------------------------
  // Render Comparison Results
  // -------------------------------------------------------------
  function renderComparisonResults(summary) {
    resultsContainer.classList.remove("hidden");
    resultsContainer.scrollIntoView({ behavior: "smooth", block: "start" });

    // 1. Metric Cards
    metricTotal.textContent = summary.total_changes;
    metricAdded.textContent = summary.added;
    metricRemoved.textContent = summary.removed;
    metricModified.textContent = summary.modified;
    metricUnchanged.textContent = summary.unchanged;

    // 2. Filter Counts
    document.getElementById("count-all").textContent = summary.records.length;
    document.getElementById("count-modified").textContent = summary.modified;
    document.getElementById("count-added").textContent = summary.added;
    document.getElementById("count-removed").textContent = summary.removed;
    document.getElementById("count-unchanged").textContent = summary.unchanged;

    // 3. Render Section List
    renderSectionList();

    // 4. Automatically select the first modified section or first record
    const firstModIdx = summary.records.findIndex((r) => r.change_type === "modified");
    if (firstModIdx !== -1) {
      selectSection(firstModIdx);
    } else if (summary.records.length > 0) {
      selectSection(0);
    }
  }

  // -------------------------------------------------------------
  // Section List Rendering & Filtering
  // -------------------------------------------------------------
  function renderSectionList() {
    if (!currentSummary) return;

    sectionList.innerHTML = "";
    const query = searchQuery.toLowerCase().trim();

    currentSummary.records.forEach((record, idx) => {
      // Filter by type
      if (activeFilter !== "all" && record.change_type !== activeFilter) {
        return;
      }

      // Filter by search query
      if (query) {
        const titleMatch = record.section.toLowerCase().includes(query);
        const catMatch = record.category.toLowerCase().includes(query);
        const oldMatch = record.old_text && record.old_text.toLowerCase().includes(query);
        const newMatch = record.new_text && record.new_text.toLowerCase().includes(query);
        if (!titleMatch && !catMatch && !oldMatch && !newMatch) {
          return;
        }
      }

      const item = document.createElement("div");
      item.className = `section-item ${idx === selectedIndex ? "selected" : ""}`;
      item.dataset.index = idx;

      const badgeClass = `badge-${record.change_type}`;
      const verifiedIcon = record.verified ? "🛡️" : "⚠️";

      item.innerHTML = `
        <div class="item-top">
          <span class="badge-type ${badgeClass}">${record.change_type}</span>
          <span title="${record.verified ? 'Verified Aligned Pair' : 'Single-Document Evidence'}">${verifiedIcon}</span>
        </div>
        <div class="item-title" title="${escapeHtml(record.section)}">${escapeHtml(record.section)}</div>
        <div class="item-meta">
          <span class="cat-tag">${record.category}</span>
          <span>Sim: ${(record.similarity || 0).toFixed(2)}</span>
          ${record.entities_changed.length > 0 ? `<span>🎯 ${record.entities_changed.length} vals</span>` : ""}
        </div>
      `;

      item.addEventListener("click", () => selectSection(idx));
      sectionList.appendChild(item);
    });

    if (sectionList.children.length === 0) {
      sectionList.innerHTML = '<div style="padding: 24px; text-align: center; color: #94a3b8;">No matching sections found.</div>';
    }
  }

  // Filter Pill Click Handlers
  filterPills.addEventListener("click", (e) => {
    const btn = e.target.closest(".pill-btn");
    if (!btn) return;

    filterPills.querySelectorAll(".pill-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    activeFilter = btn.dataset.filter;
    renderSectionList();
  });

  // Search Input Handler
  searchInput.addEventListener("input", (e) => {
    searchQuery = e.target.value;
    renderSectionList();
  });

  // -------------------------------------------------------------
  // Select Section & Populate Inspector
  // -------------------------------------------------------------
  function selectSection(idx) {
    if (!currentSummary || !currentSummary.records[idx]) return;

    selectedIndex = idx;

    // Highlight in list
    sectionList.querySelectorAll(".section-item").forEach((el) => {
      el.classList.toggle("selected", parseInt(el.dataset.index) === idx);
    });

    const r = currentSummary.records[idx];

    detailEmpty.classList.add("hidden");
    detailActive.classList.remove("hidden");

    // Header Info
    detailTitle.textContent = r.section;
    detailChangeType.textContent = r.change_type.toUpperCase();
    detailChangeType.className = `badge-type badge-${r.change_type}`;

    detailCategory.textContent = r.category;
    detailSimilarity.textContent = (r.similarity || 0).toFixed(2);
    detailMethod.textContent = r.match_method;

    // Verification Shield Banner (STRICT RULE ENFORCEMENT)
    if (r.verified) {
      bannerVerified.className = "verification-banner banner-verified";
      document.getElementById("banner-icon").textContent = "🛡️";
      bannerTitle.textContent = "VERIFIED EVIDENCE PAIR";
      bannerDesc.textContent = "Aligned old/new evidence pair confirmed. Strictly verified for audit and reliable AI explanation.";
    } else {
      bannerVerified.className = "verification-banner banner-unverified";
      document.getElementById("banner-icon").textContent = "⚠️";
      bannerTitle.textContent = "UNVERIFIED EVIDENCE (SINGLE DOCUMENT)";
      bannerDesc.textContent = "This section exists in only one document version (Added or Removed). No aligned evidence pair exists.";
    }

    // Critical Value / Entity Changes
    renderEntityCards(r.entities_changed);

    // Diffs
    wordDiffDisplay.innerHTML = r.word_diff_html || "<p style='color: #64748b;'>No textual differences.</p>";
    splitTextV1.textContent = r.old_text || "(Section was not present in Old Version — Added section)";
    splitTextV2.textContent = r.new_text || "(Section was removed in New Version — Deleted section)";

    splitV1Lines.textContent = r.old_text ? `${r.old_text.split("\n").length} lines` : "None";
    splitV2Lines.textContent = r.new_text ? `${r.new_text.split("\n").length} lines` : "None";
  }

  function renderEntityCards(entities) {
    entityCardsContainer.innerHTML = "";
    entitiesCount.textContent = `${entities.length} value change${entities.length === 1 ? "" : "s"}`;

    if (!entities || entities.length === 0) {
      entityCardsContainer.innerHTML = "<p style='color: #64748b; font-size: 0.85rem;'>No numeric or threshold entity changes detected in this section.</p>";
      return;
    }

    entities.forEach((ec) => {
      const card = document.createElement("div");
      card.className = "entity-pill";
      card.innerHTML = `
        <span class="pill-cat">${escapeHtml(ec.entity)}</span>
        <div class="pill-val-change">
          <span class="old-val">${escapeHtml(ec.old_value || "—")}</span>
          <span class="arrow">➔</span>
          <span class="new-val">${escapeHtml(ec.new_value || "—")}</span>
        </div>
      `;
      entityCardsContainer.appendChild(card);
    });
  }

  // -------------------------------------------------------------
  // Diff View Mode Toggle (Word Diff vs Split View)
  // -------------------------------------------------------------
  tabWordDiff.addEventListener("click", () => {
    tabWordDiff.classList.add("active");
    tabSplitDiff.classList.remove("active");
    panelWordDiff.classList.remove("hidden");
    panelSplitDiff.classList.add("hidden");
  });

  tabSplitDiff.addEventListener("click", () => {
    tabSplitDiff.classList.add("active");
    tabWordDiff.classList.remove("active");
    panelSplitDiff.classList.remove("hidden");
    panelWordDiff.classList.add("hidden");
  });

  // -------------------------------------------------------------
  // Copy Evidence to Clipboard
  // -------------------------------------------------------------
  btnCopyEvidence.addEventListener("click", () => {
    if (!currentSummary || selectedIndex === -1) return;
    const r = currentSummary.records[selectedIndex];

    const textToCopy = `
=== SECTION EVIDENCE REPORT ===
Section: ${r.section}
Change Type: ${r.change_type.toUpperCase()}
Category: ${r.category}
Verified: ${r.verified ? "YES (Aligned Pair)" : "NO (Single Document)"}
Similarity: ${(r.similarity || 0).toFixed(2)}

--- OLD VERSION ---
${r.old_text || "N/A"}

--- NEW VERSION ---
${r.new_text || "N/A"}

--- VALUE CHANGES ---
${r.entities_changed.map((e) => `* [${e.entity.toUpperCase()}] ${e.old_value} -> ${e.new_value}`).join("\n") || "None"}
===============================
    `.trim();

    navigator.clipboard.writeText(textToCopy).then(() => {
      const orig = btnCopyEvidence.textContent;
      btnCopyEvidence.textContent = "✅ Copied!";
      setTimeout(() => (btnCopyEvidence.textContent = orig), 2000);
    });
  });

  // -------------------------------------------------------------
  // Export JSON Report
  // -------------------------------------------------------------
  btnExportJson.addEventListener("click", () => {
    if (!currentSummary) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentSummary, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `policy_comparison_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  });

  // -------------------------------------------------------------
  // Benchmark Evaluation Modal
  // -------------------------------------------------------------
  btnEval.addEventListener("click", async () => {
    modalEval.classList.remove("hidden");
    try {
      const res = await fetch("/api/evaluate");
      if (res.ok) {
        const d = await res.json();
        document.getElementById("eval-f1").textContent = `${(d.f1 * 100).toFixed(2)}%`;
        document.getElementById("eval-precision").textContent = `${(d.precision * 100).toFixed(2)}%`;
        document.getElementById("eval-recall").textContent = `${(d.recall * 100).toFixed(2)}%`;
        document.getElementById("eval-tp").textContent = d.true_positives;
        document.getElementById("eval-fp").textContent = d.false_positives;
        document.getElementById("eval-fn").textContent = d.false_negatives;
      }
    } catch (e) {
      console.error(e);
    }
  });

  btnModalClose.addEventListener("click", () => modalEval.classList.add("hidden"));
  btnEvalClose.addEventListener("click", () => modalEval.classList.add("hidden"));

  // Helper: Escape HTML
  function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
});
