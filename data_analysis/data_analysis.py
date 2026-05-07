from pathlib import Path
from typing import List, Tuple
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import re

def load_incidents(path: Path = None) -> pd.DataFrame:
    """Load incidents from incident.csv with encoding fallback."""
    if path is None:
        path = Path(__file__).parent.parent / "output" / "incident.csv"
    
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            incidents = pd.read_csv(path, encoding=encoding)
            if "number" in incidents.columns:
                incidents["number"] = incidents["number"].astype(str).str.upper().str.strip()
            print(f"[INFO] Loaded {len(incidents)} incidents from {path}")
            return incidents
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    print(f"[ERROR] Could not load incidents from {path}")
    return pd.DataFrame()

def load_problems(path: Path = None) -> pd.DataFrame:
    """Load problems from problems.csv with encoding fallback."""
    if path is None:
        path = Path(__file__).parent.parent / "output" / "problems.csv"
    
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            problems = pd.read_csv(path, encoding=encoding)
            print(f"[INFO] Loaded {len(problems)} problems from {path}")
            return problems
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    print(f"[WARNING] Could not load problems from {path}")
    return pd.DataFrame()

def load_metric_instance(path: Path = None) -> pd.DataFrame:
    """Load metric instances from metric_instance.csv with encoding fallback."""
    if path is None:
        path = Path(__file__).parent.parent / "output" / "metric_instance.csv"
    
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            metrics = pd.read_csv(path, encoding=encoding)
            print(f"[INFO] Loaded {len(metrics)} metric instances from {path}")
            return metrics
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    print(f"[WARNING] Could not load metric instances from {path}")
    return pd.DataFrame()

def _normalize_text(text: str) -> str:
    if pd.isna(text): return ""
    text = str(text).lower()
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def _contains_any(desc: str, keywords: List[str]) -> bool:
    return any(re.search(rf"\b{re.escape(kw)}\b", desc) for kw in keywords)

def categorize_issue(description: str) -> str:
    if pd.isna(description) or not description:
        return "UNCATEGORIZED"
    desc_lower = _normalize_text(description)

    if _contains_any(desc_lower, ["checkout", "checkout block", "408 request timeout"]):
        return "CHECKOUT ISSUES"
    if _contains_any(desc_lower, ["404 not found", "stock issue", "stock item"]):
        return "STOCK SEARCH ISSUES"
    if _contains_any(desc_lower, ["vat", "tax"]):
        return "VAT ISSUES"
    if _contains_any(desc_lower, ["payment", "gateway"]):
        return "PAYMENT ISSUES"
    if _contains_any(desc_lower, ["stock", "inventory", "sync", "levels"]):
        return "STOCK/INVENTORY ISSUES"
    if _contains_any(desc_lower, ["cart", "cart update"]):
        return "CART ISSUES"
    if _contains_any(desc_lower, ["invoice", "billing"]):
        return "INVOICE ISSUES"
    
    return "UNCATEGORIZED"

def analyze_data(incidents: pd.DataFrame, problems: pd.DataFrame = None, metrics: pd.DataFrame = None) -> Tuple:
    if incidents.empty:
        return pd.DataFrame(), {}, pd.DataFrame(), pd.DataFrame()

    # Combine descriptions for categorization
    incidents["full_description"] = (
            incidents["short_description"].fillna("").astype(str) + " " +
            incidents["description"].fillna("").astype(str)
    )
    incidents["issue_type"] = incidents["full_description"].apply(categorize_issue)

    # Clean and identify valid Problem IDs
    incidents["problem_id_mapped"] = incidents["problem_id"].apply(
        lambda x: str(x).strip().upper() if pd.notna(x) and str(x).upper().startswith("PRB") else np.nan
    )

    summary = {
        "total_incidents": len(incidents),
        "tickets_with_problem": incidents["problem_id_mapped"].notna().sum(),
        "unique_issue_types": incidents["issue_type"].nunique(),
    }

    issue_trends = incidents.groupby("issue_type").size().reset_index(name="count").sort_values("count", ascending=False)
    
    # Enhanced: Group by Problem ID and capture assignment_group, short_description (title), and count
    problem_report = incidents[incidents["problem_id_mapped"].notna()].groupby("problem_id_mapped").agg({
        "assignment_group": "first",      # Take first assignment group
        "short_description": "first",     # Take first title/description
        "problem_id": "count"             # Count incidents
    }).reset_index()
    
    problem_report.columns = ["Problem ID", "Assignment Group", "Title", "Total SNOW Tickets"]
    problem_report = problem_report.sort_values("Total SNOW Tickets", ascending=False)
    
    return incidents, summary, issue_trends, problem_report

def create_problem_table_img(output_dir: Path, problem_report: pd.DataFrame):
    if problem_report.empty: 
        print("[INFO] No Problem IDs found to generate table.")
        return
    
    # Adjust figure size based on amount of data
    fig_height = max(3, len(problem_report) * 0.6 + 1.5)
    fig, ax = plt.subplots(figsize=(18, fig_height))
    ax.axis('off')
    
    # Create the table with 4 columns
    tbl = ax.table(
        cellText=problem_report.values,
        colLabels=problem_report.columns,
        cellLoc='left',
        loc='center',
        colWidths=[0.12, 0.18, 0.55, 0.15],
        colColours=["#2F5597"] * 4
    )
    
    # Styling
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.8)
    
    # Style header and cells
    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.get_text().set_color('white')
            cell.get_text().set_weight('bold')
        cell.set_edgecolor('#D9D9D9')
        # Enable text wrapping for title column
        if col == 2:
            cell.set_text_props(wrap=True)

    plt.title("Problem IDs and Associated Incident Details", fontsize=16, pad=20, weight='bold')
    
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "problem_report_table.png"
    plt.savefig(str(table_path), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[INFO] ✓ Problem table saved to: {table_path}")

def create_visualizations(output_dir: Path, issue_trends: pd.DataFrame, total_tickets: int = 0):
    if issue_trends.empty: return
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(10, 8))
    colors = plt.cm.Blues(np.linspace(0.8, 0.4, len(issue_trends)))
    
    # Create donut chart
    wedges, texts, autotexts = plt.pie(
        issue_trends["count"], 
        labels=issue_trends["issue_type"], 
        autopct='%1.1f%%', 
        startangle=140, 
        colors=colors,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1}
    )
    
    # Create donut hole
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    plt.gca().add_artist(centre_circle)
    
    plt.title(f"Incident Distribution by Category | Total Tickets: {total_tickets}", fontsize=14)
    
    graph_path = output_dir / "issues_distribution.png"
    plt.savefig(str(graph_path), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[INFO] ✓ Visualization saved to: {graph_path}")

def main():
    output_dir = Path(__file__).parent.parent / "output"
    input_dir = Path(__file__).parent.parent / "input"
    incident_path = input_dir / "incident.csv"
    problems_path = input_dir / "problems.csv"
    metric_path = input_dir / "metric_instance.csv"


    incidents = load_incidents(incident_path)
    problems = load_problems(problems_path)
    metrics = load_metric_instance(metric_path)
    
    if incidents.empty:
        print("[ERROR] No data found in incident.csv")
        return

    _, _, issue_trends, problem_report = analyze_data(incidents, problems, metrics)
    
    # Get total tickets from metrics
    total_tickets = len(metrics) if not metrics.empty else 0
    
    create_visualizations(output_dir, issue_trends, total_tickets)
    create_problem_table_img(output_dir, problem_report)

    # Print Summary Results
    print("\n" + "=" * 50)
    print("SNOW INCIDENT ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"[INFO] Total tickets (metrics): {total_tickets}")
    print(f"[INFO] Total incidents: {len(incidents)}")
    if not problems.empty:
        print(f"[INFO] Total problems loaded: {len(problems)}")
    
    print("\nTOP PROBLEM ASSOCIATIONS:")
    print(problem_report.to_string(index=False))

if __name__ == "__main__":
    main()