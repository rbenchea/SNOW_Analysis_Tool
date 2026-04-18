# MyGitProject-

## SNOW Analysis Tool

This project provides a data analysis tool for ServiceNow (SNOW) incident management data. It processes CSV files containing incidents, metric instances, and problems to generate insights, categorizations, and visualizations.

### Features

- **Data Loading**: Loads incident, metric, and problem data from CSV files with encoding fallback support.
- **Issue Categorization**: Automatically categorizes incidents into types such as CHECKOUT ISSUES, VAT ISSUES, INVOICE/BILLING ISSUES, STOCK ISSUES, and UNCATEGORIZED.
- **Analysis**: Provides summaries including total incidents, unique problems, issue trends, and top applications affected.
- **Visualization**: Generates a monochromatic blue pie chart showing incident distribution by issue type.
- **Output**: Saves visualizations to an output directory and prints detailed analysis results to the console.

### Requirements

- Python 3.x
- Dependencies listed in `requirements.txt`:
  - pandas>=1.3.0
  - numpy>=1.21.0
  - matplotlib>=3.4.0

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd MyGitProject-
   ```

2. Navigate to the project folder:
   ```
   cd proiect_final_wantsome
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Usage

Run the analysis script with default CSV files:

```
python data_analysis.py
```

Or specify custom file paths:

```
python data_analysis.py --incident path/to/incident.csv --metric path/to/metric_instance.csv --problem path/to/problems.csv --output-dir path/to/output
```

### Arguments

- `--incident`: Path to the incident CSV file (default: `incident.csv`)
- `--metric`: Path to the metric instance CSV file (default: `metric_instance.csv`)
- `--problem`: Path to the problems CSV file (default: `problems.csv`)
- `--output-dir`: Directory to save output visualizations (default: `output`)

### Output

- Console output with analysis summary, top issue types, and statistics.
- Pie chart visualization saved as `03_issues_distribution.png` in the output directory.

### Data Files

- `incident.csv`: Contains incident data with columns like number, short_description, description, state, assignment_group.
- `metric_instance.csv`: Contains metric instances linked to incidents.
- `problems.csv`: Contains problem records.

### Example Output

```
============================================================
SNOW ANALYSIS SUMMARY
============================================================
Total Incidents In Metrics     : 150
Total Unique Incidents         : 120
Tickets With Problem           : 45
Percentage With Problem        : 30.0%
Unique Applications            : 10
Total Unique Problems          : 15
Unique Issue Types             : 5

TOP ISSUE TYPES:
issue_type  incident_count
CHECKOUT ISSUES    50
UNCATEGORIZED     40
STOCK ISSUES      30
...
```

### Contributing

Feel free to contribute by submitting issues or pull requests.