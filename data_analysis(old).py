import argparse
from pathlib import Path
from typing import List, Optional, Tuple
import traceback
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import re
from matplotlib.lines import Line2D

def load_metrics(path: Path) -> pd.DataFrame:
    """Load metric instances and extract incident IDs."""
    # Read with default headers as the file contains them
    metrics = pd.read_csv(path)

    # FIX: Use the 'id' column from your CSV to create 'id_field'
    if "id" in metrics.columns:
        metrics["id_field"] = metrics["id"].astype(str).str.strip()
    else:
        metrics["id_field"] = ""

    metrics["incident_number"] = metrics["id_field"].str.extract(
        r"(?i)(INC\d+)",
        expand=False
    ).str.upper()

    print(f"[INFO] Total records loaded from metrics: {len(metrics)}")
    return metrics

def load_incidents(path: Path) -> pd.DataFrame:
    """Load incidents from incident.csv with encoding fallback."""
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            incidents = pd.read_csv(path, encoding=encoding)
            if "number" in incidents.columns:
                incidents["number"] = incidents["number"].astype(str).str.upper().str.strip()
            print(f"[INFO] Loaded {len(incidents)} incidents from incident.csv (encoding: {encoding})")
            return incidents
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not read {path}")

def load_problems(path: Path) -> pd.DataFrame:
    """Load problems from problems.csv."""
    try:
        problems = pd.read_csv(path)
        if "number" in problems.columns:
            problems["number"] = problems["number"].astype(str).str.upper().str.strip()
        print(f"[INFO] Loaded {len(problems)} problems from problems.csv")
        return problems
    except Exception:
        return pd.DataFrame()

def _normalize_text(text: str) -> str:
    if text is None: return ""
    text = str(text).lower()
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss") #e pt limba gemerna
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def _contains_any(desc: str, keywords: List[str]) -> bool:
    return any(re.search(rf"\b{re.escape(kw)}\b", desc) for kw in keywords)

def categorize_issue(description: str) -> str:
    if pd.isna(description) or not description:
        return "UNCATEGORIZED"
    desc_lower = _normalize_text(description)

    if _contains_any(desc_lower, ["checkout", "408 request timeout", "payment step"]):
        return "CHECKOUT ISSUES"
    if _contains_any(desc_lower, ["vat"]):
        return "VAT ISSUES"
    if _contains_any(desc_lower, ["invoice", "billing", "rechnung"]):
        return "INVOICE/BILLING ISSUES"
    if _contains_any(desc_lower, ["stock", "inventory", "cart", "levels"]):
        return "STOCK ISSUES"
    
    return "UNCATEGORIZED"

def analyze_data(incidents: pd.DataFrame, metrics: pd.DataFrame) -> Tuple:
    # Select available columns. Note: your Problem IDs are in the 'state' column
    incident_cols = ["number", "short_description", "description", "state", "assignment_group"]
    available_cols = [col for col in incident_cols if col in incidents.columns]

    merged_data = metrics.merge(
        incidents[available_cols],
        left_on="incident_number",
        right_on="number",
        how="left"
    )

    # Use short_description for categorization since description is empty in your file
    merged_data["full_description"] = (
            merged_data["short_description"].fillna("").astype(str) + " " +
            merged_data["description"].fillna("").astype(str)
    )
    merged_data["issue_type"] = merged_data["full_description"].apply(categorize_issue)

    # Map problem_id from the 'state' column
    merged_data["problem_id_mapped"] = merged_data["state"].apply(lambda x: x if str(x).startswith("PRB") else np.nan)

    # Extract dates from 'value' column in metrics
    if "value" in merged_data.columns:
        merged_data["date_parsed"] = pd.to_datetime(merged_data["value"], errors="coerce")
        merged_data["year_week"] = merged_data["date_parsed"].dt.strftime('%Y-W%U')

    summary = {
        "total_incidents_in_metrics": len(merged_data),
        "total_unique_incidents": merged_data["number"].nunique(),
        "tickets_with_problem": merged_data["problem_id_mapped"].notna().sum(),
        "percentage_with_problem": f"{(merged_data['problem_id_mapped'].notna().sum()/len(merged_data)*100):.1f}%" if len(merged_data) > 0 else "0%",
        "unique_applications": merged_data["start"].nunique() if "start" in merged_data.columns else 0,
        "total_unique_problems": merged_data["problem_id_mapped"].nunique(),
        "unique_issue_types": merged_data["issue_type"].nunique(),
    }

    top_applications = merged_data.groupby("start").size().reset_index(name="incident_count").sort_values("incident_count", ascending=False) if "start" in merged_data.columns else pd.DataFrame()
    issue_trends = merged_data.groupby("issue_type").size().reset_index(name="incident_count").sort_values("incident_count", ascending=False)
    
    problem_tickets = merged_data[merged_data["problem_id_mapped"].notna()].copy()
    problem_tickets["problem_id"] = problem_tickets["problem_id_mapped"]
    problem_tickets["application"] = problem_tickets["start"] if "start" in problem_tickets.columns else "Unknown"

    return merged_data, summary, pd.DataFrame(), top_applications, problem_tickets, issue_trends, pd.DataFrame()

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="SNOW Analysis Tool")
    parser.add_argument("--incident", default="incident.csv", help="Path to incident.csv")
    parser.add_argument("--metric", default="metric_instance.csv", help="Path to metric_instance.csv")
    parser.add_argument("--problem", default="problems.csv", help="Path to problems.csv")
    parser.add_argument("--output-dir", default="output", help="Directory to write graphs")
    return parser.parse_args(argv)

def print_results(matched_incidents, summary, trends, top_apps, prob_tickets, issue_trends, top_issues, problems):
    print("\n" + "=" * 60)
    print("SNOW ANALYSIS SUMMARY")
    print("=" * 60)
    for k, v in summary.items():
        print(f"{k.replace('_', ' ').title():<30}: {v}")
    
    print("\nTOP ISSUE TYPES:")
    print(issue_trends.head(10).to_string(index=False))

def create_visualizations(output_dir: Path, matched_incidents: pd.DataFrame, issue_trends: pd.DataFrame):
    """Create a monochromatic blue pie chart with shades based on incident volume."""
    try:
        if issue_trends.empty:
            print("[WARNING] No data available for visualization.")
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Sort data so the highest number is first (to map to darkest color)
        issue_trends = issue_trends.sort_values("incident_count", ascending=False).copy()
        
        total = issue_trends["incident_count"].sum()
        issue_trends["percentage"] = (issue_trends["incident_count"] / total * 100)

        # 2. Generate shades of blue
        # 'Blues' is a sequential colormap. We take a range (e.g., 0.3 to 0.9) 
        # so the lightest color isn't pure white.
        num_categories = len(issue_trends)
        colors = plt.cm.Blues(np.linspace(0.9, 0.3, num_categories))

        fig, ax = plt.subplots(figsize=(12, 10))
        
        # 3. Generate Pie Chart
        wedges, texts, autotexts = ax.pie(
            issue_trends["incident_count"], 
            labels=issue_trends["issue_type"], 
            autopct='%1.1f%%', 
            startangle=140, 
            pctdistance=0.85,
            colors=colors,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1} # Adds clean separation
        )

        plt.setp(autotexts, size=10, weight="bold", color="white")

        # 4. Legend logic for all issues (with highlight for those < 10%)
        legend_labels = []
        for _, row in issue_trends.iterrows():
            label = f"{row['issue_type']}: {int(row['incident_count'])} ({row['percentage']:.1f}%)"
            if row['percentage'] < 10:
                label += " *" # Marking minor issues
            legend_labels.append(label)

        ax.legend(
            legend_labels,
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )

        ax.set_title(f"Incident Distribution", fontsize=14)
        
        graph_path = output_dir / "03_issues_distribution.png"
        plt.savefig(str(graph_path), dpi=300, bbox_inches="tight")
        plt.close()
        
        print(f"[INFO] ✓ Monochromatic pie chart saved to: {graph_path}")
            
    except Exception as e:
        print(f"[ERROR] Failed to create monochromatic visualization: {e}")

def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir)

    incident_path = Path(args.incident)
    metric_path = Path(args.metric)
    problem_path = Path(args.problem)

    if not incident_path.exists() or not metric_path.exists():
        print(f"[ERROR] Files not found. Check: {incident_path} and {metric_path}")
        return 1

    incidents = load_incidents(incident_path)
    metrics = load_metrics(metric_path)
    problems = load_problems(problem_path)

    # These are the variable names returned by the function
    (matched_incidents, summary, trends, top_apps, 
     prob_tickets, issue_trends, top_issues) = analyze_data(incidents, metrics)

    # Generate the PNG
    create_visualizations(output_dir, matched_incidents, issue_trends)

    # FIX: Use the correct variable names (top_apps and prob_tickets)
    print_results(
        matched_incidents, 
        summary, 
        trends, 
        top_apps,          # Changed from top_applications
        prob_tickets,      # Changed from problem_tickets
        issue_trends, 
        top_issues, 
        problems
    )
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())