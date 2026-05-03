from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Adjusted Search Strings based on your incident.csv snippet
# Using substrings ensures "L3 Support" is captured even if the script looks for "L3"
L2_SEARCH = "L2"
L3_SEARCH = "L3"
L4_SEARCH = "L4"

def _parse_datetime_series(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    dt = pd.to_datetime(s, format="ISO8601", errors="coerce")
    fallback = pd.to_datetime(s, format="mixed", errors="coerce")
    return dt.fillna(fallback)

def load_metric_instance(path: Path) -> pd.DataFrame:
    if not path.exists(): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Requirement 1: Date taken from sys_created_on
    if "sys_created_on" in df.columns:
        df["dt"] = _parse_datetime_series(df["sys_created_on"])
        df["date_only"] = df["dt"].dt.date
    return df

def load_incidents(path: Path) -> pd.DataFrame:
    if not path.exists(): return pd.DataFrame()
    df = pd.DataFrame()
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except: continue
    
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def analyze_data(metrics, incidents):
    if metrics.empty or incidents.empty:
        return pd.DataFrame()

    dates = sorted(metrics["date_only"].dropna().unique())
    results = []
    
    # Requirement 3: Total existing tickets (len of 'number' column)
    total_existing = len(incidents["number"]) if "number" in incidents.columns else 0

    # Requirement 4-7: Group counts using flexible substring matching
    # This captures "L3 Support" as requested
    group_col = incidents["assignment_group"].astype(str)
    
    l2_count = len(incidents[group_col.str.contains(L2_SEARCH, case=False, na=False)])
    l3_count = len(incidents[group_col.str.contains(L3_SEARCH, case=False, na=False)])
    l4_count = len(incidents[group_col.str.contains(L4_SEARCH, case=False, na=False)])

    for d in dates:
        day_metrics = metrics[metrics["date_only"] == d]
        
        # Requirement 2: Total new incidents (len of 'id' column from metric_instance.csv)
        new_incidents = len(day_metrics["id"]) if "id" in day_metrics.columns else 0
        
        results.append({
            "Date": d,
            "Total New Incidents": new_incidents,
            "Total Existing Tickets": total_existing,
            "Support Group L1 (L2 Count)": l2_count,
            "Support Group L3": l3_count,
            "Support Group L4 (L4 Count)": l4_count
        })
    
    return pd.DataFrame(results)

def save_as_image(df, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Setup the table figure
    fig, ax = plt.subplots(figsize=(14, len(df) * 0.6 + 2))
    ax.axis('tight')
    ax.axis('off')
    
    table = ax.table(
        cellText=df.values, 
        colLabels=df.columns, 
        loc='center', 
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    # Save at 300 DPI as requested
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    print(f"Success: Analysis saved to {output_path}")

def main():
    # Use the requested path logic
    output_folder = Path(__file__).parent.parent / "output"

    parser = argparse.ArgumentParser()
    parser.add_argument("--metric", default=output_folder / "metric_instance.csv")
    parser.add_argument("--incident", default=output_folder / "incident.csv")
    args = parser.parse_args()

    m_path = Path(args.metric)
    i_path = Path(args.incident)

    if not m_path.exists() or not i_path.exists():
        print(f"Error: Files not found in {output_folder}")
        return

    metrics = load_metric_instance(m_path)
    incidents = load_incidents(i_path)
    
    final_df = analyze_data(metrics, incidents)
    
    if not final_df.empty:
        print(final_df.to_string(index=False))
        save_as_image(final_df, output_folder / "analysis_table.png")
    else:
        print("Data analysis failed. Please check file column headers.")

if __name__ == "__main__":
    main()