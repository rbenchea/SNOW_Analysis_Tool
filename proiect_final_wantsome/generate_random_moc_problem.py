import csv
from collections import Counter

def generate_problems_csv(input_file="incident.csv", output_file="problems.csv"):
    # Dictionary to map Problem IDs to their Short Descriptions
    # We'll keep these consistent with the clusters from the previous step
    descriptions = {
        "PRB0001001": "Root Cause: Payment Gateway latency and timeout during peak hours",
        "PRB0001002": "Root Cause: Regional VAT rounding logic error in fiscal module",
        "PRB0001003": "Root Cause: Race condition between Redis cache and Inventory DB"
    }

    try:
        # 1. Read the incident file and count occurrences of each problem_id
        problem_counts = Counter()
        
        with open(input_file, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                problem_counts[row['problem_id']] += 1

        # 2. Write the unique problems to the new CSV
        with open(output_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["problem_id", "short_description", "child_tickets"])

            # Sort by ID to keep it tidy
            for prob_id in sorted(problem_counts.keys()):
                writer.writerow([
                    prob_id, 
                    descriptions.get(prob_id, "Unknown Problem"), 
                    problem_counts[prob_id]
                ])

        print(f"Successfully created {output_file} with {len(problem_counts)} unique problem records.")

    except FileNotFoundError:
        print(f"Error: {input_file} not found. Please run the incident generator first.")

if __name__ == "__main__":
    generate_problems_csv()