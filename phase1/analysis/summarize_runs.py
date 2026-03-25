from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from analysis.metrics import compute_run_metrics, summarize_metrics
from simulation.utils import load_json, save_json


def summarize_run_directory(run_dir: str, output_path: str) -> Dict[str, Any]:
    run_path = Path(run_dir)
    json_files = sorted(run_path.glob("*/*.json"))
    if not json_files:
        json_files = sorted(run_path.glob("*.json"))

    runs: List[Dict[str, Any]] = [load_json(str(path)) for path in json_files]
    run_metrics = [compute_run_metrics(run) for run in runs]
    summary = summarize_metrics(run_metrics)

    payload = {
        "run_metrics": run_metrics,
        "summary": summary,
    }

    save_json(payload, output_path)
    return payload