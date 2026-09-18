"""
Diff engine module for computing deterministic textual differences and change magnitudes.

Leverages Python's standard `difflib` for:
- Sequence matching and similarity ratio
- Character and word-level visual diffs (HTML <ins>/<del> formatting)
- Unified line diffs
- Change magnitude scoring (0.0 = identical to 1.0 = completely replaced/added/removed)
"""

from dataclasses import dataclass, field
import difflib
import html
from typing import Optional, List
from src.section_splitter import Section


@dataclass
class DiffResult:
    """
    Detailed textual diff between two section instances.

    Attributes:
        change_type: "added", "removed", "modified", or "unchanged".
        change_magnitude: Normalized change score from 0.0 (identical) to 1.0 (completely new/deleted).
        similarity_ratio: SequenceMatcher similarity ratio (0.0 to 1.0).
        unified_diff: List of lines representing standard unified diff.
        word_diff_html: Rich inline HTML with <span class="diff-ins"> and <span class="diff-del"> tags.
        words_added: Count of added words.
        words_removed: Count of removed words.
    """
    change_type: str
    change_magnitude: float
    similarity_ratio: float
    unified_diff: List[str] = field(default_factory=list)
    word_diff_html: str = ""
    words_added: int = 0
    words_removed: int = 0


class DiffEngine:
    """Computes exact textual differences and change magnitude."""

    # Ratio threshold above which two normalized texts are considered identical
    UNCHANGED_THRESHOLD = 0.999

    @classmethod
    def generate_word_diff_html(cls, old_text: str, new_text: str) -> str:
        """
        Generate inline HTML showing inserted and deleted words cleanly.

        Args:
            old_text: Original raw or normalized text.
            new_text: New raw or normalized text.

        Returns:
            HTML string with styled span tags for additions and deletions.
        """
        old_words = old_text.split()
        new_words = new_text.split()

        matcher = difflib.SequenceMatcher(None, old_words, new_words)
        html_chunks: List[str] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                text = html.escape(" ".join(old_words[i1:i2]))
                html_chunks.append(f"<span>{text}</span>")
            elif tag == "delete":
                text = html.escape(" ".join(old_words[i1:i2]))
                html_chunks.append(
                    f'<span style="background-color: #ffeef0; color: #b31d28; text-decoration: line-through; padding: 2px 4px; border-radius: 3px;">{text}</span>'
                )
            elif tag == "insert":
                text = html.escape(" ".join(new_words[j1:j2]))
                html_chunks.append(
                    f'<span style="background-color: #e6ffed; color: #22863a; font-weight: 500; padding: 2px 4px; border-radius: 3px;">{text}</span>'
                )
            elif tag == "replace":
                old_chunk = html.escape(" ".join(old_words[i1:i2]))
                new_chunk = html.escape(" ".join(new_words[j1:j2]))
                html_chunks.append(
                    f'<span style="background-color: #ffeef0; color: #b31d28; text-decoration: line-through; padding: 2px 4px; border-radius: 3px;">{old_chunk}</span> '
                    f'<span style="background-color: #e6ffed; color: #22863a; font-weight: 500; padding: 2px 4px; border-radius: 3px;">{new_chunk}</span>'
                )

        return " ".join(html_chunks)

    @classmethod
    def compare_sections(
        cls,
        old_section: Optional[Section],
        new_section: Optional[Section],
    ) -> DiffResult:
        """
        Compare an aligned pair of sections to determine change type, magnitude, and diffs.

        Args:
            old_section: Section from Document V1 (None if added).
            new_section: Section from Document V2 (None if removed).

        Returns:
            DiffResult object.
        """
        # Case 1: Section was Added in V2
        if old_section is None and new_section is not None:
            new_words = len(new_section.text.split())
            escaped = html.escape(new_section.text)
            html_diff = f'<span style="background-color: #e6ffed; color: #22863a; font-weight: 500; padding: 2px 4px; border-radius: 3px;">{escaped}</span>'
            return DiffResult(
                change_type="added",
                change_magnitude=1.0,
                similarity_ratio=0.0,
                unified_diff=[f"+ {line}" for line in new_section.text.splitlines()],
                word_diff_html=html_diff,
                words_added=new_words,
                words_removed=0,
            )

        # Case 2: Section was Removed in V2
        if old_section is not None and new_section is None:
            old_words = len(old_section.text.split())
            escaped = html.escape(old_section.text)
            html_diff = f'<span style="background-color: #ffeef0; color: #b31d28; text-decoration: line-through; padding: 2px 4px; border-radius: 3px;">{escaped}</span>'
            return DiffResult(
                change_type="removed",
                change_magnitude=1.0,
                similarity_ratio=0.0,
                unified_diff=[f"- {line}" for line in old_section.text.splitlines()],
                word_diff_html=html_diff,
                words_added=0,
                words_removed=old_words,
            )

        # Case 3: Both exist (check for modified or unchanged)
        assert old_section is not None and new_section is not None

        old_norm = old_section.normalized_text or old_section.text
        new_norm = new_section.normalized_text or new_section.text

        matcher = difflib.SequenceMatcher(None, old_norm, new_norm)
        ratio = matcher.ratio()

        # Generate unified line diff on exact original text
        old_lines = old_section.text.splitlines(keepends=True)
        new_lines = new_section.text.splitlines(keepends=True)
        unified = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"v1/{old_section.title}",
                tofile=f"v2/{new_section.title}",
            )
        )

        # Calculate word additions and deletions
        old_words = old_section.text.split()
        new_words = new_section.text.split()
        word_matcher = difflib.SequenceMatcher(None, old_words, new_words)

        words_added = 0
        words_removed = 0
        for tag, i1, i2, j1, j2 in word_matcher.get_opcodes():
            if tag in ("delete", "replace"):
                words_removed += (i2 - i1)
            if tag in ("insert", "replace"):
                words_added += (j2 - j1)

        # Word-level HTML diff
        word_diff_html = cls.generate_word_diff_html(old_section.text, new_section.text)

        # Determine change type and magnitude
        if ratio >= cls.UNCHANGED_THRESHOLD and words_added == 0 and words_removed == 0:
            change_type = "unchanged"
            change_magnitude = 0.0
        else:
            change_type = "modified"
            change_magnitude = round(1.0 - ratio, 4)

        return DiffResult(
            change_type=change_type,
            change_magnitude=change_magnitude,
            similarity_ratio=round(ratio, 4),
            unified_diff=unified,
            word_diff_html=word_diff_html,
            words_added=words_added,
            words_removed=words_removed,
        )
