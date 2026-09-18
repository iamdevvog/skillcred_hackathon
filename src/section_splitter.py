"""
Section splitter module for segmenting raw policy documents into structured sections.

Detects section headers using multiple flexible patterns:
- Numbered headers (e.g., '1. Introduction', '1.1 Background', 'Section 1: Eligibility')
- Roman numerals (e.g., 'I. Purpose', 'IV. Sanctions')
- Markdown headings (e.g., '## Eligibility')
- Uppercase headers on their own line (e.g., 'ELIGIBILITY CRITERIA')
- Lettered headers (e.g., 'A. General Conditions')

Preserves exact raw text and line numbers for faithful evidence verification.
"""

from dataclasses import dataclass, field, asdict
import re
from typing import List, Optional, Dict, Any


@dataclass
class Section:
    """
    Structured representation of a document section.

    Attributes:
        id: Unique 1-based sequential identifier within the document.
        title: Extracted or inferred title of the section.
        text: Exact original text of the section (including title and body).
        normalized_text: Cleaned text for comparison (populated by normalizer).
        start_line: Starting line index (1-based) in the source document.
        end_line: Ending line index (1-based) in the source document.
        metadata: Optional dictionary for extra attributes (e.g. section number).
    """
    id: int
    title: str
    text: str
    normalized_text: str = ""
    start_line: int = 1
    end_line: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert section to a standard dictionary representation."""
        return asdict(self)


class SectionSplitter:
    """Splits raw text into structured Section objects."""

    # Regex patterns for matching common policy document section headers
    # Each pattern must capture the title or identifier
    HEADER_PATTERNS = [
        # Markdown headings: "# Title", "## Title", "### Title"
        re.compile(r"^(#{1,4})\s+(.+)$"),

        # Explicit "Section X:" or "Article X:" with optional title (supports 1, 1.1, A, IV, etc.)
        re.compile(r"^(?:Section|Article|Clause)\s+([0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*)[:.\-–—]?\s*(.*)$", re.IGNORECASE),

        # Numbered headings: "1. Title", "1.1 Title", "1.1.1 Title"
        re.compile(r"^([0-9]+(?:\.[0-9]+)*)\.?\s+([A-Z0-9][\w\s,–—\(\)\/\-\'\"]+)$"),

        # Roman numeral headings: "I. Title", "IV - Title"
        re.compile(r"^([IVXLCDM]+)[\.\-–—]\s+([A-Z0-9][\w\s,–—\(\)\/\-\'\"]+)$"),

        # Capitalized alphabetic headings: "A. Title", "B. Title"
        re.compile(r"^([A-Z])[\.\-–—]\s+([A-Z0-9][\w\s,–—\(\)\/\-\'\"]+)$"),

        # ALL-CAPS short headings on their own line (3 to 60 chars, at least 2 words or single standard heading)
        re.compile(r"^([A-Z0-9\s,–—\/\-\'\"]{3,60})$"),
    ]

    # Stop words / common non-heading all-caps lines to ignore for all-caps pattern
    EXCLUDED_ALL_CAPS = {"TABLE OF CONTENTS", "CONFIDENTIAL", "PAGE", "DRAFT", "VERSION 1.0", "VERSION 2.0"}

    def __init__(self, fallback_title: str = "Preamble"):
        self.fallback_title = fallback_title

    def _is_header_candidate(self, line: str) -> Optional[str]:
        """
        Check if a line matches any known section header pattern.

        Returns:
            The cleaned section title string if line is a header, else None.
        """
        stripped = line.strip()
        if not stripped:
            return None

        # 1. Markdown heading
        m = self.HEADER_PATTERNS[0].match(stripped)
        if m:
            title = m.group(2).strip()
            return title if title else stripped

        # 2. "Section X: Title"
        m = self.HEADER_PATTERNS[1].match(stripped)
        if m:
            sec_num = m.group(1).strip()
            rest = m.group(2).strip()
            if rest:
                return f"Section {sec_num}: {rest}"
            return f"Section {sec_num}"

        # 3. Numbered heading "1. Title"
        m = self.HEADER_PATTERNS[2].match(stripped)
        if m:
            sec_num = m.group(1).strip()
            title = m.group(2).strip()
            # Verify the title isn't just an ordinary sentence ending with a period
            if len(title.split()) <= 12 and not title.endswith("."):
                return f"{sec_num}. {title}"
            elif len(title.split()) <= 12:
                # E.g. "1. Eligibility." -> strip trailing dot
                return f"{sec_num}. {title.rstrip('.')}"

        # 4. Roman numerals "I. Title"
        m = self.HEADER_PATTERNS[3].match(stripped)
        if m:
            num = m.group(1).strip()
            title = m.group(2).strip()
            if len(title.split()) <= 12:
                return f"{num}. {title.rstrip('.')}"

        # 5. Lettered "A. Title"
        m = self.HEADER_PATTERNS[4].match(stripped)
        if m:
            letter = m.group(1).strip()
            title = m.group(2).strip()
            if len(title.split()) <= 12:
                return f"{letter}. {title.rstrip('.')}"

        # 6. All-caps line
        m = self.HEADER_PATTERNS[5].match(stripped)
        if m:
            text = m.group(1).strip()
            # Must have letters, not too long, not purely numbers, not in exclusion set
            has_letters = any(c.isalpha() for c in text)
            if has_letters and text not in self.EXCLUDED_ALL_CAPS and len(text.split()) <= 8:
                # Avoid matching if it ends with punctuation like a regular sentence
                if not text.endswith((".", ",", ";", ":")):
                    # Title case representation for clean readability
                    return text.title()

        return None

    def split(self, text: str) -> List[Section]:
        """
        Split a policy document's text into a list of Section objects.

        Args:
            text: Raw document text.

        Returns:
            List of Section objects preserving exact text chunks.
        """
        if not text or not text.strip():
            return []

        lines = text.split("\n")
        total_lines = len(lines)

        # First pass: find header locations (line_index, title)
        header_indices: List[tuple[int, str]] = []
        for idx, line in enumerate(lines):
            header_title = self._is_header_candidate(line)
            if header_title:
                header_indices.append((idx, header_title))

        # If no headers found at all, return the whole document as one section
        if not header_indices:
            return [
                Section(
                    id=1,
                    title=self.fallback_title if self.fallback_title else "Document Body",
                    text=text.strip(),
                    normalized_text="",
                    start_line=1,
                    end_line=total_lines,
                )
            ]

        sections: List[Section] = []
        sec_id = 1

        # Check if there is introductory text before the first section header
        first_header_idx = header_indices[0][0]
        if first_header_idx > 0:
            preamble_lines = lines[:first_header_idx]
            preamble_text = "\n".join(preamble_lines).strip()
            if preamble_text:
                sections.append(
                    Section(
                        id=sec_id,
                        title=self.fallback_title,
                        text=preamble_text,
                        normalized_text="",
                        start_line=1,
                        end_line=first_header_idx,
                    )
                )
                sec_id += 1

        # Build each section from header_indices
        for i, (start_idx, title) in enumerate(header_indices):
            # End line is the start of next header, or end of document
            if i + 1 < len(header_indices):
                end_idx = header_indices[i + 1][0]
            else:
                end_idx = total_lines

            sec_lines = lines[start_idx:end_idx]
            sec_text = "\n".join(sec_lines).strip()

            sections.append(
                Section(
                    id=sec_id,
                    title=title,
                    text=sec_text,
                    normalized_text="",
                    start_line=start_idx + 1,
                    end_line=end_idx,
                )
            )
            sec_id += 1

        return sections
