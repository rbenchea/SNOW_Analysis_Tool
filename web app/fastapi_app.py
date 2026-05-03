"""
FastAPI web interface for the SNOW Analysis Tool.
Updated to match data_analysis.py logic.
"""

import io
import contextlib
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Import from data_analysis module (go up one level to parent directory)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_analysis import (
    load_incidents,
    load_problems,
    load_metric_instance,
    analyze_data,
    create_visualizations,
    create_problem_table_img
)

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="SNOW Analysis Tool")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# --- HTML HELPERS ---

def _base_html(body: str, title: str = "SNOW Analysis Tool") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; background:#f5f7fa; color:#333; }}
    .card {{ background:#fff; border-radius:8px; padding:24px; margin:24px 0; box-shadow:0 2px 6px rgba(0,0,0,.1); }}
    label {{ font-weight:bold; display:block; margin-top:12px; }}
    input {{ width:100%; padding:8px; margin-top:4px; border:1px solid #ccc; border-radius:4px; box-sizing:border-box; }}
    button {{ margin-top:18px; padding:10px 28px; background:#2980b9; color:#fff; border:none; border-radius:5px; cursor:pointer; }}
    .img-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(400px,1fr)); gap:20px; }}
    .img-card img {{ max-width:100%; border-radius:4px; border: 1px solid #ddd; }}
    .msg {{ padding:12px; border-radius:5px; margin:12px 0; }}
    .error {{ background:#fadbd8; color:#c0392b; }}
    .log {{ background:#1e1e1e; color:#d4d4d4; padding:16px; border-radius:6px; font-family:monospace; font-size:12px; white-space:pre-wrap; }}
  </style>
</head>
<body>
  <div class="nav"><a href="/">🏠 Home</a> | <a href="/gallery">🖼 Gallery</a></div>
  {body}
</body>
</html>"""

def _upload_form() -> str:
    downloads = Path.home() / "Downloads"
    default_incident = downloads / "incident.csv"
    default_metric   = downloads / "metric_instance.csv"
    default_problem  = downloads / "problem.csv"
    return f"""
<div class="card">
  <h1>📊 SNOW Analysis Tool</h1>
  <p>Upload your CSV files <strong>or</strong> leave the fields empty to use the default
     <code>~/Downloads/</code> paths.</p>

  <form method="post" action="/run" enctype="multipart/form-data">
    <h2>Option A — Upload files directly</h2>
    <label>incident.csv</label>
    <input type="file" name="incident_file" accept=".csv"/>

    <label>metric_instance.csv</label>
    <input type="file" name="metric_file" accept=".csv"/>

    <label>problem.csv (optional)</label>
    <input type="file" name="problem_file" accept=".csv"/>

    <h2>Option B — Use file paths on this machine</h2>
    <label>Path to incident.csv</label>
    <input type="text" name="incident_path" placeholder="{default_incident}"/>

    <label>Path to metric_instance.csv</label>
    <input type="text" name="metric_path" placeholder="{default_metric}"/>

    <label>Path to problem.csv (optional)</label>
    <input type="text" name="problem_path" placeholder="{default_problem}"/>

    <button type="submit">▶ Run Analysis</button>
  </form>
</div>
"""

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def index():
    return _base_html(_upload_form())

@app.post("/run", response_class=HTMLResponse)
async def run_analysis(
    incident_file: Optional[UploadFile] = File(None),
    incident_path: Optional[str] = Form(None),
):
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        # Resolve incident file - check output folder first
        output_folder = OUTPUT_DIR
        default_output_incident = output_folder / "incident.csv"
        
        if incident_file and incident_file.filename:
            inc_path = tmp_dir / "incident.csv"
            inc_path.write_bytes(await incident_file.read())
        elif incident_path and incident_path.strip():
            inc_path = Path(incident_path.strip())
        elif default_output_incident.exists():
            inc_path = default_output_incident
        else:
            inc_path = Path.home() / "Downloads" / "incident.csv"

        if not inc_path.exists():
            return _base_html(f'<div class="msg error">❌ File not found at {inc_path}</div>' + _upload_form())

        # RUN ANALYSIS
        captured = io.StringIO()
        
        with contextlib.redirect_stdout(captured):
            incidents = load_incidents(inc_path)
            problems = load_problems()
            metrics = load_metric_instance()
            
            if not incidents.empty:
                _, summary, issue_trends, problem_report = analyze_data(incidents, problems, metrics)
                
                create_visualizations(OUTPUT_DIR, issue_trends)
                create_problem_table_img(OUTPUT_DIR, problem_report)
            else:
                raise ValueError("Incident file was empty or could not be read.")

        logs = captured.getvalue()
        
        # Build image display
        images = sorted(OUTPUT_DIR.glob("*.png"))
        img_html = '<div class="img-grid">' + "".join([
            f'<div class="img-card"><img src="/output/{img.name}"><br><a href="/output/{img.name}" download>Download</a></div>' 
            for img in images
        ]) + "</div>"

        return _base_html(f"""
            <div class="card">
                <h1>✅ Analysis Complete</h1>
                {img_html}
                <h3>Console Summary</h3>
                <div class="log">{logs}</div>
            </div>
        """)

    except Exception as e:
        return _base_html(f'<div class="msg error">❌ Error: {str(e)}</div>' + _upload_form())
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

@app.get("/gallery", response_class=HTMLResponse)
async def gallery():
    images = sorted(OUTPUT_DIR.glob("*.png"))
    img_html = "".join([f'<img src="/output/{i.name}" style="width:45%; margin:10px;">' for i in images])
    return _base_html(f'<div class="card"><h1>Gallery</h1>{img_html if img_html else "No images yet."}</div>')

if __name__ == "__main__":
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=True)