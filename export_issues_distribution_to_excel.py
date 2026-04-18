"""
Export merged SNOW ticket data and issue categories to Excel, matching the data used for 03_issues_distribution.png.
"""
import pandas as pd
from pathlib import Path
import argparse

from data_analysis import load_metrics, load_incidents, load_problems, analyze_data


def export_to_excel(incident_path, metric_path, problem_path, output_path):
    incidents = load_incidents(incident_path)
    metrics = load_metrics(metric_path)
    problems = load_problems(problem_path) if problem_path and Path(problem_path).exists() else None

    matched_incidents, summary, trends, top_applications, problem_tickets, issue_trends, top_issues = analyze_data(
        incidents, metrics
    )

    # Add percentage column to issue_trends as in the visualization
    total_tickets = issue_trends["incident_count"].sum()
    issue_trends = issue_trends.copy()
    if total_tickets > 0:
        issue_trends["percentage"] = (issue_trends["incident_count"] / total_tickets * 100)
    else:
        issue_trends["percentage"] = 0.0

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to Excel
    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        matched_incidents.to_excel(writer, sheet_name="Merged_Data", index=False)
        issue_trends.to_excel(writer, sheet_name="Issue_Categories", index=False)
        if problem_tickets is not None and len(problem_tickets) > 0:
            problem_tickets.to_excel(writer, sheet_name="Problem_Tickets", index=False)
        if problems is not None and len(problems) > 0:
            problems.to_excel(writer, sheet_name="Problems", index=False)
    print(f"[INFO] Excel file created at: {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Export merged SNOW ticket data and issue categories to Excel.")
    downloads_folder = Path.home() / "Downloads"
    parser.add_argument(
        "--incident",
        default=str(downloads_folder / "incident.csv"),
        help="Path to incident.csv (default: ~/Downloads/incident.csv)",
    )
    parser.add_argument(
        "--metric",
        default=str(downloads_folder / "metric_instance.csv"),
        help="Path to metric_instance.csv (default: ~/Downloads/metric_instance.csv)",
    )
    parser.add_argument(
        "--problem",
        default=str(downloads_folder / "problem.csv"),
        help="Path to problem.csv (default: ~/Downloads/problem.csv)",
    )
    parser.add_argument(
        "--output",
        default="output/issues_distribution_merged.xlsx",
        help="Path to output Excel file (default: output/issues_distribution_merged.xlsx)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    export_to_excel(args.incident, args.metric, args.problem, args.output)
