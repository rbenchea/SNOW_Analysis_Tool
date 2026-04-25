import csv
import random
import re
import os

def generate_incident_csv(input_file="metric_instance.csv", problems_file="problems.csv", output_file="incident.csv"):
    try:
        # --- 1. Validation and Problem ID Loading ---
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found.")
            return
        
        if not os.path.exists(problems_file):
            print(f"Error: {problems_file} not found. Please provide the problem instance.")
            return

        valid_problem_ids = []
        with open(problems_file, mode='r', encoding='utf-8') as pf:
            p_reader = csv.DictReader(pf, delimiter=';') 
            for p_row in p_reader:
                prob_id = p_row.get('number')
                if prob_id:
                    valid_problem_ids.append(prob_id)
        
        if not valid_problem_ids:
            print(f"Error: No IDs found in the 'number' column of {problems_file}.")
            return

        issue_templates = [
            ("Payment Gateway Timeout", "DataBase access issues"),
            ("Invalid VAT Calculation", "Issues while generating PDF documents"),
            ("Inventory Sync Failure", "Mismatch between reservation"),
            ("Cart Update Error", "Negative stock levels in the function"),
            ("Checkout Block", "User blocked during the checkout"),
            ("Invoice Failure", "Invoice generation fails due to unknown errors")
        ]

        # --- 2. Process Existing Metrics ---
        existing_incidents = []
        last_numeric_id = 0

        with open(input_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_id = row['id']
                match = re.search(r'(\d+)', raw_id)
                if match:
                    num_part = match.group(1)
                    clean_id = f"INC{num_part.zfill(7)}"
                    existing_incidents.append(clean_id)
                    last_numeric_id = max(last_numeric_id, int(num_part))

        final_rows = []
        assignees = ["Raluca"] * 30 + ["Alexandru"] * 30 + ["George"] * 30 + [""] * 10
        
        for inc_id in existing_incidents:
            desc, note = random.choice(issue_templates)
            final_rows.append({
                "number": inc_id,
                "assignment_group": "L3 Support",
                "assigned_to": random.choice(assignees),
                "description": desc,
                "work_notes": note,
                "problem_id": random.choice(valid_problem_ids) 
            })

        # --- 3. Logic for 200 New Tickets (Randomized) ---
        new_groups = (["L4 Support Group"] * 100 + 
                      ["L2 Support Group"] * 50 + 
                      ["L1 Support Group"] * 50)
        random.shuffle(new_groups)

        for i in range(1, 201):
            next_id = f"INC{str(last_numeric_id + i).zfill(7)}"
            desc, note = random.choice(issue_templates)
            final_rows.append({
                "number": next_id,
                "assignment_group": new_groups[i-1],
                "assigned_to": "ITIL User",
                "description": desc,
                "work_notes": note,
                "problem_id": random.choice(valid_problem_ids)
            })

        # --- 4. NEW: Logic for 87 Specific 404 Error Tickets ---
        # We start incrementing from 201 to reach 287 (200 random + 87 specific)
        specific_desc = "404 not found when clicking on the existing stock item"
        specific_note = "Navigation error in stock item module"
        
        for i in range(201, 288):
            next_id = f"INC{str(last_numeric_id + i).zfill(7)}"
            final_rows.append({
                "number": next_id,
                "assignment_group": random.choice(["L1 Support Group", "L2 Support Group"]),
                "assigned_to": "ITIL User",
                "description": specific_desc,
                "work_notes": specific_note,
                "problem_id": random.choice(valid_problem_ids)
            })

        # --- 5. Write to CSV ---
        headers = [
            "number", "sys_updated_by", "short_description", "state", "assignment_group",  
            "assigned_to", "problem_id", "time_worked", "group_list", "resolved_by", 
            "additional_assignee_list", "description", "sys_domain", "reassignment_count",
            "comments_and_work_notes"
        ]

        with open(output_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for row in final_rows:
                short_desc = row["description"]
                
                writer.writerow([
                    row["number"],
                    "system_admin",
                    short_desc,            
                    "6",
                    row["assignment_group"],
                    row["assigned_to"],
                    row["problem_id"],
                    "3600",
                    "",
                    "ITIL User" if row["assigned_to"] else "",
                    "",
                    f"System generated incident for {short_desc}",
                    "global",
                    random.randint(0, 3),
                    short_desc             
                ])

        print(f"Success! Generated {len(final_rows)} total incidents.")


    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    generate_incident_csv()