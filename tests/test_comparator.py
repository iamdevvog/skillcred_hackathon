"""
Comprehensive unit tests for the Policy Document Comparison System.

Covers all 10 required test scenarios:
1. Added section
2. Removed section
3. Modified section
4. Reordered section
5. Rewritten section
6. Number change
7. Date change
8. Currency change
9. Similar sections with different wording
10. Completely unrelated sections
Plus gold benchmark Precision, Recall, and F1 evaluation.
"""

import unittest
from pathlib import Path

from src.section_splitter import Section
from src.comparator import PolicyComparator
from src.evaluator import evaluate_comparator


class TestPolicyComparator(unittest.TestCase):
    """Unit tests verifying all core change detection and alignment capabilities."""

    def setUp(self):
        self.comparator = PolicyComparator()
        self.base_dir = Path(__file__).resolve().parent.parent

    # -------------------------------------------------------------
    # 1. Added Section
    # -------------------------------------------------------------
    def test_01_added_section(self):
        v1_text = "Section 1: Scope\nAll undergraduate students must register."
        v2_text = (
            "Section 1: Scope\nAll undergraduate students must register.\n\n"
            "Section 2: Appeals\nStudents can appeal decisions within 14 days."
        )
        summary = self.comparator.compare_texts(v1_text, v2_text)
        added_records = [r for r in summary.records if r.change_type == "added"]

        self.assertEqual(len(added_records), 1)
        self.assertIn("Appeals", added_records[0].section)
        self.assertIsNone(added_records[0].old_text)
        self.assertIsNotNone(added_records[0].new_text)
        # Strict reliability rule: unaligned section must NOT be verified
        self.assertFalse(added_records[0].verified)

    # -------------------------------------------------------------
    # 2. Removed Section
    # -------------------------------------------------------------
    def test_02_removed_section(self):
        v1_text = (
            "Section 1: Scope\nAll undergraduate students must register.\n\n"
            "Section 2: Work Study\nStudents must perform 10 hours of campus labor."
        )
        v2_text = "Section 1: Scope\nAll undergraduate students must register."

        summary = self.comparator.compare_texts(v1_text, v2_text)
        removed_records = [r for r in summary.records if r.change_type == "removed"]

        self.assertEqual(len(removed_records), 1)
        self.assertIn("Work Study", removed_records[0].section)
        self.assertIsNotNone(removed_records[0].old_text)
        self.assertIsNone(removed_records[0].new_text)
        # Strict reliability rule: unaligned section must NOT be verified
        self.assertFalse(removed_records[0].verified)

    # -------------------------------------------------------------
    # 3. Modified Section
    # -------------------------------------------------------------
    def test_03_modified_section(self):
        v1_text = "Section 1: Eligibility\nStudents must maintain a minimum CGPA of 7.0."
        v2_text = "Section 1: Eligibility\nStudents must maintain a minimum CGPA of 7.5."

        summary = self.comparator.compare_texts(v1_text, v2_text)
        mod_records = [r for r in summary.records if r.change_type == "modified"]

        self.assertEqual(len(mod_records), 1)
        self.assertTrue(mod_records[0].verified)
        self.assertLess(mod_records[0].similarity, 1.0)
        self.assertGreater(mod_records[0].diff_magnitude, 0.0)

    # -------------------------------------------------------------
    # 4. Reordered Section
    # -------------------------------------------------------------
    def test_04_reordered_section(self):
        v1_text = (
            "Section 1: Alpha\nContent for section alpha.\n\n"
            "Section 2: Beta\nContent for section beta."
        )
        # In V2, Beta appears before Alpha
        v2_text = (
            "Section 2: Beta\nContent for section beta.\n\n"
            "Section 1: Alpha\nContent for section alpha."
        )

        summary = self.comparator.compare_texts(v1_text, v2_text)
        # Both sections should still align to their corresponding counterparts
        self.assertEqual(summary.added_count, 0)
        self.assertEqual(summary.removed_count, 0)
        # Both should be recognized as unchanged in content
        self.assertEqual(summary.unchanged_count, 2)

    # -------------------------------------------------------------
    # 5. Rewritten Section (Similar Meaning, Different Words)
    # -------------------------------------------------------------
    def test_05_rewritten_section(self):
        v1_text = (
            "Section 1: Attendance Rule\n"
            "Every scholar is mandated to attend no less than eighty percent of classroom sessions."
        )
        v2_text = (
            "Section 1: Attendance Rule\n"
            "Scholars are obligated to participate in a minimum of 80% of all scheduled lectures."
        )

        summary = self.comparator.compare_texts(v1_text, v2_text)
        self.assertEqual(len(summary.records), 1)
        rec = summary.records[0]
        self.assertEqual(rec.change_type, "modified")
        self.assertTrue(rec.verified)

    # -------------------------------------------------------------
    # 6. Number Change
    # -------------------------------------------------------------
    def test_06_number_change(self):
        v1_text = "Section 5: Credit Load\nStudents must register for 15 credit hours per semester."
        v2_text = "Section 5: Credit Load\nStudents must register for 14 credit hours per semester."

        summary = self.comparator.compare_texts(v1_text, v2_text)
        rec = summary.records[0]

        self.assertEqual(rec.change_type, "modified")
        number_changes = [ec for ec in rec.entities_changed if ec["entity"] == "number"]
        self.assertTrue(len(number_changes) > 0)
        self.assertEqual(number_changes[0]["old_value"], "15")
        self.assertEqual(number_changes[0]["new_value"], "14")

    # -------------------------------------------------------------
    # 7. Date Change
    # -------------------------------------------------------------
    def test_07_date_change(self):
        v1_text = "Section 4: Deadlines\nApplications are due by May 1, 2024."
        v2_text = "Section 4: Deadlines\nApplications are due by June 15, 2024."

        summary = self.comparator.compare_texts(v1_text, v2_text)
        rec = summary.records[0]

        self.assertEqual(rec.change_type, "modified")
        date_changes = [ec for ec in rec.entities_changed if ec["entity"] == "date"]
        self.assertTrue(len(date_changes) > 0)
        self.assertIn("May 1, 2024", date_changes[0]["old_value"])
        self.assertIn("June 15, 2024", date_changes[0]["new_value"])

    # -------------------------------------------------------------
    # 8. Currency Change
    # -------------------------------------------------------------
    def test_08_currency_change(self):
        v1_text = "Section 3: Limits\nMaximum scholarship is $5,000 per year."
        v2_text = "Section 3: Limits\nMaximum scholarship is $6,500 per year."

        summary = self.comparator.compare_texts(v1_text, v2_text)
        rec = summary.records[0]

        self.assertEqual(rec.change_type, "modified")
        currency_changes = [ec for ec in rec.entities_changed if ec["entity"] == "currency"]
        self.assertTrue(len(currency_changes) > 0)
        self.assertEqual(currency_changes[0]["old_value"], "$5,000")
        self.assertEqual(currency_changes[0]["new_value"], "$6,500")

    # -------------------------------------------------------------
    # 9. Similar Sections with Different Wording (Matching via normalized title/content)
    # -------------------------------------------------------------
    def test_09_similar_sections_with_different_wording(self):
        v1_text = "1. Student Financial Eligibility\nCandidates need an outstanding record and academic promise."
        v2_text = "Section 1: Financial Eligibility\nCandidates need exceptional scholarly merit and commitment."

        summary = self.comparator.compare_texts(v1_text, v2_text)
        self.assertEqual(len(summary.records), 1)
        rec = summary.records[0]
        # Should align via normalized title matching
        self.assertIn(rec.match_method, ("normalized_title", "exact_title", "tfidf_cosine"))
        self.assertTrue(rec.verified)

    # -------------------------------------------------------------
    # 10. Completely Unrelated Sections
    # -------------------------------------------------------------
    def test_10_completely_unrelated_sections(self):
        v1_text = "Section A: Physics Laboratory Safety\nWear safety goggles and thermal gloves at all times."
        v2_text = "Section B: Cafeteria Meal Plan Subscription\nLunch coupons can be recharged online via university portal."

        # Unrelated sections should NOT falsely align
        summary = self.comparator.compare_texts(v1_text, v2_text)
        self.assertEqual(summary.added_count, 1)
        self.assertEqual(summary.removed_count, 1)
        self.assertEqual(summary.modified_count, 0)

    # -------------------------------------------------------------
    # 11. Gold Changes Benchmark Evaluation (Precision, Recall, F1)
    # -------------------------------------------------------------
    def test_11_gold_changes_evaluation(self):
        gold_path = self.base_dir / "data" / "gold_changes.json"
        v1_path = self.base_dir / "data" / "policy_v1.txt"
        v2_path = self.base_dir / "data" / "policy_v2.txt"

        metrics = evaluate_comparator(self.comparator, gold_path, v1_path, v2_path)

        # Assert robust evaluation performance
        self.assertGreaterEqual(metrics["precision"], 0.80)
        self.assertGreaterEqual(metrics["recall"], 0.80)
        self.assertGreaterEqual(metrics["f1"], 0.85)


if __name__ == "__main__":
    unittest.main()
