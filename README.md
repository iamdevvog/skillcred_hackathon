<<<<<<< HEAD
# Policy Document Comparison System

A deterministic-first Python system that compares two versions of a policy/regulation/internal guideline document.

## Key Capabilities
1. **Added, Removed, and Modified Sections**: Accurately detects additions, deletions, and textual edits.
2. **Deterministic Diffing**: Highlights word-level insertions (`<ins>`) and deletions (`<del>`) using `difflib`.
3. **Semantic Section Alignment**: Multi-tier alignment:
   - Exact Title Matching
   - Normalized & Fuzzy Title Matching
   - TF-IDF Cosine Similarity with configurable thresholds
   - Pluggable Sentence Transformers interface
4. **Entity and Threshold Tracking**: Pinpoints changes in critical numeric values:
   - CGPA thresholds (e.g. `7.0` -> `7.5`)
   - Currency amounts (e.g. `$5,000` -> `$6,500`, `$50` -> `$75`)
   - Calendar dates (e.g. `May 1, 2024` -> `June 15, 2024`)
   - Percentages (e.g. `75%` -> `80%`, `80%` -> `85%`)
   - Numerical thresholds (e.g. `15` -> `14` credit hours)
   - Durations & Age requirements
5. **Strict Evidence Verification**: Never marks a change as verified unless an aligned old/new evidence pair exists.
6. **Streamlit Web UI**: Interactive dashboard with side-by-side evidence inspection, inline visual diffs, and metric cards.
7. **Benchmark Evaluation**: Precision (91.7%), Recall (100.0%), and F1 (95.7%) against `gold_changes.json`.

---

## Project Structure
```text
policy-comparator/
├── app.py                     # Streamlit web application
├── demo.py                    # One-click CLI comparison demo
├── requirements.txt           # Project dependencies
├── README.md                  # System overview and usage guide
├── .vscode/
│   ├── settings.json          # VS Code test configuration
│   └── launch.json            # VS Code debug profiles (App, Demo, Tests, Eval)
├── src/
│   ├── __init__.py
│   ├── document_parser.py     # Document text ingestion (.txt, UTF-8/BOM/Latin-1)
│   ├── section_splitter.py   # Heuristic section boundary detection
│   ├── normalizer.py          # Text normalization preserving raw evidence
│   ├── aligner.py             # Multi-stage section alignment engine
│   ├── diff_engine.py         # difflib textual diffing & magnitude scoring
│   ├── entity_extractor.py    # Critical value and threshold change extractor
│   ├── change_classifier.py   # Rule-based category classifier
│   ├── comparator.py          # Central pipeline orchestrator
│   └── evaluator.py           # Precision, Recall, and F1 benchmark calculator
├── data/
│   ├── policy_v1.txt          # Sample policy document version 1
│   ├── policy_v2.txt          # Sample policy document version 2
│   └── gold_changes.json      # Evaluation benchmark dataset
└── tests/
    ├── __init__.py
    ├── test_document_parser.py
    ├── test_section_splitter.py
    └── test_comparator.py     # 10 required scenarios + evaluation test
```

---

## Quick Start in VS Code

### 1. Launch the Streamlit Web UI
```bash
streamlit run app.py
```
Or in VS Code: Press `F5` and select **"Python: Launch Streamlit App"**.

### 2. Run the Interactive CLI Demo
```bash
python demo.py
```

### 3. Run Benchmark Evaluation
```bash
python -m src.evaluator
```

### 4. Run All Unit Tests
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
Or open the **Testing** panel in VS Code to run all 29 tests with green checkmarks.
=======
# PolicyLens 2.0 — Enterprise AI Policy Comparator & Compliance Intelligence

> **Hackathon Problem Statement #20**: Intelligent policy document comparison, entity delta extraction, and strictness risk scoring.

---

## ⚡ Standout Hackathon Features

1. **1-Click Judge Demo Scenarios**:
   - 🏢 **Corporate HR & Hybrid Work Policy**: Evaluates probation shifts, attendance hurdles, and broadband stipend increments.
   - 🎓 **University Merit Scholarship Policy**: Detects GPA threshold hikes, tuition waiver grants, and grace period cancellations.
   - 💳 **Fintech Micro-Lending Terms**: Flags APR interest shifts, reduced grace periods, and mandatory binding arbitration waivers.
   - ☁️ **Enterprise Cloud SaaS TOS & Privacy**: Identifies telemetry AI model training clauses and shortened data retention windows.

2. **Semantic Category & Risk Severity Engine**:
   - Automatically tags clauses: `💰 Financial`, `⏳ Timeline`, `⚖️ Eligibility`, `🛡️ Legal & Governance`, `📋 Operational`.
   - Assigns severity scores: `🔴 High Risk`, `🟡 Medium Risk`, `🟢 Favorable`, `⚪ Low Risk`.
   - Computes global **Policy Volatility Index (0–100)** and **Strictness Verdict** (*Strictness Increased*, *Strictness Relaxed*, *Balanced*).

3. **Executive AI Briefing & Actionable Takeaways**:
   - Synthesizes top executive takeaways for compliance officers.
   - Identifies **Impacted Stakeholders** (Finance, HR, Legal, Applicants).
   - Generates immediate **Action Items** for operations teams.

4. **Multi-View Inspection Modes**:
   - 🔲 **Side-by-Side Clause Explorer**: Synchronized card pairs with inline word-level `<ins>` and `<del>` redlines and mathematical value shift pills (`₹500 ➔ ₹750 (+50.0%)`).
   - 📜 **Unified Legal Redline Stream**: Continuous legal redline markup.
   - 📊 **Structured Change Matrix**: Filterable, sortable compliance table.
   - 📈 **Numerical & Financial Delta Ledger**: Deep dive mathematical delta comparison for all currencies, percentages, dates, and durations.

5. **Power Tools & Compliance Audit Export**:
   - Instant real-time text search and multi-tag filtering chips.
   - **Download CSV Audit Report** for spreadsheet workflows.
   - **Executive Print / PDF Export** with clean styling.
   - Dual Input: Drag-and-drop file upload (`.pdf`, `.txt`, `.md`, `.json`) OR direct split-screen text editor.

---

## 🚀 Quickstart

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Run Flask App
python app.py
```

Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

>>>>>>> 3af9f2c5ed86752afa496b0c8d8b47d938169d03
