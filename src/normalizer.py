"""
Text normalization module for comparing policy document sections.

Provides deterministic text cleaning:
- Lowercases text for fair semantic comparison.
- Normalizes unicode quotes, dashes, and whitespace.
- Collapses multi-spaces and linebreaks.
- Extracts canonical titles (stripping "Section 1:", numbers, etc.).
- Never mutates or destroys the original raw text.
"""

import re
from typing import List
from src.section_splitter import Section


class Normalizer:
    """Normalizes text and section titles for accurate alignment and diffing."""

    # Unicode quote and dash standardization mappings
    CHAR_REPLACEMENTS = {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "–": "-",
        "—": "-",
        "―": "-",
        "\u00a0": " ",  # Non-breaking space
        "\u200b": "",   # Zero-width space
    }

    # Regex to extract canonical title by stripping section numbers / prefixes
    PREFIX_STRIP_REGEX = re.compile(
        r"^(?:section|article|clause)?\s*([0-9ivxlcdm]+(?:\.[0-9]+)*)?[:.\-–—\s]*",
        re.IGNORECASE,
    )

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        Normalize text content for semantic and textual comparison.

        Args:
            text: Raw input string.

        Returns:
            Normalized lowercase string with collapsed whitespace.
        """
        if not text:
            return ""

        result = text.lower()

        # Normalize special unicode quotes, hyphens, and spaces
        for char, replacement in cls.CHAR_REPLACEMENTS.items():
            result = result.replace(char, replacement)

        # Standardize punctuation spacing
        result = re.sub(r"[ \t]+", " ", result)
        result = re.sub(r"\n\s*", "\n", result)
        result = re.sub(r"\s+", " ", result)

        return result.strip()

    @classmethod
    def normalize_title(cls, title: str) -> str:
        """
        Normalize section title for title-based alignment.
        Strips prefixes like 'Section 1:', '1.', 'I.', lowercases, and removes punctuation.

        Example:
            'Section 2: Eligibility Criteria' -> 'eligibility criteria'
            '1. Introduction' -> 'introduction'

        Args:
            title: Raw section title.

        Returns:
            Canonical title string.
        """
        if not title:
            return ""

        cleaned = title.strip()

        # Remove markdown heading hashes (#, ##)
        cleaned = re.sub(r"^#+\s*", "", cleaned)

        # Remove common section prefixes
        cleaned = cls.PREFIX_STRIP_REGEX.sub("", cleaned).strip()

        # Lowercase and replace unicode characters
        for char, replacement in cls.CHAR_REPLACEMENTS.items():
            cleaned = cleaned.replace(char, replacement)

        # Remove punctuation except alphanumeric and single spaces
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()

        return cleaned

    @classmethod
    def normalize_section(cls, section: Section) -> Section:
        """
        Populate normalized_text on a Section object without modifying original text.

        Args:
            section: Section object.

        Returns:
            The same Section object with normalized_text populated.
        """
        section.normalized_text = cls.normalize_text(section.text)
        return section

    @classmethod
    def normalize_sections(cls, sections: List[Section]) -> List[Section]:
        """
        Populate normalized_text across all Section objects in a list.

        Args:
            sections: List of Section objects.

        Returns:
            List of modified Section objects.
        """
        for sec in sections:
            cls.normalize_section(sec)
        return sections
