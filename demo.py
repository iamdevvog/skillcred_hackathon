"""
Interactive demonstration of Policy Document Comparison System.
Compares policy_v1.txt and policy_v2.txt and displays:
- Section alignments (added, removed, modified, reordered)
- Textual similarity scores
- Critical entity & value changes (CGPA, dates, currency, percentages)
- Verification status (strictly verified only when aligned old/new pair exists)
"""

from pathlib import Path
from src.comparator import PolicyComparator


def main():
    base_dir = Path(__file__).resolve().parent
    v1_path = base_dir / "data" / "policy_v1.txt"
    v2_path = base_dir / "data" / "policy_v2.txt"

    print("=" * 80)
    print(" POLICY DOCUMENT COMPARISON SYSTEM - DEMO")
    print("=" * 80)

    comparator = PolicyComparator()
    summary = comparator.compare_files(v1_path, v2_path)

    print(f"Total Sections V1: {summary.total_sections_v1}")
    print(f"Total Sections V2: {summary.total_sections_v2}")
    print(f"Total Changes    : {summary.total_changes}")
    print(f"  - Added        : {summary.added_count}")
    print(f"  - Removed      : {summary.removed_count}")
    print(f"  - Modified     : {summary.modified_count}")
    print(f"  - Unchanged    : {summary.unchanged_count}")
    print("-" * 80)

    for idx, r in enumerate(summary.records, 1):
        badge = f"[{r.change_type.upper()}]"
        verified_str = "VERIFIED" if r.verified else "UNVERIFIED (Single Document Evidence)"
        print(f"\n{idx:02d}. {badge.ljust(12)} {r.section}")
        print(f"    Category   : {r.category} | Similarity: {r.similarity:.2f} | Status: {verified_str}")
        print(f"    Alignment  : {r.match_method}")

        if r.entities_changed:
            print("    Value Changes:")
            for ec in r.entities_changed:
                print(f"      * {ec['entity']}: '{ec['old_value']}' -> '{ec['new_value']}'")

    print("\n" + "=" * 80)
    print(" Demonstration complete.")
    print("=" * 80)


if __name__ == "__main__":
    main()
