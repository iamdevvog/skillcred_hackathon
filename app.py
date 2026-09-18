from flask import Flask, render_template, request, jsonify, Response
from werkzeug.utils import secure_filename
import os, re, difflib, io, csv
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

app = Flask(__name__)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED = {".txt", ".pdf", ".md", ".json"}

# ----------------------------------------------------------------------
# PRESET SAMPLE POLICIES
# ----------------------------------------------------------------------
PRESETS = {
    "hr_policy": {
        "id": "hr_policy",
        "title": "Corporate HR & Hybrid Work Policy",
        "subtitle": "v1.0 (2025) vs v2.0 (2026) — Probation, WFH allowances & approval cycles",
        "category": "Corporate HR",
        "old_title": "HR Policy 2025 v1.0",
        "new_title": "HR Policy 2026 v2.0",
        "old_text": """COMPANY EMPLOYEE BENEFITS & WORKPLACE POLICY
Version 1.0 — Effective January 2025

1. Eligibility & Probation
Employees who have completed 30 days of continuous service are eligible to apply for company wellness and health benefits. Employees must maintain an attendance record of at least 80% to retain benefit eligibility.

2. Application & Processing Fee
The annual benefit enrollment administration fee is ₹500, deducted from the employee's payroll.

3. Submission Timeline & Deadlines
Applications for annual benefits must be submitted by 15 September 2025. Late submissions will incur a ₹250 penalty.

4. Remote & Hybrid Work Guidelines
Eligible team members may work remotely for up to 2 days per week with direct manager approval. Core working hours are 10:00 AM to 5:00 PM.

5. Required Verification Documents
Employees must submit a valid Government ID, employee badge number, and personal bank account details.

6. Approval & Processing Turnaround
The HR Operations team reviews and processes benefit applications within 5 working days from submission.

7. Travel & Equipment Reimbursement
Employees are eligible for a monthly home-office broadband stipend of ₹1,000 upon submitting paid receipts.""",
        "new_text": """COMPANY EMPLOYEE BENEFITS & WORKPLACE POLICY
Version 2.0 — Effective January 2026

1. Eligibility & Probation
Employees who have completed 60 days of continuous service are eligible to apply for company wellness and health benefits. Employees must maintain an attendance record of at least 85% to retain benefit eligibility.

2. Application & Processing Fee
The annual benefit enrollment administration fee is ₹750, deducted from the employee's payroll.

3. Submission Timeline & Deadlines
Applications for annual benefits must be submitted by 30 September 2026. Late submissions will incur a ₹500 penalty.

4. Remote & Hybrid Work Guidelines
Eligible team members may work remotely for up to 3 days per week with direct manager approval. Core working hours are 10:00 AM to 4:00 PM.

5. Required Verification Documents
Employees must submit a valid Government ID, employee badge number, personal bank account details, and verified proof of home address.

6. Approval & Processing Turnaround
The HR Operations team reviews and processes benefit applications within 7 working days from submission.

7. Travel & Equipment Reimbursement
Employees are eligible for a monthly home-office broadband stipend of ₹1,500 upon submitting paid receipts.

8. Digital Identity & Biometric Verification
All applicants must complete biometric or two-factor digital identity verification via the HR portal before any policy benefit disbursement can be finalized."""
    },
    "scholarship": {
        "id": "scholarship",
        "title": "University Merit Scholarship & Tuition Policy",
        "subtitle": "Academic Year 2025 vs 2026 — Minimum GPA, tuition waivers & application window",
        "category": "Higher Education",
        "old_title": "Scholarship Guidelines 2025",
        "new_title": "Scholarship Guidelines 2026",
        "old_text": """NATIONAL UNIVERSITY MERIT SCHOLARSHIP POLICY
Academic Regulation Series 2025

1. Academic Eligibility Criteria
Undergraduate applicants must have achieved a cumulative GPA of 3.2 or an aggregate score of 70% in previous semesters. Full-time enrollment of at least 12 credit units is required.

2. Scholarship Grant & Financial Award
Recipients receive a tuition fee waiver of $2,500 per academic semester and a textbook grant of $300.

3. Application Deadlines & Grace Periods
The online portal opens on 1 June and all final applications must be submitted before 15 July 2025. A grace period of 7 days is permitted with dean recommendation.

4. Community Service Obligation
Scholars are obligated to complete 20 hours of approved campus community service per semester.

5. Renewal & Maintenance Standards
To maintain scholarship standing across academic years, the student must maintain a minimum 3.0 GPA without academic probation.""",
        "new_text": """NATIONAL UNIVERSITY MERIT SCHOLARSHIP POLICY
Academic Regulation Series 2026

1. Academic Eligibility Criteria
Undergraduate applicants must have achieved a cumulative GPA of 3.6 or an aggregate score of 80% in previous semesters. Full-time enrollment of at least 15 credit units is required.

2. Scholarship Grant & Financial Award
Recipients receive a tuition fee waiver of $3,500 per academic semester and an enhanced textbook stipend of $500.

3. Application Deadlines & Grace Periods
The online portal opens on 1 June and all final applications must be submitted strictly before 1 August 2026. No grace period extensions will be granted.

4. Community Service Obligation
Scholars are obligated to complete 35 hours of approved campus community service per semester.

5. Renewal & Maintenance Standards
To maintain scholarship standing across academic years, the student must maintain a minimum 3.4 GPA without academic probation.

6. Mandatory Research Assistantship
Scholars in their junior or senior year must commit 5 hours per week to departmental research laboratories."""
    },
    "fintech_loan": {
        "id": "fintech_loan",
        "title": "Consumer Loan & Credit Agreement",
        "subtitle": "Terms v3.4 vs v4.0 — APR interest shifts, grace periods, penalty clauses & arbitration",
        "category": "Fintech & Banking",
        "old_title": "Lending Terms v3.4",
        "new_title": "Lending Terms v4.0",
        "old_text": """NEXUS FINANCIAL CONSUMER LENDING AGREEMENT
Standard Terms & Disclosure — Revision 3.4

1. Annual Percentage Rate & Financing Cost
The standard annual percentage rate (APR) is fixed at 14.5% for Tier-1 prime borrowers. Origination fee is $75 charged upon loan disbursement.

2. Repayment Schedule & Grace Period
Borrowers must make monthly installment payments by the 5th calendar day of each month. A grace period of 10 days is provided before late fees are assessed.

3. Default Fees & Delinquency Charges
If an installment is not received prior to expiration of the grace period, a late fee of $25 or 2.0% of the overdue balance (whichever is lesser) will be applied.

4. Prepayment Penalties
Borrowers may prepay their loan principal at any time without incurring any prepayment penalties or closing fees.

5. Dispute Resolution & Governing Law
Any legal claims or controversies arising out of this agreement shall be submitted to the state courts of Delaware.""",
        "new_text": """NEXUS FINANCIAL CONSUMER LENDING AGREEMENT
Standard Terms & Disclosure — Revision 4.0

1. Annual Percentage Rate & Financing Cost
The standard annual percentage rate (APR) is adjusted to 18.9% for Tier-1 prime borrowers. Origination fee is increased to $150 charged upon loan disbursement.

2. Repayment Schedule & Grace Period
Borrowers must make monthly installment payments by the 1st calendar day of each month. A grace period of 5 days is provided before late fees are assessed.

3. Default Fees & Delinquency Charges
If an installment is not received prior to expiration of the grace period, a late fee of $60 or 5.0% of the overdue balance (whichever is greater) will be applied.

4. Prepayment Penalties
Early loan settlement within the first 6 months of issuance will be subject to an administrative prepayment fee of $100.

5. Dispute Resolution & Mandatory Binding Arbitration
All disputes, claims, and controversies arising under this agreement must be resolved exclusively through mandatory individual binding arbitration under AAA rules, waiving class action rights."""
    },
    "saas_privacy": {
        "id": "saas_privacy",
        "title": "Enterprise Cloud SaaS Terms & Privacy",
        "subtitle": "2024 vs 2026 — AI model training, data retention window & liability caps",
        "category": "Cloud & Privacy",
        "old_title": "SaaS Terms 2024",
        "new_title": "SaaS Terms 2026",
        "old_text": """CLOUDSPHERE ENTERPRISE TERMS OF SERVICE
Master Subscription Agreement 2024

1. Data Retention & Archival Timeline
Customer data stored in active cloud instances is retained for 90 days following contract termination or account expiration before irreversible purging.

2. Service Level Commitment & Uptime SLA
CloudSphere commits to maintaining a monthly service availability uptime of 99.5%. Downtime exceeding this threshold entitles the customer to a 10% billing credit.

3. Intellectual Property & Data Ownership
Customer retains all proprietary ownership rights in customer data uploaded to the service. CloudSphere will not access customer confidential content without prior written authorization.

4. Limitation of Liability
The aggregate liability of either party arising out of or related to this agreement shall not exceed the total fees paid by customer in the preceding 12 months, capped at $50,000.""",
        "new_text": """CLOUDSPHERE ENTERPRISE TERMS OF SERVICE
Master Subscription Agreement 2026

1. Data Retention & Archival Timeline
Customer data stored in active cloud instances is retained for 30 days following contract termination or account expiration before irreversible purging.

2. Service Level Commitment & Uptime SLA
CloudSphere commits to maintaining a monthly service availability uptime of 99.9%. Downtime exceeding this threshold entitles the customer to a 20% billing credit.

3. Intellectual Property, AI Training & Telemetry
Customer retains proprietary ownership of uploaded customer data. CloudSphere may use de-identified, aggregated customer telemetry and usage queries to train and refine machine learning models unless Customer explicitly submits an enterprise opt-out form.

4. Limitation of Liability
The aggregate liability of either party arising out of or related to this agreement shall not exceed the total fees paid by customer in the preceding 12 months, capped at $250,000.

5. Security Incident Notification
In the event of a confirmed security incident affecting customer data, CloudSphere will notify customer administrative contacts within 24 hours of confirmation."""
    }
}

# ----------------------------------------------------------------------
# TEXT EXTRACTION & NORMALIZATION
# ----------------------------------------------------------------------
def extract_text(path):
    suffix = Path(path).suffix.lower()
    if suffix in {".txt", ".md", ".json"}:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        if pdfplumber is None:
            raise RuntimeError("PDF support requires pdfplumber. Please run: pip install -r requirements.txt")
        with pdfplumber.open(path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(pages)
    raise ValueError("Supported formats: .pdf, .txt, .md, .json")

def clean(text):
    if not text:
        return ""
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def split_sections(text):
    pattern = r"\n(?=(?:(?:Section|Article|Clause|Part)\s+\d+(?:\.\d+)*[:.]?|\d+(?:\.\d+)*[.)]\s+|[A-Z0-9\s/&,-]{4,}:))"
    parts = re.split(pattern, text, flags=re.IGNORECASE)
    sections = []
    
    for i, p in enumerate(parts):
        p = p.strip()
        if not p:
            continue
        lines = [line.strip() for line in p.splitlines() if line.strip()]
        if not lines:
            continue
        raw_title = lines[0]
        title = raw_title[:90].strip()
        if len(raw_title) > 90:
            title += "…"
        sections.append({
            "id": i,
            "title": title,
            "text": p,
            "lines": lines
        })
        
    if len(sections) < 2:
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        sections = [{
            "id": i,
            "title": f"Clause {i+1}: " + (paras[i].splitlines()[0][:70] if paras[i].splitlines() else f"Section {i+1}"),
            "text": paras[i],
            "lines": [l.strip() for l in paras[i].splitlines() if l.strip()]
        } for i in range(len(paras))]
        
    return sections

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def extract_values(text):
    if not text:
        return []
        
    patterns = {
        "percentage": r"\b\d+(?:\.\d+)?\s?%",
        "money": r"(?:₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)\s?[\d,]+(?:\.\d+)?",
        "duration": r"\b\d+(?:\.\d+)?\s+(?:minute|minutes|hour|hours|day|days|working day|working days|week|weeks|month|months|year|years)\b",
        "date": r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{2,4}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{4}-\d{2}-\d{2})\b",
        "score_or_gpa": r"\b(?:GPA|CGPA|score|grade)\s+(?:of\s+)?(?:\d+(?:\.\d+)?)\b|\b\d+\.\d+\s+(?:GPA|CGPA)\b",
        "credit_or_hours": r"\b\d+\s+(?:credits?|credit units?|hours?|hrs?)\b"
    }
    
    found = []
    seen = set()
    for kind, pattern in patterns.items():
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            val = match.group(0).strip()
            key = (kind, val.lower())
            if key not in seen:
                seen.add(key)
                found.append({
                    "type": kind,
                    "value": val,
                    "raw_num": parse_numeric(val)
                })
    return found

def parse_numeric(val_str):
    cleaned = re.sub(r"[^\d.]", "", val_str.replace(",", ""))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

def compute_value_deltas(old_values, new_values):
    deltas = []
    old_by_type = {}
    for v in old_values:
        old_by_type.setdefault(v["type"], []).append(v)
        
    new_by_type = {}
    for v in new_values:
        new_by_type.setdefault(v["type"], []).append(v)
        
    all_types = set(old_by_type.keys()).union(set(new_by_type.keys()))
    
    for vtype in all_types:
        olds = old_by_type.get(vtype, [])
        news = new_by_type.get(vtype, [])
        
        max_len = max(len(olds), len(news))
        for i in range(max_len):
            old_item = olds[i] if i < len(olds) else None
            new_item = news[i] if i < len(news) else None
            
            if old_item and new_item:
                if old_item["value"] != new_item["value"]:
                    pct_str = ""
                    direction = "changed"
                    if old_item["raw_num"] is not None and new_item["raw_num"] is not None and old_item["raw_num"] > 0:
                        diff = new_item["raw_num"] - old_item["raw_num"]
                        pct = (diff / old_item["raw_num"]) * 100
                        direction = "increased" if diff > 0 else "decreased"
                        pct_str = f" ({'+' if diff > 0 else ''}{pct:.1f}%)"
                        
                    deltas.append({
                        "type": vtype,
                        "old": old_item["value"],
                        "new": new_item["value"],
                        "direction": direction,
                        "pct_change": pct_str,
                        "description": f"{old_item['value']} ➔ {new_item['value']}{pct_str}"
                    })
            elif old_item and not new_item:
                deltas.append({
                    "type": vtype,
                    "old": old_item["value"],
                    "new": None,
                    "direction": "removed",
                    "pct_change": "",
                    "description": f"Removed: {old_item['value']}"
                })
            elif new_item and not old_item:
                deltas.append({
                    "type": vtype,
                    "old": None,
                    "new": new_item["value"],
                    "direction": "added",
                    "pct_change": "",
                    "description": f"New value: {new_item['value']}"
                })
                
    return deltas

# ----------------------------------------------------------------------
# CATEGORIZATION & PLAIN-ENGLISH SUMMARIES
# ----------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "Financial": ["fee", "fees", "cost", "salary", "stipend", "reimbursement", "price", "charge", "charges", "penalty", "penalties", "interest", "apr", "deposit", "allowance", "waiver", "tuition", "payroll", "deducted", "currency", "₹", "$", "eur", "gbp", "inr", "usd", "monetary", "award", "grant"],
    "Timeline": ["deadline", "deadlines", "date", "dates", "duration", "day", "days", "working days", "month", "months", "year", "years", "hour", "hours", "notice period", "expiry", "expiration", "grace period", "schedule", "effective", "turnaround", "timeframe", "calendar", "timeline"],
    "Eligibility": ["eligibility", "eligible", "criteria", "requirement", "requirements", "qualification", "qualifications", "gpa", "cgpa", "attendance", "prerequisite", "score", "grade", "probation", "minimum", "maximum", "threshold", "mandatory", "obligated", "obligation", "enrollment"],
    "Legal & Governance": ["liability", "indemnity", "arbitration", "jurisdiction", "dispute", "claims", "governing law", "breach", "termination", "compliance", "privacy", "gdpr", "intellectual property", "ownership", "confidential", "security incident", "telemetry", "consent", "opt-out", "binding"],
    "Operational": ["procedure", "process", "processing", "document", "documents", "submission", "submit", "portal", "approval", "review", "manager", "workflow", "verification", "biometric", "identity", "form", "guidelines", "upload", "badge", "id"]
}

def classify_category(title, old_text, new_text):
    combined = f"{title} {old_text} {new_text}".lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(combined.count(kw) for kw in keywords)
        scores[cat] = score
        
    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        return "Operational"
    return best_cat

def analyze_risk_and_strictness(category, change_type, old_text, new_text, deltas):
    if change_type == "Unchanged":
        return {"level": "None", "badge": "Unchanged", "score": 0, "sentiment": "neutral", "reason": "No changes in this section."}
        
    combined = f"{old_text} {new_text}".lower()
    
    # Check for favorable indicators
    for delta in deltas:
        if delta["type"] == "money" and any(k in combined for k in ["waiver", "stipend", "grant", "reimbursement", "allowance"]) and delta["direction"] == "increased":
            return {"level": "Favorable", "badge": "Favorable Shift", "score": -10, "sentiment": "favorable", "reason": f"Allowance / benefit increased: {delta['description']}"}
        if delta["type"] == "duration" and "remote" in combined and delta["direction"] == "increased":
            return {"level": "Favorable", "badge": "Favorable Shift", "score": -10, "sentiment": "favorable", "reason": f"Remote work flexibility expanded: {delta['description']}"}
            
    # Check for high impact / strict conditions
    if "arbitration" in new_text.lower() and "arbitration" not in old_text.lower():
        return {"level": "High", "badge": "High Impact", "score": 85, "sentiment": "restrictive", "reason": "Mandatory arbitration clause added."}
        
    if "ai training" in new_text.lower() or "telemetry" in new_text.lower():
        return {"level": "High", "badge": "High Impact", "score": 75, "sentiment": "restrictive", "reason": "Data usage for AI model training introduced."}
        
    for delta in deltas:
        if delta["type"] == "money" and delta["direction"] == "increased" and any(k in combined for k in ["fee", "penalty", "apr", "cost", "rate", "origination"]):
            return {"level": "High", "badge": "High Impact", "score": 80, "sentiment": "restrictive", "reason": f"Cost or penalty increased: {delta['description']}"}
        if delta["type"] == "duration" and delta["direction"] == "decreased" and any(k in combined for k in ["grace period", "retention", "deadline", "turnaround"]):
            return {"level": "High", "badge": "High Impact", "score": 70, "sentiment": "restrictive", "reason": f"Timeline or grace period shortened: {delta['description']}"}
        if delta["type"] in {"percentage", "score_or_gpa", "duration"} and delta["direction"] == "increased" and any(k in combined for k in ["attendance", "gpa", "probation", "service", "community service"]):
            return {"level": "High", "badge": "High Impact", "score": 65, "sentiment": "restrictive", "reason": f"Eligibility requirement tightened: {delta['description']}"}
            
    if change_type == "Removed" and category in {"Legal & Governance", "Financial"}:
        return {"level": "High", "badge": "High Impact", "score": 75, "sentiment": "restrictive", "reason": f"Previous {category} section was removed."}
        
    if change_type == "Added":
        return {"level": "Medium", "badge": "New Section", "score": 50, "sentiment": "neutral", "reason": f"New section added to the policy."}
        
    if category in {"Financial", "Timeline", "Eligibility"}:
        return {"level": "Medium", "badge": "Moderate Change", "score": 45, "sentiment": "neutral", "reason": f"{category} details modified."}
        
    return {"level": "Low", "badge": "Editorial Update", "score": 20, "sentiment": "neutral", "reason": "Wording update without major parameter shifts."}

# ----------------------------------------------------------------------
# WORD-LEVEL VISUAL REDLINE ENGINE
# ----------------------------------------------------------------------
def generate_token_diff(old_text, new_text):
    old_words = re.findall(r"\S+|\n", old_text)
    new_words = re.findall(r"\S+|\n", new_text)
    
    sm = difflib.SequenceMatcher(None, old_words, new_words)
    old_html_parts = []
    new_html_parts = []
    unified_html_parts = []
    
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            chunk_old = " ".join(old_words[i1:i2]).replace("\n ", "\n").replace(" \n", "\n")
            chunk_new = " ".join(new_words[j1:j2]).replace("\n ", "\n").replace(" \n", "\n")
            old_html_parts.append(escape_html(chunk_old))
            new_html_parts.append(escape_html(chunk_new))
            unified_html_parts.append(escape_html(chunk_old))
        elif tag == "replace":
            old_chunk = " ".join(old_words[i1:i2]).replace("\n ", "\n").replace(" \n", "\n")
            new_chunk = " ".join(new_words[j1:j2]).replace("\n ", "\n").replace(" \n", "\n")
            old_html_parts.append(f'<del class="diff-del">{escape_html(old_chunk)}</del>')
            new_html_parts.append(f'<ins class="diff-ins">{escape_html(new_chunk)}</ins>')
            unified_html_parts.append(f'<del class="diff-del">{escape_html(old_chunk)}</del> <ins class="diff-ins">{escape_html(new_chunk)}</ins>')
        elif tag == "delete":
            old_chunk = " ".join(old_words[i1:i2]).replace("\n ", "\n").replace(" \n", "\n")
            old_html_parts.append(f'<del class="diff-del">{escape_html(old_chunk)}</del>')
            unified_html_parts.append(f'<del class="diff-del">{escape_html(old_chunk)}</del>')
        elif tag == "insert":
            new_chunk = " ".join(new_words[j1:j2]).replace("\n ", "\n").replace(" \n", "\n")
            new_html_parts.append(f'<ins class="diff-ins">{escape_html(new_chunk)}</ins>')
            unified_html_parts.append(f'<ins class="diff-ins">{escape_html(new_chunk)}</ins>')
            
    return {
        "old_html": " ".join(old_html_parts).replace("\n ", "\n"),
        "new_html": " ".join(new_html_parts).replace("\n ", "\n"),
        "unified_html": " ".join(unified_html_parts).replace("\n ", "\n")
    }

def escape_html(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#039;"))

# ----------------------------------------------------------------------
# SECTION ALIGNMENT & CHANGE SYNTHESIS
# ----------------------------------------------------------------------
def similarity(a, b):
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

def align_sections(old_sections, new_sections):
    pairs = []
    used_new = set()
    
    for o in old_sections:
        best = None
        best_score = 0
        for n in new_sections:
            if n["id"] in used_new:
                continue
            title_score = similarity(o["title"], n["title"])
            content_score = similarity(o["text"][:600], n["text"][:600])
            combined_score = 0.65 * title_score + 0.35 * content_score
            
            if combined_score > best_score:
                best_score = combined_score
                best = n
                
        if best and best_score >= 0.32:
            used_new.add(best["id"])
            pairs.append((o, best, best_score))
        else:
            pairs.append((o, None, 0))
            
    for n in new_sections:
        if n["id"] not in used_new:
            pairs.append((None, n, 0))
            
    return pairs

def synthesize_summary(change_type, category, deltas, old_text, new_text):
    if deltas:
        delta_descs = [d["description"] for d in deltas if d.get("description")]
        if delta_descs:
            return f"Values changed: {'; '.join(delta_descs)}."
            
    if change_type == "Added":
        return f"New section added to the revised policy."
    if change_type == "Removed":
        return f"This section was removed in the revised policy."
    if change_type == "Modified":
        return f"Text was updated between the two versions."
    return "No substantive changes found."

# ----------------------------------------------------------------------
# EXECUTIVE SUMMARY
# ----------------------------------------------------------------------
def generate_executive_briefing(section_results, all_deltas, summary_counts):
    takeaways = []
    
    high_impact = [s for s in section_results if s["risk"]["level"] == "High"]
    favorable = [s for s in section_results if s["risk"]["level"] == "Favorable"]
    moderate = [s for s in section_results if s["risk"]["level"] == "Medium" and s["deltas"]]
    
    for item in high_impact:
        takeaways.append({
            "title": item["display_title"],
            "badge": "High Impact",
            "type": "high",
            "category": item["category"],
            "summary": item["summary"]
        })
        
    for item in favorable:
        takeaways.append({
            "title": item["display_title"],
            "badge": "Favorable",
            "type": "favorable",
            "category": item["category"],
            "summary": item["summary"]
        })

    for item in moderate:
        takeaways.append({
            "title": item["display_title"],
            "badge": "Updated",
            "type": "moderate",
            "category": item["category"],
            "summary": item["summary"]
        })

    return {
        "takeaways": takeaways[:6],
        "total_sections": len(section_results),
        "total_changes": summary_counts["total_changes"]
    }

# ----------------------------------------------------------------------
# ROUTES & CONTROLLERS
# ----------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/presets")
def get_presets():
    return jsonify(PRESETS)

@app.post("/compare")
def compare():
    old_text = ""
    new_text = ""
    old_filename = "Document_v1"
    new_filename = "Document_v2"
    
    if request.is_json:
        data = request.get_json()
        old_text = data.get("old_text", "")
        new_text = data.get("new_text", "")
        old_filename = data.get("old_filename", "Original Version")
        new_filename = data.get("new_filename", "Revised Version")
    else:
        old_file = request.files.get("old_file")
        new_file = request.files.get("new_file")
        raw_old = request.form.get("raw_old_text")
        raw_new = request.form.get("raw_new_text")
        
        if raw_old and raw_new:
            old_text = raw_old
            new_text = raw_new
            old_filename = request.form.get("old_title", "Original Version")
            new_filename = request.form.get("new_title", "Revised Version")
        elif old_file and new_file:
            old_filename = old_file.filename
            new_filename = new_file.filename
            
            old_path = UPLOAD_DIR / secure_filename(old_file.filename)
            new_path = UPLOAD_DIR / secure_filename(new_file.filename)
            old_file.save(old_path)
            new_file.save(new_path)
            
            try:
                old_text = extract_text(old_path)
                new_text = extract_text(new_path)
            except Exception as e:
                return jsonify({"error": str(e)}), 400
        else:
            return jsonify({"error": "Please provide both the original and revised policy documents."}), 400

    old_text = clean(old_text)
    new_text = clean(new_text)
    
    if not old_text or not new_text:
        return jsonify({"error": "One or both documents are empty. Please check your files or text."}), 400

    old_sections = split_sections(old_text)
    new_sections = split_sections(new_text)
    
    pairs = align_sections(old_sections, new_sections)
    section_results = []
    all_deltas = []
    
    summary_counts = {
        "total_sections": len(pairs),
        "total_changes": 0,
        "modified": 0,
        "added": 0,
        "removed": 0,
        "unchanged": 0,
        "high_risk": 0,
        "favorable": 0
    }

    for i, (old_sec, new_sec, score) in enumerate(pairs):
        sec_id = f"sec_{i+1}"
        
        if old_sec and new_sec:
            is_same = (old_sec["text"].strip() == new_sec["text"].strip())
            status = "Unchanged" if is_same else "Modified"
            title = new_sec["title"] if new_sec["title"] != "—" else old_sec["title"]
            category = classify_category(title, old_sec["text"], new_sec["text"])
            
            old_vals = extract_values(old_sec["text"])
            new_vals = extract_values(new_sec["text"])
            deltas = compute_value_deltas(old_vals, new_vals) if not is_same else []
            all_deltas.extend(deltas)
            
            risk = analyze_risk_and_strictness(category, status, old_sec["text"], new_sec["text"], deltas)
            diff_html = generate_token_diff(old_sec["text"], new_sec["text"]) if not is_same else {
                "old_html": escape_html(old_sec["text"]),
                "new_html": escape_html(new_sec["text"]),
                "unified_html": escape_html(new_sec["text"])
            }
            
            summary_desc = synthesize_summary(status, category, deltas, old_sec["text"], new_sec["text"])
            
            if status == "Modified":
                summary_counts["modified"] += 1
                summary_counts["total_changes"] += 1
            else:
                summary_counts["unchanged"] += 1
                
            if risk["level"] == "High":
                summary_counts["high_risk"] += 1
            elif risk["level"] == "Favorable":
                summary_counts["favorable"] += 1

            section_results.append({
                "id": sec_id,
                "title_old": old_sec["title"],
                "title_new": new_sec["title"],
                "display_title": title,
                "category": category,
                "similarity": round(score * 100),
                "status": status,
                "risk": risk,
                "old_text": old_sec["text"],
                "new_text": new_sec["text"],
                "diff_html": diff_html,
                "deltas": deltas,
                "summary": summary_desc
            })

        elif old_sec:
            status = "Removed"
            category = classify_category(old_sec["title"], old_sec["text"], "")
            old_vals = extract_values(old_sec["text"])
            deltas = compute_value_deltas(old_vals, [])
            all_deltas.extend(deltas)
            risk = analyze_risk_and_strictness(category, status, old_sec["text"], "", deltas)
            diff_html = {
                "old_html": f'<del class="diff-del">{escape_html(old_sec["text"])}</del>',
                "new_html": '<span class="diff-empty">— Section Removed from Revised Policy —</span>',
                "unified_html": f'<del class="diff-del">{escape_html(old_sec["text"])}</del>'
            }
            summary_desc = synthesize_summary(status, category, deltas, old_sec["text"], "")
            
            summary_counts["removed"] += 1
            summary_counts["total_changes"] += 1
            if risk["level"] == "High":
                summary_counts["high_risk"] += 1
                
            section_results.append({
                "id": sec_id,
                "title_old": old_sec["title"],
                "title_new": "—",
                "display_title": old_sec["title"],
                "category": category,
                "similarity": 0,
                "status": status,
                "risk": risk,
                "old_text": old_sec["text"],
                "new_text": "",
                "diff_html": diff_html,
                "deltas": deltas,
                "summary": summary_desc
            })

        elif new_sec:
            status = "Added"
            category = classify_category(new_sec["title"], "", new_sec["text"])
            new_vals = extract_values(new_sec["text"])
            deltas = compute_value_deltas([], new_vals)
            all_deltas.extend(deltas)
            risk = analyze_risk_and_strictness(category, status, "", new_sec["text"], deltas)
            diff_html = {
                "old_html": '<span class="diff-empty">— Section Added in Revised Policy —</span>',
                "new_html": f'<ins class="diff-ins">{escape_html(new_sec["text"])}</ins>',
                "unified_html": f'<ins class="diff-ins">{escape_html(new_sec["text"])}</ins>'
            }
            summary_desc = synthesize_summary(status, category, deltas, "", new_sec["text"])
            
            summary_counts["added"] += 1
            summary_counts["total_changes"] += 1
            if risk["level"] == "High":
                summary_counts["high_risk"] += 1
                
            section_results.append({
                "id": sec_id,
                "title_old": "—",
                "title_new": new_sec["title"],
                "display_title": new_sec["title"],
                "category": category,
                "similarity": 0,
                "status": status,
                "risk": risk,
                "old_text": "",
                "new_text": new_sec["text"],
                "diff_html": diff_html,
                "deltas": deltas,
                "summary": summary_desc
            })

    briefing = generate_executive_briefing(section_results, all_deltas, summary_counts)

    return jsonify({
        "old_filename": old_filename,
        "new_filename": new_filename,
        "summary": summary_counts,
        "executive_briefing": briefing,
        "sections": section_results,
        "all_deltas": all_deltas
    })

@app.post("/api/export/csv")
def export_csv():
    data = request.get_json()
    if not data or "sections" not in data:
        return jsonify({"error": "Invalid report payload."}), 400
        
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Section", "Category", "Status", "Change Summary", "Original Text", "Revised Text"])
    
    for sec in data["sections"]:
        writer.writerow([
            sec.get("display_title", sec.get("title_new", "")),
            sec.get("category", ""),
            sec.get("status", ""),
            sec.get("summary", ""),
            sec.get("old_text", "").replace("\n", " "),
            sec.get("new_text", "").replace("\n", " ")
        ])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=Policy_Comparison_Report.csv"}
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
