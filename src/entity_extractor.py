"""
Entity extractor module for detecting and comparing critical values and thresholds.

Supports regex-based extraction of:
- CGPA / GPA values (e.g., 7.0 vs 7.5)
- Currency figures (e.g., $5,000 vs $6,500)
- Percentages (e.g., 75% vs 80%)
- Calendar dates (e.g., May 1, 2024 vs June 15, 2024)
- Age thresholds (e.g., 25 years vs 26 years)
- Durations (e.g., 14 days, 10 hours)
- Numerical limits and credit thresholds (e.g., 15 credits vs 14 credits)
"""

from dataclasses import dataclass, asdict
import re
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class ExtractedEntity:
    """An individual value extracted from text."""
    category: str       # "CGPA", "currency", "percentage", "date", "age", "duration", "number"
    raw_value: str      # e.g., "$5,000", "7.5", "June 15, 2024"
    span: Tuple[int, int]
    context_hint: str   # Words surrounding the entity for alignment matching


@dataclass
class EntityChange:
    """
    Comparison record for an entity between old and new text.

    Attributes:
        entity: Type of entity (e.g., "CGPA", "currency", "date").
        old_value: Value in version 1 (or None if newly introduced).
        new_value: Value in version 2 (or None if eliminated).
        context: Brief context describing the value.
    """
    entity: str
    old_value: Optional[str]
    new_value: Optional[str]
    context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity": self.entity,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


class EntityExtractor:
    """Extracts policy values and detects changes across aligned texts."""

    MONTHS = (
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
    )

    PATTERNS = {
        # CGPA / GPA: matches "CGPA of 7.0", "CGPA of at least 7.5", "minimum CGPA of 6.8", "GPA: 3.5"
        "CGPA": re.compile(
            r"\b(?:CGPA|GPA)(?:\s+(?:of|at\s+least|minimum|cumulative|overall|standing|to)?)*\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\b",
            re.IGNORECASE,
        ),
        # Currency: $, USD, EUR, INR etc.
        "currency": re.compile(
            r"(?:\$|USD|EUR|GBP|₹|Rs\.?)\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)"
        ),
        # Percentage: 75%, 10.5 percent (note: % is non-word, do not use trailing \b after %)
        "percentage": re.compile(
            r"\b([0-9]+(?:\.[0-9]+)?)\s*(?:%|\bpercent\b)",
            re.IGNORECASE,
        ),
        # Dates: "May 1, 2024", "September 15", "2024-06-15"
        "date": re.compile(
            rf"\b{MONTHS}\s+[0-9]{{1,2}}(?:st|nd|rd|th)?(?:,?\s+[0-9]{{4}})?\b|\b[0-9]{{4}}[-/][0-9]{{2}}[-/][0-9]{{2}}\b",
            re.IGNORECASE,
        ),
        # Age requirements: "25 years of age", "age limit of 26", "25 yrs"
        "age": re.compile(
            r"\b(?:age\s*(?:limit)?\s*(?:of)?\s*([0-9]{1,2})|([0-9]{1,2})\s*(?:years?\s*(?:of\s*age|old)?|yrs))\b",
            re.IGNORECASE,
        ),
        # Durations: "14 days", "10 hours per week", "2 semesters"
        "duration": re.compile(
            r"\b([0-9]+)\s*(days?|weeks?|months?|semesters?|hours?)\b",
            re.IGNORECASE,
        ),
        # Credit hours / numbers with explicit threshold keywords
        "number": re.compile(
            r"\b([0-9]+(?:\.[0-9]+)?)\s*(?:credit\s*hours?|credits?)\b",
            re.IGNORECASE,
        ),
    }

    @classmethod
    def _extract_context(cls, text: str, start: int, end: int, window: int = 35) -> str:
        """Extract surrounding text around a match to help with context alignment."""
        c_start = max(0, start - window)
        c_end = min(len(text), end + window)
        snippet = text[c_start:c_end].replace("\n", " ")
        return re.sub(r"\s+", " ", snippet).strip().lower()

    @classmethod
    def extract_entities(cls, text: str) -> List[ExtractedEntity]:
        """
        Extract all recognized entities with their category, raw value, and context.

        Args:
            text: Document section text.

        Returns:
            List of ExtractedEntity objects.
        """
        if not text:
            return []

        results: List[ExtractedEntity] = []
        occupied_spans: List[Tuple[int, int]] = []

        def overlaps(s: int, e: int) -> bool:
            return any(not (e <= os or s >= oe) for os, oe in occupied_spans)

        # 1. CGPA
        for m in cls.PATTERNS["CGPA"].finditer(text):
            val = m.group(1)
            results.append(
                ExtractedEntity("CGPA", val, m.span(), cls._extract_context(text, m.start(), m.end()))
            )
            occupied_spans.append(m.span())

        # 2. Currency
        for m in cls.PATTERNS["currency"].finditer(text):
            if not overlaps(m.start(), m.end()):
                val = m.group(0).strip()
                results.append(
                    ExtractedEntity("currency", val, m.span(), cls._extract_context(text, m.start(), m.end()))
                )
                occupied_spans.append(m.span())

        # 3. Percentages
        for m in cls.PATTERNS["percentage"].finditer(text):
            if not overlaps(m.start(), m.end()):
                val = m.group(0).strip()
                results.append(
                    ExtractedEntity("percentage", val, m.span(), cls._extract_context(text, m.start(), m.end()))
                )
                occupied_spans.append(m.span())

        # 4. Dates
        for m in cls.PATTERNS["date"].finditer(text):
            if not overlaps(m.start(), m.end()):
                val = m.group(0).strip()
                results.append(
                    ExtractedEntity("date", val, m.span(), cls._extract_context(text, m.start(), m.end()))
                )
                occupied_spans.append(m.span())

        # 5. Age
        for m in cls.PATTERNS["age"].finditer(text):
            if not overlaps(m.start(), m.end()):
                val = m.group(1) or m.group(2)
                results.append(
                    ExtractedEntity("age", val, m.span(), cls._extract_context(text, m.start(), m.end()))
                )
                occupied_spans.append(m.span())

        # 6. Durations
        for m in cls.PATTERNS["duration"].finditer(text):
            if not overlaps(m.start(), m.end()):
                val = m.group(0).strip()
                results.append(
                    ExtractedEntity("duration", val, m.span(), cls._extract_context(text, m.start(), m.end()))
                )
                occupied_spans.append(m.span())

        # 7. Credit numbers
        for m in cls.PATTERNS["number"].finditer(text):
            if not overlaps(m.start(), m.end()):
                val = m.group(1).strip()
                results.append(
                    ExtractedEntity("number", val, m.span(), cls._extract_context(text, m.start(), m.end()))
                )
                occupied_spans.append(m.span())

        return results

    @classmethod
    def compare_entities(cls, old_text: Optional[str], new_text: Optional[str]) -> List[EntityChange]:
        """
        Compare entities extracted from old and new text and report value flips.

        Args:
            old_text: Original section text (or None if added).
            new_text: New section text (or None if removed).

        Returns:
            List of EntityChange items with old_value and new_value.
        """
        changes: List[EntityChange] = []

        old_entities = cls.extract_entities(old_text or "")
        new_entities = cls.extract_entities(new_text or "")

        # If old_text was None (added section), all new entities are newly introduced
        if old_text is None and new_text:
            for ne in new_entities:
                changes.append(
                    EntityChange(entity=ne.category, old_value=None, new_value=ne.raw_value, context=ne.context_hint)
                )
            return changes

        # If new_text was None (removed section), all old entities were removed
        if new_text is None and old_text:
            for oe in old_entities:
                changes.append(
                    EntityChange(entity=oe.category, old_value=oe.raw_value, new_value=None, context=oe.context_hint)
                )
            return changes

        # Match entities by category and context similarity
        by_cat_old: Dict[str, List[ExtractedEntity]] = {}
        for oe in old_entities:
            by_cat_old.setdefault(oe.category, []).append(oe)

        by_cat_new: Dict[str, List[ExtractedEntity]] = {}
        for ne in new_entities:
            by_cat_new.setdefault(ne.category, []).append(ne)

        all_cats = set(by_cat_old.keys()).union(set(by_cat_new.keys()))

        for cat in all_cats:
            old_list = by_cat_old.get(cat, [])
            new_list = by_cat_new.get(cat, [])

            # Pair items in order if counts match or greedily
            max_len = max(len(old_list), len(new_list))
            for k in range(max_len):
                o_val = old_list[k].raw_value if k < len(old_list) else None
                n_val = new_list[k].raw_value if k < len(new_list) else None
                ctx = old_list[k].context_hint if k < len(old_list) else (new_list[k].context_hint if k < len(new_list) else "")

                # Only record as a change if the value actually changed
                if o_val != n_val:
                    changes.append(
                        EntityChange(
                            entity=cat,
                            old_value=o_val,
                            new_value=n_val,
                            context=ctx,
                        )
                    )

        return changes
