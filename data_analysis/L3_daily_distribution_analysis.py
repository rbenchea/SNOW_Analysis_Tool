from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

L3_GROUP = "EU Support_L3"
L4_GROUP = "EU Support_L4"

COLUMN_SPECS = [
    ("Date", "Date", 12, "Analysis day from metric_instance.csv."),
    ("New Daily Tickets in L3 queue", "New Daily SNOWs\n(IN L3 queue)", 10, "New Daily SNOWS = new incidents that arrived IN L3 queue"),
    ("Resolved by L3", "Resolved by L3\n(EXIT from L3 queue)", 9, "Resolved by L3 = resolved incidents by L3 from the Current L3 queue OR New Daily SNOWS"),
    ("Reassignments", "Reassignments", 7, "Reassignments = the no of tickets were at least once previously assigned to EU Support_L3  SNOW group."),
    ("Distributed to L2", "From L3 To L2\n(EXIT from L3 queue)", 6, "From L3 To L2 = tickets that EXIT L3 and were routed to L2 by L3 from the Current L3 queue OR New Daily SNOWS"),
    ("Distributed to L4", "From L3 To L4\n(EXIT from L3 queue)", 6, "From L3 To L4 = tickets that EXIT L3 and were routed to L4 by L3 from the Current L3 queue OR New Daily SNOWS"),
    ("Third parties", "3rdParty\n(EXIT from L3 queue)", 8, "3rd Party = tickets that EXIT L3 and were routed to 3rd Party by L3 from the Current L3 queue OR New Daily SNOWS"),
    ("Existing L3 queue", "Current L3 queue", 9, "Open tickets currently in EU Support_L3 from incident.csv with an assignee (excluding closed/resolved/canceled)."),
    ("Total L3 queue", "Total L3 queue", 10, "Total L3 queue = New Daily SNOWs + Resolved by L3 + From L3 To L2 + From L3 To L4 + 3rdParty + Current L3 queue"),
]

def _parse_datetime_series(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    dt = pd.to_datetime(s, format="ISO8601", errors="coerce")
    fallback = pd.to_datetime(s, format="mixed", errors="coerce")
    return dt.fillna(fallback)

def _format_png_date_label(value: object) -> str:
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt): return str(value)
    date_text = dt.date().isoformat()
    return f"WEEKEND\n{date_text}" if dt.dayofweek in (5, 6) else date_text

def _prepare_png_display(daily_df: pd.DataFrame) -> pd.DataFrame:
    display = daily_df.copy().reset_index(drop=True)
    display["Date"] = display["Date"].apply(_format_png_date_label)
    return display

def load_metric_instance(path: Path) -> pd.DataFrame:
    metrics = pd.read_csv(path, header=None)
    col_names = ["metric_timestamp", "metric_type", "id_field", "value", "metric_start", "metric_end", "duration", "complete"]
    
    # Corrected: metrics.shape gets the column count
    metrics.columns = col_names[:metrics.shape]

    header_mask = (metrics["id_field"].astype(str).str.lower().str.contains("id") | 
                   metrics["metric_start"].astype(str).str.lower().str.contains("start"))
    metrics = metrics.loc[~header_mask].copy()

    metrics["id_field"] = metrics["id_field"].astype(str).str.strip()
    metrics["incident_number"] = metrics["id_field"].str.extract(r"(?i)(INC\d+)", expand=False).str.upper()
    metrics["value"] = metrics["value"].astype(str).fillna("").str.strip()
    metrics["start_dt"] = _parse_datetime_series(metrics["metric_start"])
    metrics["start_date"] = metrics["start_dt"].dt.date
    
    return metrics[metrics["incident_number"].notna()].copy()

def load_incidents(path: Path) -> pd.DataFrame:
    df = pd.DataFrame()
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except: continue
    
    if df.empty: return df

    df.columns = [str(c).strip().lower() for c in df.columns]
    
    rename_map = {}
    if "number" in df.columns: rename_map["number"] = "number"
    if "assignment_group" in df.columns: rename_map["assignment_group"] = "assignment_group"
    if "state" in df.columns: rename_map["state"] = "state"
    
    assignee_key = next((k for k in ["assigned_to", "assignee", "u_assigned_to"] if k in df.columns), None)
    if assignee_key: rename_map[assignee_key] = "assignee"
        
    df = df.rename(columns=rename_map)
    df["number"] = df["number"].astype(str).str.upper().str.strip()
    df["assignee"] = df["assignee"].fillna("").astype(str).str.strip()
    return df

def analyze_support_daily_distribution(metrics, incidents):
    dates = sorted(metrics["start_date"].dropna().unique())
    l3_rows = metrics[metrics["value"].str.contains(L3_GROUP, case=False, na=False)].copy()

    # Calculate New Daily Tickets entering L3
    new_daily = l3_rows.groupby("start_date").size().reindex(dates, fill_value=0)
    
    # Calculate daily reassignments (Incidents that hit L3 more than once)
    reassignment_counts = l3_rows.groupby(["start_date", "incident_number"]).size()
    daily_reassignments = reassignment_counts[reassignment_counts > 1].groupby(level=0).size().reindex(dates, fill_value=0)

    # Current snapshot of open L3 tickets
    active_mask = (incidents["assignment_group"].str.contains(L3_GROUP, case=False, na=False) & 
                   ~incidents["state"].str.contains("closed|resolved", case=False, na=False))
    baseline = incidents[active_mask]["number"].nunique()

    result = pd.DataFrame({
        "Date": dates,
        "New Daily Tickets in L3 queue": new_daily.values,
        "Reassignments": daily_reassignments.values,
        "Resolved by L3": 0,
        "Distributed to L2": 0,
        "Distributed to L4": 0,
        "Third parties": 0,
        "Existing L3 queue": baseline
    })
    
    # Calculate Total L3 queue (Sum columns 1-6 + Existing queue)
    result["Total L3 queue"] = result.iloc[:, 1:7].sum(axis=1) + result["Existing L3 queue"]
    
    return result

def print_summary(df):
    print("\n" + "=" * 80)
    print("SUPPORT DAILY DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    # Corrected: Added to check for Sat/Sun
    df["Date"] = pd.to_datetime(df["Date"])
    weekdays = df[~df["Date"].dt.dayofweek.isin()]
    weekends = df[df["Date"].dt.dayofweek.isin()]
    
    print(df.to_string(index=False))
    print("\n" + "-" * 80)
    print(f"Total Weekday Incoming: {weekdays['New Daily Tickets in L3 queue'].sum()}")
    print(f"Total Weekend Incoming: {weekends['New Daily Tickets in L3 queue'].sum()}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metric", default="metric_instance.csv")
    parser.add_argument("--incident", default="incident.csv")
    args = parser.parse_args()

    m_path, i_path = Path(args.metric), Path(args.incident)
    if not m_path.exists() or not i_path.exists():
        print(f"Files not found: {m_path} or {i_path}")
        return

    metrics = load_metric_instance(m_path)
    incidents = load_incidents(i_path)
    
    if metrics.empty or incidents.empty:
        print("Error: One or more source files are empty or could not be parsed.")
        return

    daily_df = analyze_support_daily_distribution(metrics, incidents)
    print_summary(daily_df)

if __name__ == "__main__":
    main()