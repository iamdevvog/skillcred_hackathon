"""
Section alignment module for matching corresponding sections across document versions.

Multi-tier alignment strategy:
1. Exact title matching
2. Normalized title matching (handles formatting & numbering deltas)
3. Vector similarity matching (TF-IDF Cosine similarity, with pluggable Sentence Transformers)
4. Bipartite greedy assignment with configurable similarity threshold
5. Identification of added (None -> New) and removed (Old -> None) sections
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import math
import re
from collections import Counter
from typing import List, Optional, Tuple, Dict

from src.section_splitter import Section
from src.normalizer import Normalizer


@dataclass
class AlignmentResult:
    """
    Result of aligning a pair of sections across versions.

    Attributes:
        old_section: Section from Document V1 (None if added section).
        new_section: Section from Document V2 (None if removed section).
        similarity: Semantic/textual similarity score (0.0 to 1.0).
        match_method: Strategy that achieved alignment ("exact_title", "normalized_title", "tfidf_cosine", "embedding", "unaligned").
    """
    old_section: Optional[Section]
    new_section: Optional[Section]
    similarity: float
    match_method: str

    @property
    def display_arrow(self) -> str:
        """User-friendly representation: e.g. 'Eligibility V1 -> Eligibility V2'."""
        old_name = self.old_section.title if self.old_section else "None"
        new_name = self.new_section.title if self.new_section else "None"
        return f"{old_name} -> {new_name}"


class SimilarityEngine(ABC):
    """Abstract interface for text similarity calculations."""

    @abstractmethod
    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute similarity score between two text strings (0.0 to 1.0)."""
        pass

    @abstractmethod
    def compute_similarity_matrix(self, texts_a: List[str], texts_b: List[str]) -> List[List[float]]:
        """Compute pairwise similarity matrix between two lists of text."""
        pass


class TfidfSimilarityEngine(SimilarityEngine):
    """
    TF-IDF Cosine Similarity Engine.
    Uses scikit-learn when available, with a pure-Python fallback implementation.
    """

    def __init__(self):
        self._has_sklearn = False
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self._vectorizer_cls = TfidfVectorizer
            self._cosine_similarity_fn = cosine_similarity
            self._has_sklearn = True
        except ImportError:
            self._has_sklearn = False

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer for pure-Python fallback."""
        return re.findall(r"\b[a-z0-9_]{2,}\b", text.lower())

    def _pure_python_cosine(self, text_a: str, text_b: str) -> float:
        """Pure-Python TF-IDF cosine similarity."""
        tokens_a = self._tokenize(text_a)
        tokens_b = self._tokenize(text_b)

        if not tokens_a or not tokens_b:
            return 0.0

        all_tokens = set(tokens_a).union(set(tokens_b))
        freq_a = Counter(tokens_a)
        freq_b = Counter(tokens_b)

        # IDF approximation across the two documents
        doc_count = 2
        idf: Dict[str, float] = {}
        for token in all_tokens:
            df = (1 if token in freq_a else 0) + (1 if token in freq_b else 0)
            idf[token] = math.log((1 + doc_count) / (1 + df)) + 1.0

        # Vector dot product and norms
        dot_product = 0.0
        norm_a = 0.0
        norm_b = 0.0

        for token in all_tokens:
            tfidf_a = (freq_a.get(token, 0) / len(tokens_a)) * idf[token]
            tfidf_b = (freq_b.get(token, 0) / len(tokens_b)) * idf[token]
            dot_product += tfidf_a * tfidf_b
            norm_a += tfidf_a ** 2
            norm_b += tfidf_b ** 2

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute composite similarity between two texts using TF-IDF and sequence matching."""
        if not text_a.strip() or not text_b.strip():
            return 0.0

        import difflib
        seq_ratio = difflib.SequenceMatcher(None, text_a, text_b).ratio()

        tfidf_sim = 0.0
        if self._has_sklearn:
            try:
                vec = self._vectorizer_cls(stop_words="english", token_pattern=r"(?u)\b[\w\.]+\b")
                tfidf = vec.fit_transform([text_a, text_b])
                tfidf_sim = float(self._cosine_similarity_fn(tfidf[0:1], tfidf[1:2])[0][0])
                tfidf_sim = max(0.0, min(1.0, tfidf_sim))
            except Exception:
                tfidf_sim = max(0.0, min(1.0, self._pure_python_cosine(text_a, text_b)))
        else:
            tfidf_sim = max(0.0, min(1.0, self._pure_python_cosine(text_a, text_b)))

        # Blend TF-IDF with character/token sequence ratio
        if seq_ratio >= 0.999:
            return 1.0
        composite = 0.5 * tfidf_sim + 0.5 * seq_ratio
        # Ensure that if text is modified, similarity never falsely caps at 1.0
        return min(0.99, max(0.0, round(composite, 4)))

    def compute_similarity_matrix(self, texts_a: List[str], texts_b: List[str]) -> List[List[float]]:
        """Pairwise similarity matrix."""
        if not texts_a or not texts_b:
            return []

        if self._has_sklearn:
            try:
                corpus = texts_a + texts_b
                vec = self._vectorizer_cls(stop_words="english")
                tfidf_all = vec.fit_transform(corpus)
                tfidf_a = tfidf_all[:len(texts_a)]
                tfidf_b = tfidf_all[len(texts_a):]
                sim_matrix = self._cosine_similarity_fn(tfidf_a, tfidf_b)
                return [[float(max(0.0, min(1.0, val))) for val in row] for row in sim_matrix]
            except Exception:
                pass

        # Fallback matrix
        matrix: List[List[float]] = []
        for a in texts_a:
            row: List[float] = []
            for b in texts_b:
                row.append(self._pure_python_cosine(a, b))
            matrix.append(row)
        return matrix


class SentenceTransformerSimilarityEngine(SimilarityEngine):
    """
    Pluggable Semantic Similarity Engine using Sentence Transformers.
    Can be dynamically instantiated once sentence_transformers is installed.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        self._load_model()
        from sentence_transformers.util import cos_sim
        emb_a = self._model.encode(text_a, convert_to_tensor=True)
        emb_b = self._model.encode(text_b, convert_to_tensor=True)
        score = float(cos_sim(emb_a, emb_b)[0][0])
        return max(0.0, min(1.0, score))

    def compute_similarity_matrix(self, texts_a: List[str], texts_b: List[str]) -> List[List[float]]:
        self._load_model()
        from sentence_transformers.util import cos_sim
        emb_a = self._model.encode(texts_a, convert_to_tensor=True)
        emb_b = self._model.encode(texts_b, convert_to_tensor=True)
        scores = cos_sim(emb_a, emb_b).tolist()
        return [[max(0.0, min(1.0, float(val))) for val in row] for row in scores]


class SectionAligner:
    """
    Orchestrates multi-stage alignment between old sections and new sections.
    """

    def __init__(
        self,
        similarity_engine: Optional[SimilarityEngine] = None,
        min_similarity_threshold: float = 0.40,
    ):
        """
        Initialize aligner.

        Args:
            similarity_engine: Engine implementing SimilarityEngine (defaults to TfidfSimilarityEngine).
            min_similarity_threshold: Configurable minimum score to accept a match (default 0.40).
        """
        self.similarity_engine = similarity_engine or TfidfSimilarityEngine()
        self.min_similarity_threshold = min_similarity_threshold

    def align(self, old_sections: List[Section], new_sections: List[Section]) -> List[AlignmentResult]:
        """
        Align sections from old document to new document.

        Returns:
            List of AlignmentResult indicating:
            - Aligned pairs (old_section -> new_section)
            - Removed sections (old_section -> None)
            - Added sections (None -> new_section)
        """
        # Ensure all sections have normalized text
        Normalizer.normalize_sections(old_sections)
        Normalizer.normalize_sections(new_sections)

        matched_old: Dict[int, AlignmentResult] = {}
        matched_new: Dict[int, AlignmentResult] = {}

        unmatched_old = list(range(len(old_sections)))
        unmatched_new = list(range(len(new_sections)))

        # -------------------------------------------------------------
        # Stage 1: Exact Title Matching
        # -------------------------------------------------------------
        rem_old = []
        for i in unmatched_old:
            found_j = None
            for j in unmatched_new:
                if old_sections[i].title.strip().lower() == new_sections[j].title.strip().lower():
                    found_j = j
                    break
            if found_j is not None:
                # Text similarity for reporting
                text_sim = self.similarity_engine.compute_similarity(
                    old_sections[i].normalized_text, new_sections[found_j].normalized_text
                )
                res = AlignmentResult(
                    old_section=old_sections[i],
                    new_section=new_sections[found_j],
                    similarity=round(text_sim, 4),
                    match_method="exact_title",
                )
                matched_old[i] = res
                matched_new[found_j] = res
                unmatched_new.remove(found_j)
            else:
                rem_old.append(i)
        unmatched_old = rem_old

        # -------------------------------------------------------------
        # Stage 2: Normalized & Fuzzy Title Matching (e.g. "Section 2: Criteria" vs "Criteria")
        # -------------------------------------------------------------
        rem_old = []
        for i in unmatched_old:
            norm_title_old = Normalizer.normalize_title(old_sections[i].title)
            if not norm_title_old:
                rem_old.append(i)
                continue

            found_j = None
            best_overlap = 0.0

            words_old = set(re.findall(r"\b\w{3,}\b", norm_title_old))

            for j in unmatched_new:
                norm_title_new = Normalizer.normalize_title(new_sections[j].title)
                if not norm_title_new:
                    continue

                # Exact normalized title match
                if norm_title_old == norm_title_new:
                    found_j = j
                    break

                # Fuzzy title word overlap (e.g. "student financial eligibility" vs "financial eligibility")
                words_new = set(re.findall(r"\b\w{3,}\b", norm_title_new))
                if words_old and words_new:
                    common = words_old.intersection(words_new)
                    overlap = len(common) / min(len(words_old), len(words_new))
                    if overlap >= 0.6 and overlap > best_overlap:
                        best_overlap = overlap
                        found_j = j

            if found_j is not None:
                text_sim = self.similarity_engine.compute_similarity(
                    old_sections[i].normalized_text, new_sections[found_j].normalized_text
                )
                res = AlignmentResult(
                    old_section=old_sections[i],
                    new_section=new_sections[found_j],
                    similarity=round(text_sim, 4),
                    match_method="normalized_title",
                )
                matched_old[i] = res
                matched_new[found_j] = res
                unmatched_new.remove(found_j)
            else:
                rem_old.append(i)
        unmatched_old = rem_old

        # -------------------------------------------------------------
        # Stage 3: Vector / TF-IDF Cosine Similarity on Body Text
        # -------------------------------------------------------------
        if unmatched_old and unmatched_new:
            old_texts = [old_sections[i].normalized_text for i in unmatched_old]
            new_texts = [new_sections[j].normalized_text for j in unmatched_new]

            sim_matrix = self.similarity_engine.compute_similarity_matrix(old_texts, new_texts)

            # Build list of potential candidates (score, old_idx, new_idx)
            candidates: List[Tuple[float, int, int]] = []
            for row_idx, i in enumerate(unmatched_old):
                for col_idx, j in enumerate(unmatched_new):
                    score = sim_matrix[row_idx][col_idx]
                    if score >= self.min_similarity_threshold:
                        candidates.append((score, i, j))

            # Sort descending by similarity score
            candidates.sort(key=lambda x: x[0], reverse=True)

            # Greedy bipartite assignment
            assigned_old = set()
            assigned_new = set()

            for score, i, j in candidates:
                if i not in assigned_old and j not in assigned_new:
                    res = AlignmentResult(
                        old_section=old_sections[i],
                        new_section=new_sections[j],
                        similarity=round(score, 4),
                        match_method="tfidf_cosine",
                    )
                    matched_old[i] = res
                    matched_new[j] = res
                    assigned_old.add(i)
                    assigned_new.add(j)

            unmatched_old = [i for i in unmatched_old if i not in assigned_old]
            unmatched_new = [j for j in unmatched_new if j not in assigned_new]

        # -------------------------------------------------------------
        # Stage 4 & 5: Assemble Final Alignment Ordered List
        # -------------------------------------------------------------
        aligned_results: List[AlignmentResult] = []

        # First, add all old sections in original order (either matched or removed)
        for i in range(len(old_sections)):
            if i in matched_old:
                aligned_results.append(matched_old[i])
            else:
                # Removed section: old -> None
                aligned_results.append(
                    AlignmentResult(
                        old_section=old_sections[i],
                        new_section=None,
                        similarity=0.0,
                        match_method="unaligned",
                    )
                )

        # Next, append newly added sections (None -> new)
        for j in unmatched_new:
            aligned_results.append(
                AlignmentResult(
                    old_section=None,
                    new_section=new_sections[j],
                    similarity=0.0,
                    match_method="unaligned",
                )
            )

        return aligned_results
