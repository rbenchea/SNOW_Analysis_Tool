import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

def get_problem_timestamp_map(incident_file, metric_file):
    """
    Links Incident IDs to Problem IDs and fetches the creation timestamp.
    Returns: { 'PRB0001001': '2026-04-01 12:00:00' }
    This is done to reflect data realistically how these are in SNOW
    """
    inc_to_prb = {}
    prb_to_timestamp = {}

    try:
        # Step 1: Map Incident ID to Problem ID
        with open(incident_file, mode='r', encoding='utf-8') as f:
            # Assuming ',' delimiter (standard CSV)
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('number') and row.get('problem_id'):
                    inc_to_prb[row['number']] = row['problem_id']

        # Step 2: Map Incident ID to its Timestamp from metrics
        with open(metric_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inc_id = row.get('id')
                timestamp = row.get('sys_created_on')
                
                # If this Incident is linked to a Problem, store the timestamp
                if inc_id in inc_to_prb and timestamp:
                    target_prb = inc_to_prb[inc_id]
                    # We store the earliest timestamp found for the problem
                    current_dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    
                    if target_prb not in prb_to_timestamp or current_dt < prb_to_timestamp[target_prb]:
                        prb_to_timestamp[target_prb] = current_dt

        return prb_to_timestamp

    except FileNotFoundError as e:
        print(f"File missing: {e}")
        return {}

def generate_problems_csv(incident_file=None, metric_file=None, output_file=None):
    # Setup output directory paths 
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set default paths to output folder
    if incident_file is None:
        incident_file = output_dir / "incident.csv"
    if metric_file is None:
        metric_file = output_dir / "metric_instance.csv"
    if output_file is None:
        output_file = output_dir / "problems.csv"
    
    # Convert to strings for file operations
    incident_file = str(incident_file)
    metric_file = str(metric_file)
    output_file = str(output_file)
    
    descriptions = {
        "PRB0001001": "Database deadlocks during concurrent stock updates for Flash Sale items",
        "PRB0001002": "PDF Generation Service failing to map VAT rates for international addresses",
        "PRB0001003": "Mismatch between cart Reservation timestamp and actual warehouse availability",
        "PRB0001004": "408 Request Timeout during the final payment step due to unoptimized SQL queries.",
        "PRB0001005": "Missing billing address fields in the API payload causing invoice generation to fail.",
        "PRB0001006": "Negative stock levels allowed due to lack of atomic operations in the cart update function",
        "PRB0001007": "Incorrect currency conversion applied to VAT totals for non-Euro transactions ",
        "PRB0001008": "User blocked at payment step because the checkout session ID was invalidated by a firewall rule.",
        "PRB0001009": "Stock levels not synchronizing between the mobile app and web frontend due to a stale Redis cache.",
        "PRB0001010": "Missing invoice template headers causing 500 errors in the billing export tool"
    }

    headers = [
        "number", "sys_created_on", "short_description", "priority", 
        "state", "resolution_code", "assignment_group", "assigned_to", 
        "sys_updated_on", "sys_updated_by"
    ]

    # Get the timestamps linked via incident.csv
    time_map = get_problem_timestamp_map(incident_file, metric_file)

    try:
        with open(output_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=';')
            writer.writeheader()

            for prob_id, desc in sorted(descriptions.items()):
                # Use linked date or fallback to a default if no incident link exists
                if prob_id in time_map:
                    created_date = time_map[prob_id]
                else:
                    created_date = datetime(2026, 4, 1) # Static fallback
                
                updated_date = created_date + timedelta(days=2)
                
                writer.writerow({
                    "number": prob_id,
                    "sys_created_on": created_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "short_description": desc,
                    "priority": random.choice(["1 - Critical", "2 - High", "3 - Moderate"]),
                    "state": "3",
                    "resolution_code": "Fix Applied",
                    "assignment_group": "Problem Management",
                    "assigned_to": "Admin User",
                    "sys_updated_on": updated_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "sys_updated_by": "system_admin"
                })

        print(f"Success: {output_file} created using cross-referenced timestamps.")

    except Exception as e:
        print(f"Error during file writing: {e}")

if __name__ == "__main__":
    generate_problems_csv()