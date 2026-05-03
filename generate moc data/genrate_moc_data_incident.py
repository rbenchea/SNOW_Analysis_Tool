import csv
import random
import re
import os
from pathlib import Path

def generate_incident_csv(input_file=None, problems_file=None, output_file=None):
    try:
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if input_file is None:
            input_file = output_dir / "metric_instance.csv"
        if problems_file is None:
            problems_file = output_dir / "problems.csv"
        if output_file is None:
            output_file = output_dir / "incident.csv"
        
        input_file = str(input_file)
        problems_file = str(problems_file)
        output_file = str(output_file)
        
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found.")
            return
        
        if not os.path.exists(problems_file):
            print(f"Error: {problems_file} not found.")
            return

        valid_problem_ids = []
        with open(problems_file, mode='r', encoding='utf-8') as pf:
            p_reader = csv.DictReader(pf, delimiter=';') 
            for p_row in p_reader:
                prob_id = p_row.get('number')
                if prob_id:
                    valid_problem_ids.append(prob_id)

        issue_templates = [
            ("Payment Gateway Timeout", "DataBase access issues"),
            ("Invalid VAT Calculation", "Issues while generating PDF documents"),
            ("Inventory Sync Failure", "Mismatch between reservation"),
            ("Cart Update Error", "Negative stock levels in the function"),
            ("Checkout Block", "User blocked during the checkout"),
            ("Invoice Failure", "Invoice generation fails due to unknown errors")
        ]

        # --- UPDATED STEP 2: Process Existing Metrics and Create Date Map ---
        existing_incidents = []
        date_mapping = {} # Dictionary to store { 'INC000123': '2023-01-01' }
        last_numeric_id = 0
        generic_date = "2026-01-01 00:00:00"

        with open(input_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_id = row['id']
                match = re.search(r'(\d+)', raw_id)
                if match:
                    num_part = match.group(1)
                    clean_id = f"INC{num_part.zfill(7)}"
                    existing_incidents.append(clean_id)
                    
                    # Store the date from the metric file
                    date_mapping[clean_id] = row.get('sys_created_on', generic_date)
                    
                    last_numeric_id = max(last_numeric_id, int(num_part))

        final_rows = []
        assignees = ["Raluca"] * 30 + ["Alexandru"] * 30 + ["George"] * 30 + [""] * 10
        
        # Process metrics-based incidents
        for inc_id in existing_incidents:
            desc, note = random.choice(issue_templates)
            final_rows.append({
                "number": inc_id,
                "assignment_group": "L3 Support",
                "assigned_to": random.choice(assignees),
                "description": desc,
                "work_notes": note,
                "problem_id": random.choice(valid_problem_ids),
                "sys_created_on": date_mapping.get(inc_id, generic_date) # Pull mapped date
            })

        # Process New Tickets (Randomized)
        for i in range(1, 201):
            next_id = f"INC{str(last_numeric_id + i).zfill(7)}"
            desc, note = random.choice(issue_templates)
            final_rows.append({
                "number": next_id,
                "assignment_group": random.choice(["L1 Support Group", "L2 Support Group", "L4 Support Group"]),
                "assigned_to": "ITIL User",
                "description": desc,
                "work_notes": note,
                "problem_id": random.choice(valid_problem_ids),
                "sys_created_on": generic_date # Add generic date for new ones
            })

        # Process Specific 404 Tickets
        for i in range(201, 288):
            next_id = f"INC{str(last_numeric_id + i).zfill(7)}"
            final_rows.append({
                "number": next_id,
                "assignment_group": random.choice(["L1 Support Group", "L2 Support Group"]),
                "assigned_to": "ITIL User",
                "description": "404 not found when clicking on the existing stock item",
                "work_notes": "Navigation error in stock item module",
                "problem_id": random.choice(valid_problem_ids),
                "sys_created_on": generic_date # Add generic date for new ones
            })

        # --- UPDATED STEP 5: Write to CSV with sys_created_on ---
        headers = [
            "number", "sys_created_on", "sys_updated_by", "short_description", "state", 
            "assignment_group", "assigned_to", "problem_id", "time_worked", 
            "group_list", "resolved_by", "description", "sys_domain", 
            "reassignment_count", "comments_and_work_notes"
        ]

        with open(output_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for row in final_rows:
                writer.writerow({
                    "number": row["number"],
                    "sys_created_on": row["sys_created_on"],
                    "sys_updated_by": "system_admin",
                    "short_description": row["description"],
                    "state": "6",
                    "assignment_group": row["assignment_group"],
                    "assigned_to": row["assigned_to"],
                    "problem_id": row["problem_id"],
                    "time_worked": "3600",
                    "group_list": "",
                    "resolved_by": "ITIL User" if row["assigned_to"] else "",
                    "description": f"System generated incident for {row['description']}",
                    "sys_domain": "global",
                    "reassignment_count": random.randint(0, 3),
                    "comments_and_work_notes": row["description"]
                })

        print(f"Success! Generated {len(final_rows)} total incidents to: {output_file}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    generate_incident_csv()