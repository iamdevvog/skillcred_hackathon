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

