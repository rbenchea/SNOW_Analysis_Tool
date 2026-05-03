from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Adjusted Search Strings based on your incident.csv file
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

    # Date taken from sys_created_on from metric_instance
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

    # Remove "Incident: " prefix and whitespace to match the incident.csv format
    metrics['id_clean'] = metrics['id'].astype(str).str.replace("Incident: ", "", case=False).str.strip()
    incidents['number_clean'] = incidents['number'].astype(str).str.strip()
    
    # Merge using the cleaned IDs
    merged_incidents = pd.merge(
        incidents, 
        metrics[['id_clean', 'date_only']], 
        left_on='number_clean', 
        right_on='id_clean', 
        how='left'
    )

    dates = sorted(metrics["date_only"].dropna().unique())
    results = []

    for d in dates:
        # Filter for the specific day
        day_incidents = merged_incidents[merged_incidents["date_only"] == d]
        day_metrics = metrics[metrics["date_only"] == d]
        
        # Ensure the group column is treated as a string for searching
        group_col = day_incidents["assignment_group"].astype(str)
        
        results.append({
            "Date": d,
            "Total New Incidents": len(day_metrics),
            "Support L1": len(day_incidents[group_col.str.contains("L1", case=False, na=False)]),
            "Support L2": len(day_incidents[group_col.str.contains("L2", case=False, na=False)]),
            "Support L3": len(day_incidents[group_col.str.contains("L3", case=False, na=False)]),
            "Support L4": len(day_incidents[group_col.str.contains("L4", case=False, na=False)]),
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
    
    # Save at 300 DPI
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