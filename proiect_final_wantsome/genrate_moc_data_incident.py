import csv
import random

def generate_incident_csv(input_file="metric_instance.csv", output_file="incident.csv"):
    # Define the issue clusters with descriptions and work notes
    clusters = [
        {
            "description": "Payment Gateway Timeout",
            "work_notes": "User unable to complete checkout; 408 Request Timeout at payment step.",
            "problem_id": "PRB0081193",
            "weight": 50  # 50%
        },
        {
            "description": "Invalid VAT Calculation",
            "work_notes": "VAT applying incorrectly to cross-border category items.",
            "problem_id": "PRB0080942",
            "weight": 30  # 30%
        },
        {
            "description": "Inventory Sync Failure",
            "work_notes": "Stock levels in cart do not match database availability.",
            "problem_id": "PRB0080942",
            "weight": 20  # 20%
        },
        {
            "description": "Inventory Sync Failure",
            "work_notes": "Payment issues that are reflected in the invoice",
            "problem_id": "PRB0081530",
            "weight": 20  # 20%
        }

    ]

    try:
        # Read IDs from the metrics file
        with open(input_file, mode='r') as f:
            reader = csv.DictReader(f)
            incident_ids = [row['id'] for row in reader]

        # Prepare the weighted choices
        # We multiply the clusters by their weights to create a pool for random.choice
        population = []
        for c in clusters:
            population.extend([c] * c['weight'])

        with open(output_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["number", "sys_updated_by", "short_description", "state", "assignment_group",	
                             "assigned_to", "problem_id", "time_worked", "group_list", "resolved_by", 
                             "additional_assignee_list", "description", "sys_domain","reassignment_count",
                               "comments_and_work_notes"])

            for inc_id in incident_ids:
                # Assign a cluster based on the weights
                issue = random.choice(population)
                
                writer.writerow([
                    inc_id, 
                    issue["description"], 
                    issue["work_notes"], 
                    issue["problem_id"]
                ])

        print(f"Successfully created {output_file} with {len(incident_ids)} entries.")

    except FileNotFoundError:
        print(f"Error: {input_file} not found. Please run the metrics generator first.")

if __name__ == "__main__":
    generate_incident_csv()