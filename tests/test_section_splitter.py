"""
Unit tests for SectionSplitter.
"""

import unittest
from pathlib import Path

from src.section_splitter import SectionSplitter, Section
from src.document_parser import DocumentParser


class TestSectionSplitter(unittest.TestCase):
    """Tests for section splitting heuristics and structure preservation."""

    def setUp(self):
        self.splitter = SectionSplitter()

    def test_numbered_sections(self):
        sample = (
            "1. Introduction\n"
            "This is the introductory text.\n\n"
            "2. Eligibility\n"
            "Students must have a CGPA of 7.0.\n"
        )
        sections = self.splitter.split(sample)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].title, "1. Introduction")
        self.assertIn("introductory text", sections[0].text)
        self.assertEqual(sections[1].title, "2. Eligibility")
        self.assertIn("CGPA of 7.0", sections[1].text)

    def test_section_keyword_prefix(self):
        sample = (
            "Section 1: Purpose\n"
            "Scope of this policy.\n\n"
            "Section 2: Criteria\n"
            "Criteria description.\n"
        )
        sections = self.splitter.split(sample)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].title, "Section 1: Purpose")
        self.assertEqual(sections[1].title, "Section 2: Criteria")

    def test_markdown_headers(self):
        sample = (
            "## Policy Scope\n"
            "This is policy scope.\n\n"
            "### Award Limits\n"
            "Max $5000.\n"
        )
        sections = self.splitter.split(sample)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].title, "Policy Scope")
        self.assertEqual(sections[1].title, "Award Limits")

    def test_roman_numerals(self):
        sample = (
            "I. General Provisions\n"
            "General provisions text.\n\n"
            "II. Sanctions\n"
            "Disciplinary sanctions.\n"
        )
        sections = self.splitter.split(sample)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].title, "I. General Provisions")
        self.assertEqual(sections[1].title, "II. Sanctions")

    def test_all_caps_headings(self):
        sample = (
            "ELIGIBILITY REQUIREMENTS\n"
            "Applicant requirements.\n\n"
            "APPLICATION DEADLINE\n"
            "Due May 1st.\n"
        )
        sections = self.splitter.split(sample)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].title, "Eligibility Requirements")
        self.assertEqual(sections[1].title, "Application Deadline")

    def test_preamble_detection(self):
        sample = (
            "University Financial Policy 2024\n"
            "Published by Financial Services\n\n"
            "Section 1: Purpose\n"
            "Purpose text here.\n"
        )
        sections = self.splitter.split(sample)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].title, "Preamble")
        self.assertIn("University Financial Policy 2024", sections[0].text)
        self.assertEqual(sections[1].title, "Section 1: Purpose")

    def test_no_headers_fallback(self):
        sample = "Just a single paragraph of text with no recognized section headings."
        sections = self.splitter.split(sample)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].title, "Preamble")
        self.assertEqual(sections[0].text, sample)

    def test_empty_string(self):
        sections = self.splitter.split("")
        self.assertEqual(sections, [])

    def test_exact_text_preservation(self):
        sample = "Section 1: Exact Preservation\nPreserves Case, $500, 10% & Punctuation!"
        sections = self.splitter.split(sample)
        self.assertEqual(len(sections), 1)
        self.assertIn("$500, 10% & Punctuation!", sections[0].text)

    def test_real_sample_policies(self):
        data_dir = Path(__file__).resolve().parent.parent / "data"
        p1_path = data_dir / "policy_v1.txt"
        p2_path = data_dir / "policy_v2.txt"

        self.assertTrue(p1_path.exists(), "policy_v1.txt should exist")
        self.assertTrue(p2_path.exists(), "policy_v2.txt should exist")

        text_v1 = DocumentParser.parse_txt(p1_path)
        text_v2 = DocumentParser.parse_txt(p2_path)

        sections_v1 = self.splitter.split(text_v1)
        sections_v2 = self.splitter.split(text_v2)

        # Both documents have a markdown title header + 10 sections = 11 sections total (or preamble + 10)
        self.assertGreaterEqual(len(sections_v1), 10)
        self.assertGreaterEqual(len(sections_v2), 10)

        # Check key sections exist in v1
        titles_v1 = [s.title for s in sections_v1]
        self.assertTrue(any("Eligibility Criteria" in t for t in titles_v1))
        self.assertTrue(any("Work-Study Prerequisite" in t for t in titles_v1))

        # Check key sections exist in v2
        titles_v2 = [s.title for s in sections_v2]
        self.assertTrue(any("Eligibility Criteria" in t for t in titles_v2))
        self.assertTrue(any("Appeals and Grievance Procedure" in t for t in titles_v2))
        # V2 should not have Work-Study Prerequisite
        self.assertFalse(any("Work-Study Prerequisite" in t for t in titles_v2))


if __name__ == "__main__":
    unittest.main()
