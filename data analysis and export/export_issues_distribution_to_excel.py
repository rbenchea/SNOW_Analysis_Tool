"""
Export merged SNOW ticket data and issue categories to Excel, 
and generate individual files for each category.
"""
import pandas as pd
from pathlib import Path
import argparse

# Importing from your provided data_analysis.py structure
from data_analysis import load_incidents, analyze_data


def export_to_excel(incident_path, output_dir):
    # 1. Load Data
    incidents = load_incidents(Path(incident_path))
    if incidents.empty:
        print("[ERROR] No data found.")
        return

    # 2. Analyze Data 
    # Matches the return signature: analyzed_df, summary, issue_trends, problem_report
    analyzed_df, summary, issue_trends, problem_report = analyze_data(incidents)

    # 3. Setup Output Folders
    output_base = Path(output_dir)
    categories_dir = output_base / "categorized_issues"
    categories_dir.mkdir(parents=True, exist_ok=True)

    # 4. Export the Master Excel File
    master_path = output_base / "issues_distribution_merged.xlsx"
    with pd.ExcelWriter(master_path, engine="xlsxwriter") as writer:
        analyzed_df.to_excel(writer, sheet_name="All_Incidents", index=False)
        issue_trends.to_excel(writer, sheet_name="Issue_Summary", index=False)
        if not problem_report.empty:
            problem_report.to_excel(writer, sheet_name="Problem_Report", index=False)
    
    print(f"[INFO] Master Excel file created at: {master_path}")

    # 5. Export individual files for each category
    # This addresses your request to export all categorized issues separately
    for category in analyzed_df["issue_type"].unique():
        # Filter data for this specific category
        category_data = analyzed_df[analyzed_df["issue_type"] == category]
        
        # Create a safe filename (remove spaces and special chars)
        safe_name = category.lower().replace(" ", "_").replace("/", "_")
        category_file_path = categories_dir / f"{safe_name}.xlsx"
        
        category_data.to_excel(category_file_path, index=False)
        print(f"[INFO] Exported {len(category_data)} tickets to: {category_file_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Export SNOW ticket data to Excel by category.")
    downloads_folder = Path.home() / "Downloads"
    
    parser.add_argument(
        "--incident",
        default=str(downloads_folder / "incident.csv"),
        help="Path to incident.csv",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: output)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    export_to_excel(args.incident, args.output)