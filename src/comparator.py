"""
Policy document comparator orchestrator module.

Integrates:
- DocumentParser -> SectionSplitter -> Normalizer -> SectionAligner
- DiffEngine -> EntityExtractor -> RuleBasedChangeClassifier

Strict Reliability Rule:
The `verified` field must only be True when an aligned old/new evidence pair exists.
"""

from dataclasses import dataclass, field, asdict
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from src.document_parser import DocumentParser
from src.section_splitter import SectionSplitter, Section
from src.normalizer import Normalizer
from src.aligner import SectionAligner, AlignmentResult
from src.diff_engine import DiffEngine, DiffResult
from src.entity_extractor import EntityExtractor, EntityChange
from src.change_classifier import RuleBasedChangeClassifier, BaseChangeClassifier


@dataclass
class ChangeRecord:
    """
    Structured record for a detected section change or status.

    Attributes:
        section: Display title of the section.
        change_type: "added", "removed", "modified", or "unchanged".
        category: Classified policy topic (eligibility, deadline, fee, etc.).
        similarity: Semantic/textual similarity score (0.0 to 1.0).
        old_text: Exact text from Document V1 (None if added).
        new_text: Exact text from Document V2 (None if removed).
        entities_changed: List of critical value/threshold differences.
        verified: True ONLY when an aligned old/new evidence pair exists.
        word_diff_html: Inline visual diff HTML.
        diff_magnitude: Magnitude score (0.0 to 1.0).
        match_method: Method used to align this section.
    """
    section: str
    change_type: str
    category: str
    similarity: float
    old_text: Optional[str]
    new_text: Optional[str]
    entities_changed: List[Dict[str, Any]]
    verified: bool
    word_diff_html: str = ""
    diff_magnitude: float = 0.0
    match_method: str = "unaligned"

    def to_dict(self) -> Dict[str, Any]:
        """Convert ChangeRecord to dictionary conforming to Phase 9 schema."""
        return {
            "section": self.section,
            "change_type": self.change_type,
            "category": self.category,
            "similarity": self.similarity,
            "old_text": self.old_text,
            "new_text": self.new_text,
            "entities_changed": self.entities_changed,
            "verified": self.verified,
        }


@dataclass
class ComparisonSummary:
    """High-level summary metrics of the document comparison."""
    total_sections_v1: int
    total_sections_v2: int
    total_changes: int
    added_count: int
    removed_count: int
    modified_count: int
    unchanged_count: int
    records: List[ChangeRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_sections_v1": self.total_sections_v1,
            "total_sections_v2": self.total_sections_v2,
            "total_changes": self.total_changes,
            "added": self.added_count,
            "removed": self.removed_count,
            "modified": self.modified_count,
            "unchanged": self.unchanged_count,
            "records": [r.to_dict() for r in self.records],
        }


class PolicyComparator:
    """Central orchestrator for the Policy Document Comparison pipeline."""

    def __init__(
        self,
        splitter: Optional[SectionSplitter] = None,
        aligner: Optional[SectionAligner] = None,
        classifier: Optional[BaseChangeClassifier] = None,
    ):
        self.splitter = splitter or SectionSplitter()
        self.aligner = aligner or SectionAligner()
        self.classifier = classifier or RuleBasedChangeClassifier()

    def compare_sections(
        self, old_sections: List[Section], new_sections: List[Section]
    ) -> ComparisonSummary:
        """
        Execute comparison across lists of Section objects.

        Args:
            old_sections: Parsed sections from Document 1.
            new_sections: Parsed sections from Document 2.

        Returns:
            ComparisonSummary with classified, diffed, and verified records.
        """
        # Step 1: Align sections
        alignments = self.aligner.align(old_sections, new_sections)

        records: List[ChangeRecord] = []
        added_count = 0
        removed_count = 0
        modified_count = 0
        unchanged_count = 0

        for item in alignments:
            old_sec = item.old_section
            new_sec = item.new_section

            # Step 2: Compute deterministic diff and change magnitude
            diff_res = DiffEngine.compare_sections(old_sec, new_sec)
            change_type = diff_res.change_type

            # Step 3: Determine section display title
            if old_sec and new_sec:
                display_title = new_sec.title if new_sec.title == old_sec.title else f"{old_sec.title} -> {new_sec.title}"
            elif new_sec:
                display_title = new_sec.title
            elif old_sec:
                display_title = old_sec.title
            else:
                display_title = "Unknown Section"

            # Step 4: Extract and compare critical entities/values
            old_raw = old_sec.text if old_sec else None
            new_raw = new_sec.text if new_sec else None
            entity_changes = EntityExtractor.compare_entities(old_raw, new_raw)
            entities_dict_list = [ec.to_dict() for ec in entity_changes]

            # Step 5: Classify change category
            sample_text = new_raw or old_raw or ""
            category = self.classifier.classify(display_title, sample_text, entity_changes)

            # Step 6: Enforce Strict Verification Rule:
            # Verified must ONLY be True when an aligned old/new evidence pair exists!
            is_verified = (old_sec is not None) and (new_sec is not None)

            # Update metrics
            if change_type == "added":
                added_count += 1
            elif change_type == "removed":
                removed_count += 1
            elif change_type == "modified":
                modified_count += 1
            elif change_type == "unchanged":
                unchanged_count += 1

            records.append(
                ChangeRecord(
                    section=display_title,
                    change_type=change_type,
                    category=category,
                    similarity=item.similarity,
                    old_text=old_raw,
                    new_text=new_raw,
                    entities_changed=entities_dict_list,
                    verified=is_verified,
                    word_diff_html=diff_res.word_diff_html,
                    diff_magnitude=diff_res.change_magnitude,
                    match_method=item.match_method,
                )
            )

        total_changes = added_count + removed_count + modified_count

        return ComparisonSummary(
            total_sections_v1=len(old_sections),
            total_sections_v2=len(new_sections),
            total_changes=total_changes,
            added_count=added_count,
            removed_count=removed_count,
            modified_count=modified_count,
            unchanged_count=unchanged_count,
            records=records,
        )

    def compare_texts(self, text_v1: str, text_v2: str) -> ComparisonSummary:
        """Parse raw text, split into sections, and run comparison."""
        sections_v1 = self.splitter.split(text_v1)
        sections_v2 = self.splitter.split(text_v2)
        return self.compare_sections(sections_v1, sections_v2)

    def compare_files(
        self, file_v1: Union[str, Path], file_v2: Union[str, Path]
    ) -> ComparisonSummary:
        """Read files from disk, extract text, and run comparison."""
        text_v1 = DocumentParser.parse_document(file_v1)
        text_v2 = DocumentParser.parse_document(file_v2)
        return self.compare_texts(text_v1, text_v2)
