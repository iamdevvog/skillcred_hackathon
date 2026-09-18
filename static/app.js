// ==========================================================================
// POLICYLENS — FRONTEND CONTROLLER & CHANGE RENDERER
// ==========================================================================

let presetsData = {};
let currentResults = null;
let activeInputMode = "files"; // 'files' or 'text'
let activeCategoryFilter = "all";
let searchQuery = "";

// DOM Elements
const tabFiles = document.getElementById("tabFiles");
const tabText = document.getElementById("tabText");
const fileUploadContainer = document.getElementById("fileUploadContainer");
const textEditorContainer = document.getElementById("textEditorContainer");

const dropzoneOld = document.getElementById("dropzoneOld");
const dropzoneNew = document.getElementById("dropzoneNew");
const oldFileInput = document.getElementById("oldFileInput");
const newFileInput = document.getElementById("newFileInput");
const oldFileName = document.getElementById("oldFileName");
const newFileName = document.getElementById("newFileName");
const oldFileSize = document.getElementById("oldFileSize");
const newFileSize = document.getElementById("newFileSize");

const rawOldText = document.getElementById("rawOldText");
const rawNewText = document.getElementById("rawNewText");
const oldCharCount = document.getElementById("oldCharCount");
const newCharCount = document.getElementById("newCharCount");

const compareBtn = document.getElementById("compareBtn");
const errorMessage = document.getElementById("errorMessage");
const loadingState = document.getElementById("loadingState");
const resultsSection = document.getElementById("resultsSection");
const presetButtons = document.getElementById("presetButtons");

const labelOldDoc = document.getElementById("labelOldDoc");
const labelNewDoc = document.getElementById("labelNewDoc");
const totalChanges = document.getElementById("totalChanges");
const modifiedCount = document.getElementById("modifiedCount");
const addedCount = document.getElementById("addedCount");
const removedCount = document.getElementById("removedCount");
const executiveTakeaways = document.getElementById("executiveTakeaways");

const searchInput = document.getElementById("searchInput");
const categoryChips = document.getElementById("categoryChips");

const btnExportCsv = document.getElementById("btnExportCsv");
const btnPrintReport = document.getElementById("btnPrintReport");

// INITIALIZATION
document.addEventListener("DOMContentLoaded", async () => {
  setupTabs();
  setupDragAndDrop();
  setupTextCounters();
  setupFiltersAndSearch();
  setupViewTabs();
  setupExports();
  await loadPresets();
});

// TAB SWITCHING
function setupTabs() {
  tabFiles.onclick = () => {
    activeInputMode = "files";
    tabFiles.classList.add("active");
    tabText.classList.remove("active");
    fileUploadContainer.classList.add("active");
    textEditorContainer.classList.remove("active");
  };

  tabText.onclick = () => {
    activeInputMode = "text";
    tabText.classList.add("active");
    tabFiles.classList.remove("active");
    textEditorContainer.classList.add("active");
    fileUploadContainer.classList.remove("active");
  };
}

// DRAG AND DROP
function setupDragAndDrop() {
  [
    { zone: dropzoneOld, input: oldFileInput, name: oldFileName, size: oldFileSize },
    { zone: dropzoneNew, input: newFileInput, name: newFileName, size: newFileSize }
  ].forEach(({ zone, input, name, size }) => {
    ["dragenter", "dragover"].forEach(ev => {
      zone.addEventListener(ev, e => {
        e.preventDefault();
        zone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach(ev => {
      zone.addEventListener(ev, e => {
        e.preventDefault();
        zone.classList.remove("dragover");
      });
    });

    zone.addEventListener("drop", e => {
      if (e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        updateFileTag(input.files[0], name, size);
      }
    });

    input.addEventListener("change", () => {
      if (input.files.length) {
        updateFileTag(input.files[0], name, size);
      }
    });
  });
}

function updateFileTag(file, nameEl, sizeEl) {
  if (!file) return;
  nameEl.textContent = file.name;
  sizeEl.textContent = `(${formatBytes(file.size)})`;
}

function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

// TEXT EDITORS COUNTER
function setupTextCounters() {
  const updateCounts = () => {
    oldCharCount.textContent = `${rawOldText.value.length} chars`;
    newCharCount.textContent = `${rawNewText.value.length} chars`;
  };
  rawOldText.addEventListener("input", updateCounts);
  rawNewText.addEventListener("input", updateCounts);
}

// LOAD SAMPLE PRESETS
async function loadPresets() {
  try {
    const res = await fetch("/api/presets");
    presetsData = await res.json();
    setupPresetButtons();
    selectPreset("hr_policy", true);
  } catch (err) {
    console.error("Failed to load sample presets:", err);
  }
}

function setupPresetButtons() {
  presetButtons.querySelectorAll(".preset-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const pKey = chip.getAttribute("data-preset");
      presetButtons.querySelectorAll(".preset-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      selectPreset(pKey, false);
    });
  });
}

function selectPreset(key, autoRun = false) {
  const preset = presetsData[key];
  if (!preset) return;

  rawOldText.value = preset.old_text;
  rawNewText.value = preset.new_text;
  oldFileName.textContent = `${preset.old_title}.txt`;
  newFileName.textContent = `${preset.new_title}.txt`;
  oldFileSize.textContent = "(Sample ready)";
  newFileSize.textContent = "(Sample ready)";

  oldCharCount.textContent = `${rawOldText.value.length} chars`;
  newCharCount.textContent = `${rawNewText.value.length} chars`;

  if (autoRun) {
    runComparison();
  }
}

// RUN COMPARISON
compareBtn.onclick = runComparison;

async function runComparison() {
  errorMessage.classList.add("hidden");
  errorMessage.textContent = "";

  let payload = null;
  let isFormData = false;

  if (activeInputMode === "files" && oldFileInput.files[0] && newFileInput.files[0]) {
    const fd = new FormData();
    fd.append("old_file", oldFileInput.files[0]);
    fd.append("new_file", newFileInput.files[0]);
    payload = fd;
    isFormData = true;
  } else {
    const oldT = rawOldText.value.trim();
    const newT = rawNewText.value.trim();
    if (!oldT || !newT) {
      errorMessage.textContent = "Please upload documents or paste text into both input areas.";
      errorMessage.classList.remove("hidden");
      return;
    }
    payload = JSON.stringify({
      old_text: oldT,
      new_text: newT,
      old_filename: oldFileName.textContent || "Original Policy",
      new_filename: newFileName.textContent || "Revised Policy"
    });
  }

  loadingState.classList.remove("hidden");
  resultsSection.classList.add("hidden");

  try {
    const fetchOptions = {
      method: "POST",
      body: payload
    };
    if (!isFormData) {
      fetchOptions.headers = { "Content-Type": "application/json" };
    }

    const res = await fetch("/compare", fetchOptions);
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Comparison failed.");
    }

    currentResults = data;
    renderResults(data);

  } catch (err) {
    errorMessage.textContent = err.message;
    errorMessage.classList.remove("hidden");
  } finally {
    loadingState.classList.add("hidden");
  }
}

// RENDER RESULTS
function renderResults(data) {
  resultsSection.classList.remove("hidden");

  // Overview Header
  labelOldDoc.textContent = data.old_filename || "Original Policy";
  labelNewDoc.textContent = data.new_filename || "Revised Policy";

  const summary = data.summary || {};
  totalChanges.textContent = summary.total_changes || 0;
  modifiedCount.textContent = summary.modified || 0;
  addedCount.textContent = summary.added || 0;
  removedCount.textContent = summary.removed || 0;

  // Key Takeaways
  const takeaways = data.executive_briefing?.takeaways || [];
  executiveTakeaways.innerHTML = "";

  if (takeaways.length > 0) {
    takeaways.forEach(t => {
      const row = document.createElement("div");
      const typeClass = t.type === "high" ? "type-high" : t.type === "favorable" ? "type-favorable" : "";
      const badgeClass = t.type === "high" ? "badge-tag-high" : t.type === "favorable" ? "badge-tag-favorable" : "badge-tag-moderate";
      row.className = `takeaway-row ${typeClass}`;
      row.innerHTML = `
        <div class="takeaway-header-line">
          <span class="takeaway-sec-name">${escapeHtml(t.title)}</span>
          <span class="takeaway-badge-tag ${badgeClass}">${escapeHtml(t.badge)}</span>
        </div>
        <div class="takeaway-body-text">${escapeHtml(t.summary)}</div>
      `;
      executiveTakeaways.appendChild(row);
    });
  } else {
    executiveTakeaways.innerHTML = `<div style="color:var(--text-muted); font-size:13px;">No major high-impact shifts detected. All changes are standard updates.</div>`;
  }

  renderActiveViews();
}

// RENDER VIEWS
function renderActiveViews() {
  if (!currentResults || !currentResults.sections) return;

  const filtered = currentResults.sections.filter(sec => {
    // Search query
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchTitle = (sec.display_title || "").toLowerCase().includes(q);
      const matchOld = (sec.old_text || "").toLowerCase().includes(q);
      const matchNew = (sec.new_text || "").toLowerCase().includes(q);
      const matchSumm = (sec.summary || "").toLowerCase().includes(q);
      if (!matchTitle && !matchOld && !matchNew && !matchSumm) return false;
    }

    // Category filter
    if (activeCategoryFilter !== "all" && sec.category !== activeCategoryFilter) {
      return false;
    }

    return true;
  });

  renderSideBySide(filtered);
  renderSummaryTable(filtered);
  renderDeltaLedger(currentResults.all_deltas || []);
}

// 1. SIDE-BY-SIDE RENDERER
function renderSideBySide(sections) {
  const container = document.getElementById("clauseCardsContainer");
  container.innerHTML = "";

  if (sections.length === 0) {
    container.innerHTML = `<div class="card" style="text-align:center; padding:32px; color:var(--text-muted);">No sections match the current filter.</div>`;
    return;
  }

  sections.forEach(sec => {
    const card = document.createElement("div");
    card.className = "clause-card";

    const deltaPills = (sec.deltas || []).map(d => {
      const cls = d.direction === "increased" ? "increased" : d.direction === "decreased" ? "decreased" : "";
      return `<span class="val-pill ${cls}">${escapeHtml(d.description)}</span>`;
    }).join("");

    card.innerHTML = `
      <div class="clause-card-top">
        <span class="clause-card-title">${escapeHtml(sec.display_title)}</span>
        <div class="clause-card-badges">
          <span class="badge badge-category">${escapeHtml(sec.category)}</span>
          <span class="badge badge-${sec.status}">${sec.status}</span>
        </div>
      </div>
      <div class="clause-comparison-grid">
        <div class="clause-pane">
          <div class="pane-title">Original Version</div>
          <div class="pane-text">${sec.diff_html ? sec.diff_html.old_html : escapeHtml(sec.old_text || "—")}</div>
        </div>
        <div class="clause-pane">
          <div class="pane-title">Revised Version</div>
          <div class="pane-text">${sec.diff_html ? sec.diff_html.new_html : escapeHtml(sec.new_text || "—")}</div>
        </div>
      </div>
      <div class="clause-card-bottom">
        <div><strong>What changed:</strong> ${escapeHtml(sec.summary || "No changes.")}</div>
        ${deltaPills ? `<div class="values-shift-row">${deltaPills}</div>` : ''}
      </div>
    `;
    container.appendChild(card);
  });
}

// 2. SUMMARY TABLE RENDERER
function renderSummaryTable(sections) {
  const tbody = document.getElementById("changeMatrixBody");
  tbody.innerHTML = "";

  if (sections.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:24px; color:var(--text-muted);">No matching sections.</td></tr>`;
    return;
  }

  sections.forEach(sec => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><div class="table-heading">${escapeHtml(sec.display_title)}</div></td>
      <td><span class="badge badge-category">${escapeHtml(sec.category)}</span></td>
      <td><span class="badge badge-${sec.status}">${sec.status}</span></td>
      <td><div>${escapeHtml(sec.summary)}</div></td>
    `;
    tbody.appendChild(tr);
  });
}

// 3. VALUE SHIFTS TABLE RENDERER
function renderDeltaLedger(deltas) {
  const tbody = document.getElementById("deltasLedgerBody");
  tbody.innerHTML = "";

  if (!deltas || deltas.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:24px; color:var(--text-muted);">No specific numeric or date changes found in this document.</td></tr>`;
    return;
  }

  deltas.forEach(d => {
    const tr = document.createElement("tr");
    const dir = d.direction === "increased" ? "Increased" : d.direction === "decreased" ? "Decreased" : d.direction === "added" ? "Added" : d.direction === "removed" ? "Removed" : "Modified";

    tr.innerHTML = `
      <td><span class="badge badge-category">${escapeHtml(d.type.toUpperCase())}</span></td>
      <td><span class="delta-old">${escapeHtml(d.old || "—")}</span></td>
      <td>➔</td>
      <td><span class="delta-new">${escapeHtml(d.new || "—")}</span></td>
      <td><strong>${dir}</strong></td>
      <td><span class="delta-shift">${escapeHtml(d.pct_change || "Value update")}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// SEARCH & CATEGORY FILTERS
function setupFiltersAndSearch() {
  searchInput.addEventListener("input", e => {
    searchQuery = e.target.value.trim();
    renderActiveViews();
  });

  categoryChips.querySelectorAll(".filter-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      categoryChips.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      activeCategoryFilter = chip.getAttribute("data-filter");
      renderActiveViews();
    });
  });
}

// VIEW SWITCHER TABS
function setupViewTabs() {
  document.querySelectorAll(".view-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".view-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".view-panel").forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const viewKey = btn.getAttribute("data-view");

      if (viewKey === "sideBySide") document.getElementById("viewSideBySide").classList.add("active");
      if (viewKey === "changeMatrix") document.getElementById("viewChangeMatrix").classList.add("active");
      if (viewKey === "deltasLedger") document.getElementById("viewDeltasLedger").classList.add("active");
    });
  });
}

// EXPORT ACTIONS
function setupExports() {
  btnExportCsv.addEventListener("click", async () => {
    if (!currentResults) return;
    try {
      const res = await fetch("/api/export/csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentResults)
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Policy_Comparison_${new Date().toISOString().slice(0,10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert("Failed to export CSV: " + err.message);
    }
  });

  btnPrintReport.addEventListener("click", () => {
    window.print();
  });
}

// HTML ESCAPE
function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  }[c]));
}
