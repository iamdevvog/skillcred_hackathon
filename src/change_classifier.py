"""
Change classification module for categorizing policy modifications into business categories.

Supports:
- eligibility
- deadline
- fee
- amount
- procedure
- definition
- requirement
- penalty
- duration
- other

Designed with a modular abstract base class so an ML or LLM-based classifier can effortlessly replace or augment the rule-based engine.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Set
from src.entity_extractor import EntityChange


class BaseChangeClassifier(ABC):
    """Abstract interface for policy change classification."""

    @abstractmethod
    def classify(self, section_title: str, text: str, entities_changed: List[EntityChange]) -> str:
        """Assign category string given section context and detected changes."""
        pass


class RuleBasedChangeClassifier(BaseChangeClassifier):
    """Rule-based heuristic classifier using weighted keywords and detected entity types."""

    CATEGORY_KEYWORDS: Dict[str, Set[str]] = {
        "penalty": {
            "penalty", "disqualification", "probation", "sanction", "disciplinary",
            "revoke", "revocation", "terminated", "void", "repayment", "violation"
        },
        "fee": {
            "fee", "charge", "late fee", "registration fee", "tuition", "cost", "reimbursement"
        },
        "deadline": {
            "deadline", "due date", "submission window", "due by", "late submission", "cutoff"
        },
        "amount": {
            "amount", "limits", "award limits", "grant", "maximum award", "funding",
            "ceiling", "allowance", "budget", "sum"
        },
        "eligibility": {
            "eligibility", "qualify", "eligible", "qualification", "cgpa", "gpa",
            "matriculated", "age limit", "criteria", "scholarship renewal", "continuation"
        },
        "procedure": {
            "procedure", "process", "appeal", "appeals", "grievance", "disbursement",
            "steps", "inquiry", "contact", "portal", "schedule"
        },
        "definition": {
            "purpose", "scope", "definition", "definitions", "meaning", "preamble",
            "background", "overview"
        },
        "requirement": {
            "requirement", "credit load", "credits", "mandatory", "prerequisite",
            "work-study", "obliged", "maintain", "attendance"
        },
        "duration": {
            "duration", "period", "tenure", "term", "academic year", "semester"
        },
    }

    # Hierarchy priority when multiple categories match
    CATEGORY_PRIORITY = [
        "penalty",
        "fee",
        "deadline",
        "amount",
        "eligibility",
        "requirement",
        "procedure",
        "definition",
        "duration",
    ]

    def classify(self, section_title: str, text: str, entities_changed: List[EntityChange]) -> str:
        """
        Classify change into one of the designated categories.

        Args:
            section_title: Title of the section.
            text: Relevant section text.
            entities_changed: Entities detected as modified or added.

        Returns:
            One of the valid category names or 'other'.
        """
        # Lowercase search content
        title_lower = section_title.lower() if section_title else ""
        content_lower = (text or "").lower()
        combined_text = f"{title_lower} {content_lower}"

        # 1. Check title matches first (highest weight)
        for cat in self.CATEGORY_PRIORITY:
            keywords = self.CATEGORY_KEYWORDS[cat]
            if any(kw in title_lower for kw in keywords):
                return cat

        # 2. Check entity change types
        for ec in entities_changed:
            if ec.entity == "CGPA":
                return "eligibility"
            if ec.entity == "currency" and any(w in combined_text for w in ["fee", "late"]):
                return "fee"
            if ec.entity == "currency":
                return "amount"
            if ec.entity == "date" and any(w in combined_text for w in ["deadline", "due", "submit"]):
                return "deadline"
            if ec.entity == "age":
                return "eligibility"

        # 3. Check body text keyword matches
        scores: Dict[str, int] = {cat: 0 for cat in self.CATEGORY_PRIORITY}
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in combined_text:
                    scores[cat] += 1

        best_cat = max(scores, key=lambda c: scores[c])
        if scores[best_cat] > 0:
            return best_cat

        return "other"
