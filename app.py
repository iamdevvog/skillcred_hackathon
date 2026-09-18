"""
Flask Web Application for Policy Document Comparison System.
Serves a modern HTML/CSS/JS frontend with real-time comparison APIs.
"""

from pathlib import Path
import json
import webbrowser
import threading
from typing import Dict, Any

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from src.document_parser import DocumentParser
from src.comparator import PolicyComparator
from src.evaluator import evaluate_comparator


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
CORS(app)


@app.route("/")
def index():
    """Serve the single-page HTML frontend."""
    return send_from_directory(str(STATIC_DIR), "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "Policy Document Comparison System"})


@app.route("/api/sample", methods=["GET"])
def get_sample_policies():
    """Load and return the pre-configured sample policy documents (V1 and V2)."""
    try:
        p1_path = BASE_DIR / "data" / "policy_v1.txt"
        p2_path = BASE_DIR / "data" / "policy_v2.txt"

        if not p1_path.exists() or not p2_path.exists():
            return jsonify({"error": "Sample policy files not found in data/ directory."}), 404

        text_v1 = DocumentParser.parse_txt(p1_path)
        text_v2 = DocumentParser.parse_txt(p2_path)

        return jsonify({
            "policy_v1": text_v1,
            "policy_v2": text_v2,
            "filename_v1": "policy_v1.txt",
            "filename_v2": "policy_v2.txt",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/compare", methods=["POST"])
def compare_policies():
    """
    Execute comparison between two documents.
    Accepts JSON body: { text_v1: str, text_v2: str, min_similarity_threshold: float }
    or multipart form files: file_v1, file_v2.
    """
    try:
        text_v1 = ""
        text_v2 = ""
        threshold = 0.40

        if request.is_json:
            data = request.get_json() or {}
            text_v1 = data.get("text_v1", "")
            text_v2 = data.get("text_v2", "")
            threshold = float(data.get("min_similarity_threshold", 0.40))
        elif request.files:
            file1 = request.files.get("file_v1")
            file2 = request.files.get("file_v2")
            if file1:
                text_v1 = DocumentParser.parse_document(file1.read(), filename=file1.filename)
            if file2:
                text_v2 = DocumentParser.parse_document(file2.read(), filename=file2.filename)
            threshold = float(request.form.get("min_similarity_threshold", 0.40))

        if not text_v1.strip() or not text_v2.strip():
            return jsonify({"error": "Both Version 1 and Version 2 content must be provided."}), 400

        comparator = PolicyComparator()
        comparator.aligner.min_similarity_threshold = threshold

        summary = comparator.compare_texts(text_v1, text_v2)

        # Build full JSON response including extra visual diff metadata
        records_payload = []
        for r in summary.records:
            record_dict = r.to_dict()
            record_dict["word_diff_html"] = r.word_diff_html
            record_dict["diff_magnitude"] = r.diff_magnitude
            record_dict["match_method"] = r.match_method
            records_payload.append(record_dict)

        response_payload = {
            "total_sections_v1": summary.total_sections_v1,
            "total_sections_v2": summary.total_sections_v2,
            "total_changes": summary.total_changes,
            "added": summary.added_count,
            "removed": summary.removed_count,
            "modified": summary.modified_count,
            "unchanged": summary.unchanged_count,
            "records": records_payload,
        }

        return jsonify(response_payload)

    except Exception as e:
        return jsonify({"error": f"Comparison pipeline failed: {str(e)}"}), 500


@app.route("/api/evaluate", methods=["GET"])
def evaluate_benchmark():
    """Run precision, recall, and F1 evaluation against gold_changes.json."""
    try:
        comparator = PolicyComparator()
        gold_path = BASE_DIR / "data" / "gold_changes.json"
        v1_path = BASE_DIR / "data" / "policy_v1.txt"
        v2_path = BASE_DIR / "data" / "policy_v2.txt"

        metrics = evaluate_comparator(comparator, gold_path, v1_path, v2_path)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def open_browser():
    """Open web browser after a brief delay."""
    webbrowser.open_new("http://127.0.0.1:5000")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" ⚖️  POLICY DOCUMENT COMPARISON SYSTEM - WEB UI")
    print("=" * 70)
    print(" Running at: http://127.0.0.1:5000")
    print(" Frontend  : Modern HTML5 / CSS3 / Vanilla JavaScript")
    print(" Backend   : Flask REST API + Deterministic NLP Engine")
    print("=" * 70 + "\n")

    # Launch browser automatically
    threading.Timer(1.2, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
