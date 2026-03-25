from __future__ import annotations

from typing import Any, Dict, List


def compute_run_metrics(run: Dict[str, Any]) -> Dict[str, Any]:
    trajectory = run.get("trajectory", [])
    decisive_features = set(run.get("decisive_features", []))
    misleading_features = set(run.get("misleading_features", []))

    surfaced_features = set()
    total_cost = 0
    total_contributions = 0

    for turn in trajectory:
        revealed = turn.get("revealed_features", []) or []
        surfaced_features.update(revealed)
        total_cost += int(turn.get("total_disclosure_cost", 0))
        if turn.get("contributed", False):
            total_contributions += 1

    decisive_surfaced = len(decisive_features.intersection(surfaced_features)) > 0
    misleading_surfaced = len(misleading_features.intersection(surfaced_features)) > 0

    return {
        "scenario_id": run.get("scenario_id"),
        "repeat_idx": run.get("repeat_idx"),
        "group_answer": run.get("group_answer"),
        "label": run.get("label"),
        "correct": run.get("correct"),
        "total_disclosure_cost": total_cost,
        "total_contributions": total_contributions,
        "decisive_feature_surfaced": decisive_surfaced,
        "misleading_feature_surfaced": misleading_surfaced,
        "agent_contribution_counts": run.get("agent_contribution_counts", {}),
    }


def summarize_metrics(run_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not run_metrics:
        return {}

    n = len(run_metrics)
    accuracy = sum(1 for r in run_metrics if r["correct"]) / n
    decisive_rate = sum(1 for r in run_metrics if r["decisive_feature_surfaced"]) / n
    misleading_rate = sum(1 for r in run_metrics if r["misleading_feature_surfaced"]) / n
    avg_cost = sum(r["total_disclosure_cost"] for r in run_metrics) / n
    avg_contributions = sum(r["total_contributions"] for r in run_metrics) / n

    aggregate_agent_contribs: Dict[str, int] = {}
    for row in run_metrics:
        counts = row.get("agent_contribution_counts", {})
        for agent_id, count in counts.items():
            aggregate_agent_contribs[agent_id] = aggregate_agent_contribs.get(agent_id, 0) + count

    return {
        "num_runs": n,
        "accuracy": accuracy,
        "decisive_feature_surfacing_rate": decisive_rate,
        "misleading_feature_surfacing_rate": misleading_rate,
        "average_total_disclosure_cost": avg_cost,
        "average_total_contributions": avg_contributions,
        "aggregate_agent_contribution_counts": aggregate_agent_contribs,
    }