import csv
import random
from datetime import datetime, timedelta

def generate_metrics_csv(filename="metric_instance.csv", num_rows=400):
    # Configuration
    value = "L3 Support Group"
    definition = "Incident Assignment Group"
    start_id = 9855
    
    incident_ids = [f"Incident: INC{12220000 + i}" for i in range(start_id, start_id + num_rows)]
    
    def get_random_date(year, month):
        start_date = datetime(year, month, 1)
        # Random seconds within a 28-day window to stay safe within the month
        random_seconds = random.randint(0, 28 * 24 * 60 * 60 - 1)
        return start_date + timedelta(seconds=random_seconds)

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["sys_created_on", "definition", "id", "value", "metric_start", "metric_end", 
                         "duration", "calculation_complete"])
        
        for inc_id in incident_ids:
            # 1. Logic for Start and End
            # Generating start date in April 2026 as per your example
            start_dt = get_random_date(2026, 4)
            start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # 40% chance to have no end date
            if random.random() < 0.40:
                end_str = ""
                end_dt = None
            else:
                # End date is start date + random time (between 1 hour and 3 days)
                end_dt = start_dt + timedelta(seconds=random.randint(3600, 259200))
                end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

            # 2. Logic for Duration (in seconds)
            if end_dt:
                duration_delta = end_dt - start_dt
                duration = int(duration_delta.total_seconds())
            else:
                # If there is no end date, duration is typically 0 or empty 
                # (adjust based on your system requirements)
                duration = None

            # 3. Logic for Calculation Complete
            calculation_complete = "TRUE" if end_dt else "FALSE"

            # Use start date as sys_created_on for consistency
            sys_created_on = start_str 

            writer.writerow([
                sys_created_on, 
                definition, 
                inc_id, 
                value, 
                start_str, 
                end_str, 
                duration, 
                calculation_complete
            ])

    print(f"Successfully generated {filename} with {num_rows} rows.")

if __name__ == "__main__":
    generate_metrics_csv()