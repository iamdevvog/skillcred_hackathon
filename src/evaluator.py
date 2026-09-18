"""
Evaluation module for computing Precision, Recall, and F1 metrics against gold benchmark datasets.
"""

import json
from pathlib import Path
from typing import Dict, Any, Union

from src.comparator import PolicyComparator, ComparisonSummary


def evaluate_comparator(
    comparator: PolicyComparator,
    gold_path: Union[str, Path],
    v1_path: Union[str, Path],
    v2_path: Union[str, Path],
) -> Dict[str, Any]:
    """
    Evaluate PolicyComparator against a gold standard benchmark.

    Args:
        comparator: Instance of PolicyComparator.
        gold_path: Path to gold_changes.json.
        v1_path: Path to document version 1.
        v2_path: Path to document version 2.

    Returns:
        Dictionary containing precision, recall, f1, true_positives, false_positives, and false_negatives.
    """
    gold_data = json.loads(Path(gold_path).read_text(encoding="utf-8"))
    summary = comparator.compare_files(v1_path, v2_path)

    # Build gold lookup: normalized title -> expected change_type
    gold_map: Dict[str, str] = {}
    for item in gold_data["changes"]:
        norm_title = item["section_title"].strip().lower()
        gold_map[norm_title] = item["change_type"]

    tp = 0
    fp = 0
    fn = 0

    # Check predicted records
    predicted_matched = set()

    for r in summary.records:
        r_title = r.section.strip().lower()
        pred_type = r.change_type

        # Match against gold entries
        matched_gold_key = None
        for g_key in gold_map:
            if g_key in r_title or r_title in g_key:
                matched_gold_key = g_key
                break

        if matched_gold_key:
            predicted_matched.add(matched_gold_key)
            expected_type = gold_map[matched_gold_key]
            if pred_type == expected_type:
                tp += 1
            else:
                fp += 1
        else:
            # Predicted change not in gold
            if pred_type != "unchanged":
                fp += 1

    # False negatives: gold changes not found or unmatched
    for g_key, expected_type in gold_map.items():
        if g_key not in predicted_matched and expected_type != "unchanged":
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    c = PolicyComparator()
    res = evaluate_comparator(
        c,
        base / "data" / "gold_changes.json",
        base / "data" / "policy_v1.txt",
        base / "data" / "policy_v2.txt",
    )
    print("=" * 50)
    print(" BENCHMARK EVALUATION RESULTS (V1 vs V2)")
    print("=" * 50)
    print(f" True Positives (TP) : {res['true_positives']}")
    print(f" False Positives (FP): {res['false_positives']}")
    print(f" False Negatives (FN): {res['false_negatives']}")
    print("-" * 50)
    print(f" Precision           : {res['precision']:.2%}")
    print(f" Recall              : {res['recall']:.2%}")
    print(f" F1 Score            : {res['f1']:.2%}")
    print("=" * 50)
