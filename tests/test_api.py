"""
Integration tests for Flask API endpoints and web server.
"""

import json
import unittest
from app import app


class TestPolicyComparisonAPI(unittest.TestCase):
    """Test Flask endpoints for the HTML/CSS/JS frontend."""

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_route(self):
        res = self.app.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Policy Comparator", res.data)

    def test_health_route(self):
        res = self.app.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "ok")

    def test_sample_route(self):
        res = self.app.get("/api/sample")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("policy_v1", data)
        self.assertIn("policy_v2", data)
        self.assertIn("Eligibility Criteria", data["policy_v1"])

    def test_compare_endpoint(self):
        payload = {
            "text_v1": "Section 1: CGPA Requirement\nStudents must maintain a minimum CGPA of 7.0.",
            "text_v2": "Section 1: CGPA Requirement\nStudents must maintain a minimum CGPA of 7.5.",
            "min_similarity_threshold": 0.40,
        }
        res = self.app.post(
            "/api/compare",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        self.assertEqual(data["total_changes"], 1)
        self.assertEqual(data["modified"], 1)
        rec = data["records"][0]
        self.assertTrue(rec["verified"])
        self.assertEqual(rec["change_type"], "modified")
        self.assertEqual(rec["category"], "eligibility")
        # Check entities
        self.assertTrue(len(rec["entities_changed"]) > 0)
        self.assertEqual(rec["entities_changed"][0]["old_value"], "7.0")
        self.assertEqual(rec["entities_changed"][0]["new_value"], "7.5")

    def test_evaluate_endpoint(self):
        res = self.app.get("/api/evaluate")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("f1", data)
        self.assertGreaterEqual(data["f1"], 0.85)


if __name__ == "__main__":
    unittest.main()
