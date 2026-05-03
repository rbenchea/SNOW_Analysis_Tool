import sys
from pathlib import Path
import pandas as pd
import pytest

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_analysis import (
    load_incidents,
    analyze_data,
    categorize_issue,
    create_problem_table_img
)

def test_normalize_text_and_categorize():
    # Normalize: german chars, punctuation and extra spaces
    src = "  Grüß,  VAT issue! Checkout-block?  "
    normalized = da._normalize_text(src)
    assert "gruess" in normalized or "grues" in normalized
    assert "vat" in normalized

    # Categorize specific cases
    assert da.categorize_issue("Checkout blocked with 408 request timeout") == "CHECKOUT ISSUES"
    assert da.categorize_issue("We have a VAT discrepancy") == "VAT ISSUES"
    assert da.categorize_issue("Cannot find product - 404 not found") == "STOCK SEARCH ISSUES"
    assert da.categorize_issue("Payment gateway failure") == "PAYMENT ISSUES"
    assert da.categorize_issue("") == "UNCATEGORIZED"
    assert da.categorize_issue(None) == "UNCATEGORIZED"

def test_load_incidents_and_number_normalization(tmp_path):
    csv_path = tmp_path / "incident.csv"
    csv_content = "number,short_description,description,problem_id,assignment_group\n  abC123  ,short,desc,PRB001,GROUP_A\n"
    csv_path.write_text(csv_content, encoding="utf-8")

    df = da.load_incidents(csv_path)
    assert not df.empty
    # number column should be uppercased and stripped
    assert df.loc[0, "number"] == "ABC123"

def test_analyze_data_and_problem_report():
    # Create a DataFrame with two incidents sharing same problem_id (with mixed-case and spaces)
    df = pd.DataFrame([
        {"short_description": "checkout timeout", "description": "", "problem_id": " prb001 ", "assignment_group": "GROUP_A"},
        {"short_description": "checkout error", "description": "408 request timeout", "problem_id": "PRB001", "assignment_group": "GROUP_A"},
        {"short_description": "unrelated", "description": "some note", "problem_id": pd.NA, "assignment_group": "GROUP_B"},
    ])

    analyzed_df, summary, issue_trends, problem_report = da.analyze_data(df)

    # Summary checks
    assert summary["total_incidents"] == 3
    assert summary["tickets_with_problem"] == 2
    assert summary["unique_issue_types"] >= 1

    # Problem report should aggregate the two PRB001 into one entry with count 2
    assert not problem_report.empty
    # Verify new column structure: Problem ID, Assignment Group, Title, Total SNOW Tickets
    assert list(problem_report.columns) == ["Problem ID", "Assignment Group", "Title", "Total SNOW Tickets"]
    entry = problem_report[problem_report["Problem ID"] == "PRB001"]
    assert not entry.empty
    assert int(entry["Total SNOW Tickets"].iloc[0]) == 2

def test_create_problem_table_img_writes_file(tmp_path):
    # Prepare a small problem_report DataFrame with new 4-column format
    problem_report = pd.DataFrame({
        "Problem ID": ["PRB001", "PRB002"],
        "Assignment Group": ["GROUP_A", "GROUP_B"],
        "Title": ["desc1", "desc2"],
        "Total SNOW Tickets": [2, 1]
    })

    out_dir = tmp_path / "out"
    # Ensure no error is raised and file is created
    da.create_problem_table_img(out_dir, problem_report)

    expected_file = out_dir / "problem_report_table.png"
    assert expected_file.exists() and expected_file.stat().st_size > 0

def test_create_problem_table_img_empty_report(tmp_path):
    # Test handling of empty problem_report
    problem_report = pd.DataFrame({
        "Problem ID": [],
        "Assignment Group": [],
        "Title": [],
        "Total SNOW Tickets": []
    })

    out_dir = tmp_path / "out"
    # Should not raise an error
    da.create_problem_table_img(out_dir, problem_report)
    # No file should be created for empty data
    assert not list(out_dir.glob("*.png"))

def test_categorize_issue_multiple_keywords():
    # Test that issue categorization works with various keyword combinations
    assert da.categorize_issue("Stock inventory levels sync issue") == "STOCK/INVENTORY ISSUES"
    assert da.categorize_issue("Invoice billing problem") == "INVOICE ISSUES"
    assert da.categorize_issue("Cart update failed") == "CART ISSUES"
