"""
Unit tests for DocumentParser.
"""

import io
import tempfile
import unittest
from pathlib import Path

from src.document_parser import DocumentParser


class TestDocumentParser(unittest.TestCase):
    """Tests for document reading and decoding functionality."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_txt_from_file_path(self):
        test_file = self.temp_path / "sample.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3", encoding="utf-8")

        result = DocumentParser.parse_txt(str(test_file))
        self.assertEqual(result, "Line 1\nLine 2\nLine 3")

    def test_parse_txt_crlf_normalization(self):
        raw_bytes = b"Line 1\r\nLine 2\r\nLine 3"
        result = DocumentParser.parse_txt(raw_bytes)
        self.assertEqual(result, "Line 1\nLine 2\nLine 3")

    def test_parse_txt_from_bytes_io(self):
        stream = io.BytesIO(b"Hello World from Stream\nSecond Line")
        result = DocumentParser.parse_txt(stream)
        self.assertEqual(result, "Hello World from Stream\nSecond Line")

    def test_parse_txt_with_utf8_bom(self):
        # UTF-8 with BOM (0xEF, 0xBB, 0xBF)
        bom_bytes = b"\xef\xbb\xbfSection 1: Overview\nContent"
        result = DocumentParser.parse_txt(bom_bytes)
        self.assertTrue(result.startswith("Section 1: Overview"))

    def test_parse_txt_latin1_fallback(self):
        # Character 'café' in latin-1 (0xe9)
        latin1_bytes = "Café Policy: Minimum threshold".encode("latin-1")
        result = DocumentParser.parse_txt(latin1_bytes)
        self.assertIn("Café Policy", result)

    def test_file_not_found(self):
        non_existent = self.temp_path / "does_not_exist.txt"
        with self.assertRaises(FileNotFoundError):
            DocumentParser.parse_txt(str(non_existent))

    def test_unsupported_type(self):
        with self.assertRaises(TypeError):
            DocumentParser.parse_txt(12345)  # type: ignore

    def test_parse_document_dispatcher_unsupported_extension(self):
        with self.assertRaises(ValueError):
            DocumentParser.parse_document("test.xyz", filename="test.xyz")


if __name__ == "__main__":
    unittest.main()
