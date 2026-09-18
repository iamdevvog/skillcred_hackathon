"""
Document parser module for extracting raw text from various document formats.
Initially focuses on plain text (.txt) files with support for binary buffers and multiple encodings.
"""

from pathlib import Path
from typing import Union, BinaryIO
import io


class DocumentParser:
    """Parses input files or buffers into raw text strings."""

    SUPPORTED_EXTENSIONS = {".txt"}

    @staticmethod
    def parse_txt(source: Union[str, Path, BinaryIO, bytes]) -> str:
        """
        Extract text from a plain text source (.txt).

        Args:
            source: A file path (str or Path), bytes object, or file-like binary stream.

        Returns:
            Extracted text as a standard string with normalized line breaks (\\n).

        Raises:
            FileNotFoundError: If the given file path does not exist.
            ValueError: If the input cannot be decoded or is empty.
        """
        raw_bytes: bytes

        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Document not found at path: {path}")
            raw_bytes = path.read_bytes()
        elif isinstance(source, (io.BytesIO, BinaryIO)) or hasattr(source, "read"):
            raw_bytes = source.read()
            if isinstance(raw_bytes, str):
                return raw_bytes.replace("\r\n", "\n").replace("\r", "\n")
        elif isinstance(source, bytes):
            raw_bytes = source
        else:
            raise TypeError(f"Unsupported source type: {type(source)}")

        # Try multiple encodings in order of likelihood
        # Note: utf-8-sig seamlessly handles both BOM and non-BOM UTF-8 text
        encodings_to_try = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
        decoded_text: str | None = None

        for encoding in encodings_to_try:
            try:
                decoded_text = raw_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if decoded_text is None:
            raise ValueError("Unable to decode document with standard encodings (utf-8, latin-1, cp1252).")

        # Strip any stray BOM character and standardize line endings to \n
        normalized_text = decoded_text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
        return normalized_text

    @classmethod
    def parse_document(cls, source: Union[str, Path, BinaryIO, bytes], filename: str | None = None) -> str:
        """
        General document parser dispatcher.

        Args:
            source: A file path, bytes, or binary stream.
            filename: Optional filename hint to determine file type if source is a stream or bytes.

        Returns:
            Extracted text string.
        """
        ext = ""
        if filename:
            ext = Path(filename).suffix.lower()
        elif isinstance(source, (str, Path)):
            ext = Path(source).suffix.lower()

        if ext == ".txt" or not ext:
            return cls.parse_txt(source)
        elif ext == ".pdf":
            # Reserved for PyMuPDF in upcoming phase
            raise NotImplementedError("PDF parsing will be enabled in subsequent phase.")
        elif ext in (".docx", ".doc"):
            # Reserved for python-docx in upcoming phase
            raise NotImplementedError("DOCX parsing will be enabled in subsequent phase.")
        else:
            raise ValueError(f"Unsupported file format: {ext}")
