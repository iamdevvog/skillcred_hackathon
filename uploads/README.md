# PolicyLens — Policy Document Comparison System

MVP for hackathon problem statement #20.

## Features
- Upload two PDF/TXT policy versions
- Extract text
- Split into sections
- Align related sections
- Detect Added / Removed / Modified text
- Extract important values: percentages, money, durations and dates
- Generate evidence-backed change summaries
- Side-by-side comparison dashboard

## Run
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Demo
Create two small TXT files first:
Old:
Students with 60% or above are eligible.
Application fee is ₹500.
Deadline is 15 September.

New:
Students with 65% or above are eligible.
Application fee is ₹750.
Deadline is 30 September.

Upload them and click Compare Documents.

## Next upgrades
1. Replace SequenceMatcher with sentence-transformers embeddings.
2. Add DOCX support.
3. Add an LLM only after evidence alignment, for concise impact wording.
4. Add change categories: eligibility, deadline, fee, procedure, definition.
5. Add export to PDF/CSV.
