from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def _parse_datetime_series(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    dt = pd.to_datetime(s, format="ISO8601", errors="coerce")
    fallback = pd.to_datetime(s, format="mixed", errors="coerce")
    return dt.fillna(fallback)

def load_metric_instance(path: Path) -> pd.DataFrame:
    if not path.exists(): 
        print(f"Warning: {path} not found.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    
    if "sys_created_on" in df.columns:
        df["dt"] = _parse_datetime_series(df["sys_created_on"])
        df["date_only"] = df["dt"].dt.date
    return df

def load_incidents(path: Path) -> pd.DataFrame:
    if not path.exists(): 
        print(f"Warning: {path} not found.")
        return pd.DataFrame()
    df = pd.DataFrame()
    # Handle various encodings common in CSV exports
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

    # 1. CLEAN IDs: Remove "Incident: " prefix from metrics to match incident.csv
    metrics['id_clean'] = metrics['id'].astype(str).str.replace("Incident: ", "", case=False).str.strip()
    incidents['number_clean'] = incidents['number'].astype(str).str.strip()
    
    # 2. MERGE: Link incidents to dates from the metrics file
    merged_incidents = pd.merge(
        incidents, 
        metrics[['id_clean', 'date_only']], 
        left_on='number_clean', 
        right_on='id_clean', 
        how='left'
    )

    # 3. FALLBACK: Use incident sys_created_on if no metric match (for generic dates)
    merged_incidents['final_date'] = merged_incidents['date_only'].fillna(
        pd.to_datetime(merged_incidents['sys_created_on'], errors='coerce').dt.date
    )

    # 4. AGGREGATE
    all_dates = sorted(merged_incidents['final_date'].dropna().unique())
    results = []

    for d in all_dates:
        day_incidents = merged_incidents[merged_incidents['final_date'] == d]
        day_metrics = metrics[metrics['date_only'] == d]
        
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
    
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    print(f"Success: Analysis saved to {output_path}")

def main():
    # SET PATHS: Moving up two levels to the "output" folder
    output_folder = Path(__file__).parent.parent / "output"
    
    m_path = output_folder / "metric_instance.csv"
    i_path = output_folder / "incident.csv"
    save_path = output_folder / "analysis_table.png"

    metrics = load_metric_instance(m_path)
    incidents = load_incidents(i_path)
    
    final_df = analyze_data(metrics, incidents)
    
    if not final_df.empty:
        print(final_df.to_string(index=False))
        save_as_image(final_df, save_path)
    else:
        print("Analysis failed. Ensure CSV files exist in the 'output' directory.")

if __name__ == "__main__":
    main()