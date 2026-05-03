"""
SNOW Analysis Tool - Data Analysis Module

Attempt normal package-relative imports; if that fails (direct execution or
odd sys.path) fall back to loading data_analysis.py via importlib.
"""
from pathlib import Path

try:
    # Normal package import (works when imported as a package)
    from .data_analysis import (
        load_incidents,
        load_problems,
        load_metric_instance,
        analyze_data,
        categorize_issue,
        create_visualizations,
        create_problem_table_img,
        main
    )
except Exception:
    # Fallback: load the module by file path (handles running this file directly)
    import importlib.util
    import sys

    module_path = Path(__file__).with_name("data_analysis.py")
    spec = importlib.util.spec_from_file_location("data_analysis_fallback", str(module_path))
    _mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_mod)

    # Re-export expected symbols from the loaded module
    load_incidents = _mod.load_incidents
    load_problems = _mod.load_problems
    load_metric_instance = _mod.load_metric_instance
    analyze_data = _mod.analyze_data
    categorize_issue = _mod.categorize_issue
    create_visualizations = _mod.create_visualizations
    create_problem_table_img = _mod.create_problem_table_img
    main = _mod.main

__all__ = [
    "load_incidents",
    "load_problems",
    "load_metric_instance",
    "analyze_data",
    "categorize_issue",
    "create_visualizations",
    "create_problem_table_img",
    "main"
]
