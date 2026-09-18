"""
Streamlit Web Interface for Policy Document Comparison System.

Features:
- Dual document upload (.txt files) or 1-click sample policy loader
- Real-time comparison pipeline execution
- Metrics dashboard: Total Changes, Added, Removed, Modified
- Structured change log table (Section, Change Type, Category, Similarity, Verification)
- Side-by-side evidence viewer with exact excerpts
- Inline word-level visual diff highlighting additions (<ins>) and deletions (<del>)
- Critical entity/threshold change tracker (CGPA, currency, dates, percentages)
- Strict evidence verification enforcement (No AI explanation without aligned old/new evidence pair)
"""

from pathlib import Path
import streamlit as st
import pandas as pd

from src.document_parser import DocumentParser
from src.comparator import PolicyComparator


st.set_page_config(
    page_title="Policy Document Comparison System",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling for clean diff presentation and badges
st.markdown(
    """
    <style>
    .metric-box {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #0366d6;
        margin-bottom: 10px;
    }
    .badge-verified {
        background-color: #28a745;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
    }
    .badge-unverified {
        background-color: #dc3545;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
    }
    .diff-container {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
        line-height: 1.6;
        padding: 16px;
        background-color: #fafbfc;
        border: 1px solid #e1e4e8;
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    st.title("⚖️ Policy Document Comparison System")
    st.caption("Deterministic textual comparison, semantic section alignment & critical threshold tracking.")

    # Sidebar: File Uploads & Settings
    st.sidebar.header("📁 Document Ingestion")

    use_sample = st.sidebar.checkbox(
        "Load Sample Policies (V1 vs V2)",
        value=True,
        help="Use built-in University Scholarship Policy V1 and V2 sample files",
    )

    doc1_content: str | None = None
    doc2_content: str | None = None
    name_v1 = "Version 1"
    name_v2 = "Version 2"

    base_dir = Path(__file__).resolve().parent
    v1_sample_path = base_dir / "data" / "policy_v1.txt"
    v2_sample_path = base_dir / "data" / "policy_v2.txt"

    if use_sample and v1_sample_path.exists() and v2_sample_path.exists():
        doc1_content = DocumentParser.parse_txt(v1_sample_path)
        doc2_content = DocumentParser.parse_txt(v2_sample_path)
        name_v1 = "policy_v1.txt (Sample)"
        name_v2 = "policy_v2.txt (Sample)"
        st.sidebar.success("Sample documents loaded.")

    upload_v1 = st.sidebar.file_uploader("Upload Version 1 (.txt)", type=["txt"], key="upload_v1")
    upload_v2 = st.sidebar.file_uploader("Upload Version 2 (.txt)", type=["txt"], key="upload_v2")

    if upload_v1 is not None:
        doc1_content = DocumentParser.parse_txt(upload_v1)
        name_v1 = upload_v1.name

    if upload_v2 is not None:
        doc2_content = DocumentParser.parse_txt(upload_v2)
        name_v2 = upload_v2.name

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Alignment Settings")
    min_sim_threshold = st.sidebar.slider(
        "Minimum Alignment Similarity Threshold",
        min_value=0.10,
        max_value=0.90,
        value=0.40,
        step=0.05,
        help="Cosine similarity cutoff to consider two sections aligned if titles differ",
    )

    compare_clicked = st.sidebar.button("🔍 COMPARE DOCUMENTS", type="primary", use_container_width=True)

    if not doc1_content or not doc2_content:
        st.info("👈 Please select sample documents or upload two text files in the sidebar to begin.")
        return

    # Execute Comparison
    comparator = PolicyComparator()
    comparator.aligner.min_similarity_threshold = min_sim_threshold

    with st.spinner("Analyzing document structure, aligning sections, and calculating diffs..."):
        summary = comparator.compare_texts(doc1_content, doc2_content)

    # -------------------------------------------------------------
    # 1. Summary Metrics
    # -------------------------------------------------------------
    st.subheader("📊 Comparison Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Changes", summary.total_changes)
    c2.metric("Added Sections", summary.added_count, delta=f"+{summary.added_count}" if summary.added_count else None)
    c3.metric("Removed Sections", summary.removed_count, delta=f"-{summary.removed_count}" if summary.removed_count else None, delta_color="inverse")
    c4.metric("Modified Sections", summary.modified_count)
    c5.metric("Unchanged Sections", summary.unchanged_count)

    st.divider()

    # -------------------------------------------------------------
    # 2. Structured Change Log Table
    # -------------------------------------------------------------
    st.subheader("📑 Structured Change Log")

    filter_type = st.radio(
        "Filter Changes by Type:",
        ["All Changes", "Modified Only", "Added Only", "Removed Only", "All Sections (including unchanged)"],
        horizontal=True,
    )

    filtered_records = []
    for r in summary.records:
        if filter_type == "All Changes" and r.change_type != "unchanged":
            filtered_records.append(r)
        elif filter_type == "Modified Only" and r.change_type == "modified":
            filtered_records.append(r)
        elif filter_type == "Added Only" and r.change_type == "added":
            filtered_records.append(r)
        elif filter_type == "Removed Only" and r.change_type == "removed":
            filtered_records.append(r)
        elif filter_type == "All Sections (including unchanged)":
            filtered_records.append(r)

    if not filtered_records:
        st.info("No records match the selected filter.")
    else:
        table_rows = []
        for r in filtered_records:
            table_rows.append({
                "Section": r.section,
                "Change Type": r.change_type.upper(),
                "Category": r.category.capitalize(),
                "Similarity": f"{r.similarity:.2f}",
                "Verified Evidence": "✅ VERIFIED" if r.verified else "⚠️ SINGLE-DOC",
                "Entities Changed": len(r.entities_changed),
            })

        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------------------------------------------
    # 3. Section Evidence Inspector
    # -------------------------------------------------------------
    st.subheader("🔍 Section Evidence Inspector")

    options = [f"[{r.change_type.upper()}] {r.section}" for r in summary.records]
    selected_idx = st.selectbox(
        "Select a section to inspect verified evidence and value changes:",
        range(len(options)),
        format_func=lambda i: options[i],
    )

    selected_record = summary.records[selected_idx]

    # Verification Status Banner
    v_col1, v_col2 = st.columns([3, 1])
    with v_col1:
        st.markdown(f"### {selected_record.section}")
        st.write(f"**Category:** `{selected_record.category}` | **Alignment Method:** `{selected_record.match_method}` | **Similarity Score:** `{selected_record.similarity:.2f}`")
    with v_col2:
        if selected_record.verified:
            st.success("✅ **VERIFIED EVIDENCE**\n\nAligned old/new pair exists.")
        else:
            st.warning("⚠️ **UNVERIFIED**\n\nSingle-document evidence only (Addition or Deletion).")

    # Value / Threshold Changes
    if selected_record.entities_changed:
        st.markdown("#### 🎯 Detected Value & Threshold Changes")
        val_rows = []
        for ec in selected_record.entities_changed:
            val_rows.append({
                "Entity": ec["entity"].upper(),
                "Old Value": ec["old_value"] if ec["old_value"] is not None else "—",
                "New Value": ec["new_value"] if ec["new_value"] is not None else "—",
            })
        st.table(pd.DataFrame(val_rows))
    else:
        st.info("No numeric or threshold entity changes detected in this section.")

    # Side-by-side Excerpts
    st.markdown("#### 📜 Source Text Excerpts")
    col_old, col_new = st.columns(2)

    with col_old:
        st.markdown(f"**OLD VERSION ({name_v1})**")
        if selected_record.old_text:
            st.text_area("Old Excerpt", selected_record.old_text, height=220, disabled=True, key=f"old_text_{selected_idx}")
        else:
            st.info("(Section was not present in Old Version — Added section)")

    with col_new:
        st.markdown(f"**NEW VERSION ({name_v2})**")
        if selected_record.new_text:
            st.text_area("New Excerpt", selected_record.new_text, height=220, disabled=True, key=f"new_text_{selected_idx}")
        else:
            st.info("(Section was removed in New Version — Deleted section)")

    # Inline Visual Diff
    if selected_record.change_type == "modified":
        st.markdown("#### 🔀 Inline Visual Diff")
        st.caption("Red strike-through = deleted text, Green highlight = inserted text")
        st.markdown(
            f'<div class="diff-container">{selected_record.word_diff_html}</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
