# MyGitProject-

## SNOW Analysis Tool

A data analysis tool for ServiceNow (SNOW) incident management. Process CSV files containing incidents to generate insights, categorizations, and visualizations. Access via CLI or web interface.

### Features

- **Data Loading**: Loads incident data from CSV files with encoding fallback support (UTF-8, Latin-1, CP1252).
- **Issue Categorization**: Automatically categorizes incidents into:
  - CHECKOUT ISSUES
  - STOCK SEARCH ISSUES
  - VAT ISSUES
  - PAYMENT ISSUES
  - STOCK/INVENTORY ISSUES
  - CART ISSUES
  - INVOICE ISSUES
  - UNCATEGORIZED
- **Problem ID Aggregation**: Groups incidents by Problem ID and counts associated tickets.
- **Analysis Summary**: Provides total incidents, tickets with problems, and unique issue type counts.
- **Visualizations**: 
  - Pie chart showing incident distribution by category
  - Table image displaying Problem IDs and incident counts
- **Web Interface**: FastAPI-based web UI for easy file upload and analysis.
- **Output**: Saves visualizations to the output directory.

### Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`:
  - pandas>=1.3.0
  - numpy>=1.21.0
  - matplotlib>=3.4.0
  - fastapi>=0.95.0
  - uvicorn>=0.21.0

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

### Option 1: Command Line (CLI)

Run the analysis script with default CSV file in the current directory:

```
python data_analysis.py
```

The script expects `incident.csv` in the current working directory.

### Option 2: Web Interface (FastAPI)

Start the web server:

```
python fastapi_app.py
```

Then open your browser to:
```
http://localhost:8000
```

**Features:**
- Upload incident CSV files directly via the web form
- Or specify file paths on your machine (defaults to `~/Downloads/incident.csv`)
- View generated visualizations in the browser
- Download visualization images

View a gallery of all generated visualizations:
```
http://localhost:8000/gallery
```

## Input Data Format

### incident.csv

Required columns:
- `number`: Incident number (will be normalized to uppercase)
- `short_description`: Brief description of the incident
- `description`: Full incident description
- `problem_id`: Associated Problem ID (format: PRB followed by numbers)

Example:
```
number,short_description,description,problem_id
INC0001,Checkout timeout,408 request timeout during checkout,PRB001
INC0002,Stock sync error,Inventory levels not syncing,PRB002
```

## Output

### Console Output (CLI)

```
==================================================
SNOW INCIDENT ANALYSIS SUMMARY
==================================================
Total Incidents        : 150
Tickets With Problem   : 45
Unique Issue Types     : 5

TOP PROBLEM ASSOCIATIONS:
Problem ID  Description              Incident Count
PRB001      Checkout timeout         12
PRB002      Stock sync error         8
...
```

### Generated Files

- `issues_distribution.png`: Pie chart of incident distribution by category
- `problem_report_table.png`: Table showing Problem IDs and associated incident counts

## Project Structure

```
proiect_final_wantsome/
├── data_analysis.py           # Core analysis logic
├── fastapi_app.py             # Web interface
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── tests/
│   └── test_data_analysis.py  # Unit tests
└── output/                    # Generated visualizations
```

## Testing

Run unit tests using pytest:

```bash
pytest tests/test_data_analysis.py -v
```

Tests cover:
- Text normalization and German character handling
- Issue categorization logic
- CSV loading with number column normalization
- Problem ID aggregation and grouping
- Visualization file generation

## Contributing

Feel free to contribute by submitting issues or pull requests.

## License

[Add your license information here]