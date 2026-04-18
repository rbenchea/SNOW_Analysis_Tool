import csv
import random
from datetime import datetime, timedelta

def generate_metrics_csv(filename="metric_instance.csv", num_rows=400):
    # Configuration
    assignment_group = "raluca_test"
    start_id = 9855
    
    # Generate unique incident IDs (INC12226518 and onwards)
    incident_ids = [f"INC{str(i).zfill(7)}" for i in range(start_id, start_id + num_rows)]
    
    # Function to get a random date in January 2026
    def get_random_january_date():
        start_date = datetime(2026, 1, 1)
        # Random number of seconds in 31 days
        random_seconds = random.randint(0, 31 * 24 * 60 * 60 - 1)
        return (start_date + timedelta(seconds=random_seconds)).strftime("%Y-%m-%d %H:%M:%S")

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Writing Header
        writer.writerow(["id","value", "start", "end duration", "calculation_complete"])
        
        # Writing Rows
        for inc_id in incident_ids:
            writer.writerow([inc_id, get_random_january_date(), assignment_group])

    print(f"Successfully generated {filename} with {num_rows} rows.")

if __name__ == "__main__":
    generate_metrics_csv()