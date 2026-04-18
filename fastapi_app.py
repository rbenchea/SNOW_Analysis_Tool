"""
FastAPI web interface for the SNOW Analysis Tool.

Run with:
    uvicorn fastapi_app:app --reload --port 8000

Then open: http://localhost:8000
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from data_analysis_with_fastapi import (
    load_incidents,
    load_metrics,
    load_problems,
    analyze_data,
    analyze_uncategorized_issues,
    create_visualizations,
)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="SNOW Analysis Tool")

# Serve generated images as static files
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def _base_html(body: str, title: str = "SNOW Analysis Tool") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; background:#f5f7fa; color:#333; }}
    h1   {{ color:#2c3e50; }}
    h2   {{ color:#34495e; border-bottom:2px solid #bdc3c7; padding-bottom:6px; }}
    .card {{ background:#fff; border-radius:8px; padding:24px; margin:24px 0; box-shadow:0 2px 6px rgba(0,0,0,.1); }}
    label {{ font-weight:bold; display:block; margin-top:12px; }}
    input[type=file], input[type=text] {{ width:100%; padding:8px; margin-top:4px; border:1px solid #ccc; border-radius:4px; box-sizing:border-box; }}
    button {{ margin-top:18px; padding:10px 28px; background:#2980b9; color:#fff; border:none; border-radius:5px; font-size:15px; cursor:pointer; }}
    button:hover {{ background:#1a6fa0; }}
    .img-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(420px,1fr)); gap:20px; }}
    .img-card {{ background:#fff; border-radius:8px; padding:16px; box-shadow:0 2px 6px rgba(0,0,0,.1); text-align:center; }}
    .img-card img {{ max-width:100%; border-radius:4px; cursor:pointer; }}
    .img-card a {{ display:block; margin-top:8px; font-size:13px; color:#2980b9; }}
    .msg {{ padding:12px 18px; border-radius:5px; margin:12px 0; }}
    .success {{ background:#d5f5e3; color:#1e8449; }}
    .error   {{ background:#fadbd8; color:#c0392b; }}
    .nav {{ margin-bottom:20px; }}
    .nav a {{ margin-right:14px; color:#2980b9; text-decoration:none; font-weight:bold; }}
    .nav a:hover {{ text-decoration:underline; }}
    .log {{ background:#1e1e1e; color:#d4d4d4; padding:16px; border-radius:6px; font-family:monospace; font-size:12px;
            max-height:320px; overflow-y:auto; white-space:pre-wrap; }}
  </style>
</head>
<body>
  <div class="nav">
    <a href="/">🏠 Home</a>
    <a href="/gallery">🖼 Gallery</a>
  </div>
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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    return _base_html(_upload_form())


@app.post("/run", response_class=HTMLResponse)
async def run_analysis(
    request: Request,
    incident_file: Optional[UploadFile] = File(None),
    metric_file:   Optional[UploadFile] = File(None),
    problem_file:  Optional[UploadFile] = File(None),
    incident_path: Optional[str] = Form(None),
    metric_path:   Optional[str] = Form(None),
    problem_path:  Optional[str] = Form(None),
):
    logs: str = ""
    tmp_dir = Path(tempfile.mkdtemp())

    try:
        # ---- resolve incident.csv ----
        if incident_file and incident_file.filename:
            inc_path = tmp_dir / "incident.csv"
            inc_path.write_bytes(await incident_file.read())
        elif incident_path and incident_path.strip():
            inc_path = Path(incident_path.strip())
        else:
            inc_path = Path.home() / "Downloads" / "incident.csv"

        if not inc_path.exists():
            return _base_html(
                f'<div class="card"><div class="msg error">❌ incident.csv not found at: <code>{inc_path}</code></div>'
                + _upload_form() + "</div>"
            )

        # ---- resolve metric_instance.csv ----
        if metric_file and metric_file.filename:
            met_path = tmp_dir / "metric_instance.csv"
            met_path.write_bytes(await metric_file.read())
        elif metric_path and metric_path.strip():
            met_path = Path(metric_path.strip())
        else:
            met_path = Path.home() / "Downloads" / "metric_instance.csv"

        if not met_path.exists():
            return _base_html(
                f'<div class="card"><div class="msg error">❌ metric_instance.csv not found at: <code>{met_path}</code></div>'
                + _upload_form() + "</div>"
            )

        # ---- resolve problem.csv (optional) ----
        prob_path: Optional[Path] = None
        if problem_file and problem_file.filename:
            prob_path = tmp_dir / "problem.csv"
            prob_path.write_bytes(await problem_file.read())
        elif problem_path and problem_path.strip():
            prob_path = Path(problem_path.strip())
            if not prob_path.exists():
                prob_path = None
        else:
            candidate = Path.home() / "Downloads" / "problem.csv"
            if candidate.exists():
                prob_path = candidate

        # ---- run analysis ----
        import sys, contextlib, io as _io

        captured = _io.StringIO()
        with contextlib.redirect_stdout(captured):
            incidents = load_incidents(inc_path)
            metrics   = load_metrics(met_path)
            problems  = load_problems(prob_path) if prob_path else None

            matched, summary, trends, top_apps, prob_tickets, issue_trends, top_issues = analyze_data(
                incidents, metrics
            )
            analyze_uncategorized_issues(matched)
            create_visualizations(OUTPUT_DIR, matched, issue_trends)

        logs = captured.getvalue()

        # ---- build gallery of generated PNGs ----
        images = sorted(OUTPUT_DIR.glob("*.png"))
        if not images:
            img_html = "<p>No images were generated.</p>"
        else:
            img_html = '<div class="img-grid">'
            for img in images:
                img_html += f"""
                <div class="img-card">
                  <a href="/output/{img.name}" target="_blank">
                    <img src="/output/{img.name}" alt="{img.stem}"/>
                  </a>
                  <a href="/output/{img.name}" download>⬇ Download {img.name}</a>
                </div>"""
            img_html += "</div>"

        body = f"""
        <div class="card">
          <h1>✅ Analysis Complete</h1>
          <div class="msg success">Charts saved to <code>{OUTPUT_DIR}</code></div>
          <h2>Output Charts</h2>
          {img_html}
          <h2>Console Log</h2>
          <div class="log">{logs}</div>
        </div>"""
        return _base_html(body, title="Analysis Results")

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc()
        body = f"""
        <div class="card">
          <div class="msg error">❌ Analysis failed: {exc}</div>
          <div class="log">{tb}</div>
        </div>""" + _upload_form()
        return _base_html(body, title="Error")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.get("/gallery", response_class=HTMLResponse)
async def gallery():
    """Show all previously generated output images."""
    images = sorted(OUTPUT_DIR.glob("*.png"))
    if not images:
        body = '<div class="card"><h1>🖼 Gallery</h1><p>No images yet. Run an analysis first.</p></div>'
    else:
        img_html = '<div class="img-grid">'
        for img in images:
            img_html += f"""
            <div class="img-card">
              <a href="/output/{img.name}" target="_blank">
                <img src="/output/{img.name}" alt="{img.stem}"/>
              </a>
              <a href="/output/{img.name}" download>⬇ Download {img.name}</a>
            </div>"""
        img_html += "</div>"
        body = f'<div class="card"><h1>🖼 Gallery ({len(images)} charts)</h1>{img_html}</div>'

    return _base_html(body, title="Gallery")


@app.get("/images", response_class=JSONResponse)
async def list_images():
    """JSON endpoint listing available output images."""
    images = sorted(OUTPUT_DIR.glob("*.png"))
    return {"images": [f"/output/{img.name}" for img in images]}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=True)

