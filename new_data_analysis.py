import argparse
from pathlib import Path
from typing import List, Optional, Tuple
import traceback
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import re

def load_metrics(path: Path) -> pd.DataFrame:
    """Load metric instances. In your file, INC IDs are in the first column."""
    # We read with header=0 because your file has 'id,value,start...'
    metrics = pd.read_csv(path)
    
    # Extract incident number from the first column (named 'id')
    metrics["incident_number"] = metrics.iloc[:, 0].astype(str).str.extract(
        r"(?i)(INC\d+)", expand=False
    ).str.upper()

    print(f"[INFO] Total records loaded from metrics: {len(metrics)}")
    print(f"[INFO] Records with valid incident numbers: {metrics['incident_number'].notna().sum()}")
    return metrics

def load_incidents(path: Path) -> pd.DataFrame:
    """Load incidents and fix the column shift/data type issues."""
    # Explicitly set dtypes to prevent 'LossySetitemError' (float64 vs string)
    incidents = pd.read_csv(path, dtype={
        'number': str, 
        'state': str, 
        'problem_id': str,
        'sys_updated_by': str,
        'short_description': str
    })
    
    if "number" in incidents.columns:
        incidents["number"] = incidents["number"].astype(str).str.upper().str.strip()
    
    # Fix: In your CSV, the PRB IDs are actually sitting in the 'state' column
    if "state" in incidents.columns and "problem_id" in incidents.columns:
        mask = incidents["state"].str.contains("PRB", na=False)
        incidents.loc[mask, "problem_id"] = incidents.loc[mask, "state"]
        
    print(f"[INFO] Loaded {len(incidents)} incidents from incident.csv")
    return incidents

def load_problems(path: Path) -> pd.DataFrame:
    """Load problems from CSV."""
    if not path.exists():
        return pd.DataFrame()
    problems = pd.read_csv(path)
    if "problem_id" in problems.columns:
        problems["number"] = problems["problem_id"].astype(str).str.upper().str.strip()
    return problems

def _normalize_text(text: str) -> str:
    if pd.isna(text): return ""
    text = str(text).lower()
    return re.sub(r"[^a-z0-9\s]", " ", text).strip()

def categorize_issue(row: pd.Series) -> str:
    """Categorize issues based on Exercise 9: Shopping Cart requirements."""
    # Combine description and the 'sys_updated_by' column which holds error titles
    text = _normalize_text(str(row.get("short_description", "")) + " " + str(row.get("sys_updated_by", "")))
    
    if any(kw in text for kw in ["checkout", "timeout", "payment", "408"]):
        return "CHECKOUT ISSUES"
    if "vat" in text:
        return "VAT ISSUES"
    if any(kw in text for kw in ["stock", "inventory", "sync", "levels", "cart"]):
        return "STOCK ISSUES"
    if any(kw in text for kw in ["invoice", "billing", "rechnung"]):
        return "INVOICE/BILLING ISSUES"
        
    return "UNCATEGORIZED"

def analyze_data(incidents: pd.DataFrame, metrics: pd.DataFrame) -> Tuple:
    """Merge and analyze the datasets."""
    # Left merge to keep all metric records
    merged_data = metrics.merge(
        incidents[['number', 'short_description', 'sys_updated_by', 'problem_id', 'assignment_group']], 
        left_on="incident_number", 
        right_on="number", 
        how="left"
    )
    
    merged_data["issue_type"] = merged_data.apply(categorize_issue, axis=1)
    
    issue_trends = (
        merged_data.groupby("issue_type")
        .size()
        .reset_index(name="incident_count")
        .sort_values("incident_count", ascending=False)
    )

    summary = {
        "total_metrics": len(metrics),
        "unique_incidents": merged_data["number"].nunique(),
        "issue_types_found": merged_data["issue_type"].nunique()
    }
    
    return merged_data, summary, issue_trends

def create_visualizations(output_dir: Path, issue_trends: pd.DataFrame, total_count: int):
    """Generate the PNG distribution chart."""
    if issue_trends.empty:
        print("[WARNING] No data available for plotting.")
        return

    plt.figure(figsize=(12, 8))
    
    # Create colors
    colors = plt.cm.Paired(np.linspace(0, 1, len(issue_trends)))
    
    plt.pie(
        issue_trends["incident_count"], 
        labels=issue_trends["issue_type"], 
        autopct=lambda p: f'{p:.1f}%\n({int(p*total_count/100)} items)',
        colors=colors,
        startangle=140,
        pctdistance=0.85
    )
    
    # Draw a circle at the center to make it a donut chart (optional, looks cleaner)
    centre_circle = plt.Circle((0,0), 0.70, fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)

    plt.title(f"Shopping Cart System: Issue Distribution\nTotal Records: {total_count}", fontsize=14, fontweight='bold')
    
    output_dir.mkdir(parents=True, exist_ok=True)
    graph_path = output_dir / "03_issues_distribution.png"
    plt.savefig(graph_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Visualization successfully saved to: {graph_path}")

def main():
    # Setup paths
    downloads = Path.home() / "Downloads"
    # Note: using the specific filenames from your upload
    inc_path = Path("incident.csv") 
    met_path = Path("metric_instance.csv")
    prob_path = Path("problems.csv") 
    output_dir = Path("output")

    try:
        # 1. Load Data
        inc_df = load_incidents(inc_path)
        met_df = load_metrics(met_path)
        
        # 2. Analyze
        matched_incidents, summary, issue_trends = analyze_data(inc_df, met_df)
        
        # 3. Print Summary to Terminal
        print("\n" + "="*30)
        print("ANALYSIS SUMMARY")
        print("="*30)
        for k, v in summary.items():
            print(f"{k.replace('_', ' ').title()}: {v}")
        print("\nTop Issues:")
        print(issue_trends.to_string(index=False))

        # 4. Visualize
        create_visualizations(output_dir, issue_trends, summary["total_metrics"])
        
    except Exception as e:
        print(f"\n[ERROR] Critical failure: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()