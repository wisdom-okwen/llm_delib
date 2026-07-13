#!/usr/bin/env python3
"""
Main experiment runner.

Usage:
    # Quick test (2 scenarios, 1 run)
    python run.py --preset quick_test --incentive uniform

    # Full sweep (parallel, with resume on crash)
    python run.py --incentive uniform contribution stake --num-runs 3

    # Ablation: no decision rules
    python run.py --preset ablate_no_rules --incentive uniform contribution

    # Use Llama via Together
    python run.py --preset llama_together --incentive contribution
"""

import argparse
import json
import logging
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np

from config import Config, PRESETS
from llm import LLM
from data import load_scenarios
from engine import run_deliberation
from metrics import (
    compute_metrics, disclosure_calibration,
    format_comparison_table,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def build_config(args) -> Config:
    kwargs = {}

    if args.preset and args.preset in PRESETS:
        kwargs.update(PRESETS[args.preset])
        log.info(f"Applied preset: {args.preset}")

    if args.model:
        kwargs["model"] = args.model
    if args.base_url:
        kwargs["base_url"] = args.base_url
    if args.api_key_env:
        kwargs["api_key_env"] = args.api_key_env
    if args.data_path:
        kwargs["data_path"] = args.data_path
    if args.scenarios:
        kwargs["scenario_ids"] = args.scenarios
    if args.num_rounds:
        kwargs["num_rounds"] = args.num_rounds
    if args.num_agents:
        kwargs["num_agents"] = args.num_agents
    if args.num_runs:
        kwargs["num_runs"] = args.num_runs
    if args.token_cost is not None:
        kwargs["token_cost"] = args.token_cost
    if args.output_dir:
        kwargs["output_dir"] = args.output_dir
    if args.seed is not None:
        kwargs["seed"] = args.seed
    if args.max_concurrent:
        kwargs["max_concurrent"] = args.max_concurrent
    if args.no_resume:
        kwargs["resume"] = False
    if args.ablate_no_rules:
        kwargs["ablate_decision_rules"] = True
    if args.no_shuffle:
        kwargs["shuffle_agent_order"] = False
    if args.hybrid_alpha is not None:
        kwargs["hybrid_alpha"] = args.hybrid_alpha
    if args.enable_cmc:
        kwargs["counterfactual_contribution"] = True
    if args.neutral_wording:
        kwargs["neutral_agent_wording"] = True

    kwargs["verbose"] = not args.quiet
    return Config(**kwargs)


# ── Incremental save/resume ─────────────────────────────────────────────

def _result_key(scenario_id: str, run_idx: int) -> str:
    return f"{scenario_id}__run{run_idx}"


def load_completed(output_dir: Path, incentive: str) -> dict[str, dict]:
    """Load already-completed results for resume."""
    fpath = output_dir / f"results_{incentive}.jsonl"
    completed = {}
    if fpath.exists():
        with open(fpath) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    key = _result_key(r["scenario_id"], r.get("run_idx", 0))
                    completed[key] = r
                except json.JSONDecodeError:
                    continue
    return completed


def append_result(output_dir: Path, incentive: str, result_dict: dict):
    """Append a single result to the JSONL file (crash-safe)."""
    fpath = output_dir / f"results_{incentive}.jsonl"
    with open(fpath, "a") as f:
        f.write(json.dumps(result_dict, default=str) + "\n")


def finalize_results(output_dir: Path, incentive: str) -> list[dict]:
    """Read JSONL → write final JSON → return list."""
    fpath_jsonl = output_dir / f"results_{incentive}.jsonl"
    fpath_json = output_dir / f"results_{incentive}.json"
    results = []
    if fpath_jsonl.exists():
        with open(fpath_jsonl) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    with open(fpath_json, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return results


# ── Parallel execution ──────────────────────────────────────────────────

def _run_single(
    scenario, cfg_cond: Config, run_idx: int,
) -> dict:
    """Run a single scenario/run pair. Thread-safe (each gets own LLM)."""
    llm = LLM(cfg_cond)
    result = run_deliberation(scenario, llm, cfg_cond, run_idx=run_idx)
    result_dict = result.to_dict()
    result_dict["run_idx"] = run_idx
    result_dict["api_usage"] = llm.usage.summary()
    return result_dict


def run_condition(
    incentive: str,
    scenarios,
    cfg: Config,
    output_dir: Path,
) -> list[dict]:
    """Run all scenarios under one incentive condition, with parallelism and resume."""
    cfg_cond = Config(**{**cfg.__dict__, "incentive": incentive})

    # Save condition-specific config
    condition_config_path = output_dir / f"config_{incentive}.json"
    with open(condition_config_path, "w") as f:
        json.dump(cfg_cond.__dict__, f, indent=2, default=str)

    # Clear stale JSONL when not resuming (prevents duplicate rows on rerun)
    fpath_jsonl = output_dir / f"results_{incentive}.jsonl"
    if not cfg.resume and fpath_jsonl.exists():
        fpath_jsonl.unlink()
        log.info(f"[{incentive}] --no-resume: cleared existing JSONL")

    # Load completed results for resume
    completed = load_completed(output_dir, incentive) if cfg.resume else {}
    if completed:
        log.info(f"[{incentive}] Resuming: {len(completed)} already done")

    # Build work items
    work = []
    for run_idx in range(cfg.num_runs):
        for scenario in scenarios:
            key = _result_key(scenario.id, run_idx)
            if key not in completed:
                work.append((scenario, run_idx))

    if not work:
        log.info(f"[{incentive}] All {len(completed)} results already complete")
        return list(completed.values())

    log.info(f"[{incentive}] {len(work)} tasks to run ({len(completed)} cached)")

    errors = 0
    n_workers = min(cfg.max_concurrent, len(work))

    if n_workers <= 1:
        # Sequential
        for scenario, run_idx in work:
            try:
                result_dict = _run_single(scenario, cfg_cond, run_idx)
                key = _result_key(scenario.id, run_idx)
                completed[key] = result_dict
                append_result(output_dir, incentive, result_dict)
            except Exception as e:
                errors += 1
                log.error(f"FAILED {scenario.id} run={run_idx}: {e}", exc_info=True)
    else:
        # Parallel
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            futures = {}
            for scenario, run_idx in work:
                fut = pool.submit(_run_single, scenario, cfg_cond, run_idx)
                futures[fut] = (scenario.id, run_idx)

            for fut in as_completed(futures):
                sid, ridx = futures[fut]
                try:
                    result_dict = fut.result()
                    key = _result_key(sid, ridx)
                    completed[key] = result_dict
                    append_result(output_dir, incentive, result_dict)
                    log.info(
                        f"[{incentive}] Completed {sid} run={ridx} "
                        f"(correct={result_dict['is_correct']})"
                    )
                except Exception as e:
                    errors += 1
                    log.error(f"FAILED {sid} run={ridx}: {e}", exc_info=True)

    if errors:
        log.warning(f"[{incentive}] {errors} failures out of {len(work)} tasks")
    if errors == len(work):
        log.error(f"[{incentive}] ALL tasks failed — check API key / connectivity")

    # Finalize: write combined JSON
    all_results = finalize_results(output_dir, incentive)

    # Aggregate cost
    total_cost = sum(
        r.get("api_usage", {}).get("estimated_cost_usd", 0)
        for r in all_results
    )
    log.info(f"[{incentive}] Done: {len(all_results)} results, ~${total_cost:.4f}")

    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Run multi-agent deliberation experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--preset", choices=list(PRESETS.keys()))
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-env")
    parser.add_argument("--data-path")
    parser.add_argument("--scenarios", nargs="*")
    parser.add_argument(
        "--incentive", nargs="+", default=["uniform"],
        choices=[
            "uniform", "uniform_no_cost",
            "contribution", "contribution_no_cost", "contribution_oracle",
            "counterfactual_contribution", "hybrid",
            "stake", "bid_to_speak", "free_debate", "forced_sharing", "no_comm",
        ],
    )
    parser.add_argument("--num-rounds", type=int)
    parser.add_argument("--num-agents", type=int)
    parser.add_argument("--num-runs", type=int)
    parser.add_argument("--token-cost", type=float)
    parser.add_argument("--hybrid-alpha", type=float, help="Blend weight for hybrid mechanism (default 0.5)")
    parser.add_argument("--enable-cmc", action="store_true",
                        help="Enable counterfactual marginal contribution scoring (adds N×R LLM calls)")
    parser.add_argument("--max-concurrent", type=int)
    parser.add_argument("--output-dir", default="results")
    parser.add_argument(
        "--run-dir",
        help="Use this existing directory directly instead of creating a new timestamped one. "
             "Enables crash-resume: point to a previous run's directory and re-run the same command.",
    )
    parser.add_argument("--seed", type=int)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--no-resume", action="store_true", help="Don't skip completed runs")
    parser.add_argument("--ablate-no-rules", action="store_true", help="Strip DECISION RULES from prompts")
    parser.add_argument("--neutral-wording", action="store_true",
                        help="Use group-benefit prompt framing instead of self-interested (ablation)")
    parser.add_argument("--no-shuffle", action="store_true", help="Don't shuffle agent speaking order")

    args = parser.parse_args()
    cfg = build_config(args)

    random.seed(cfg.seed)
    np.random.seed(cfg.seed)

    # Load data
    scenarios = load_scenarios(cfg.data_path, cfg.scenario_ids)
    if not scenarios:
        log.error("No scenarios loaded.")
        sys.exit(1)
    yes_count = sum(1 for s in scenarios if s.label.upper() == "YES")
    no_count  = len(scenarios) - yes_count
    no_decisive = [s.id for s in scenarios if not s.decisive_features]
    log.info(f"Loaded {len(scenarios)} scenarios — YES={yes_count}, NO={no_count} "
             f"({yes_count/len(scenarios):.0%} YES)")
    if no_decisive:
        log.warning(f"Scenarios with NO decisive features (will score 0 DSR): {no_decisive}")
    log.info(f"Config: model={cfg.model}, rounds={cfg.num_rounds}, "
             f"shuffle={cfg.shuffle_agent_order}, ablate_rules={cfg.ablate_decision_rules}, "
             f"concurrent={cfg.max_concurrent}")

    # Output directory
    if args.run_dir:
        output_dir = Path(args.run_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"Using existing run directory: {output_dir}")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(cfg.output_dir) / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "config.json", "w") as f:
        json.dump(cfg.__dict__, f, indent=2, default=str)

    # Run conditions
    all_results_by_condition = {}
    for incentive in args.incentive:
        log.info(f"\n{'='*60}")
        log.info(f"CONDITION: {incentive}")
        log.info(f"{'='*60}")
        all_results_by_condition[incentive] = run_condition(
            incentive, scenarios, cfg, output_dir,
        )

    # Compute metrics
    from engine import DeliberationResult
    condition_metrics = []

    for incentive, results_dicts in all_results_by_condition.items():
        result_objs = []
        for rd in results_dicts:
            try:
                obj = DeliberationResult(**{
                    k: rd[k] for k in DeliberationResult.__dataclass_fields__ if k in rd
                })
                result_objs.append(obj)
            except Exception as e:
                log.debug(f"Could not reconstruct result: {e}")
                continue

        if result_objs:
            cm = compute_metrics(result_objs, scenarios)
            condition_metrics.append(cm)
            calib = disclosure_calibration(result_objs, scenarios)
            log.info(f"[{incentive}] Calibration: {json.dumps(calib, indent=2)}")

    if condition_metrics:
        print("\n" + format_comparison_table(condition_metrics) + "\n")

        metrics_out = {}
        for cm in condition_metrics:
            metrics_out[cm.condition] = {
                "accuracy": cm.accuracy,
                "std_accuracy": cm.std_accuracy,
                "accuracy_ci": cm.accuracy_ci,
                "decisive_surfacing_rate": cm.decisive_surfacing_rate,
                "std_decisive_surfacing_rate": cm.std_decisive_surfacing_rate,
                "selective_disclosure_index": cm.selective_disclosure_index,
                "free_riding_rate": cm.free_riding_rate,
                "round_free_riding_rate": cm.round_free_riding_rate,
                "decisive_holder_disclosure_rate": cm.decisive_holder_disclosure_rate,
                "non_holder_disclosure_rate": cm.non_holder_disclosure_rate,
                "mean_communication_tokens": cm.mean_communication_tokens,
                "mean_disclosure_cost": cm.mean_disclosure_cost,
                "misleading_before_wrong_rate": cm.misleading_before_wrong_rate,
                "misleading_preceded_decisive_rate": cm.misleading_preceded_decisive_rate,
                "time_to_decisive_surfacing": cm.time_to_decisive_surfacing,
                "novelty_rate": cm.novelty_rate,
                "judge_oracle_correlation": cm.judge_oracle_correlation,
                "surfacing_by_cost": cm.surfacing_by_cost,
                "per_domain": cm.per_domain,
            }
        with open(output_dir / "metrics.json", "w") as f:
            json.dump(metrics_out, f, indent=2)

    # ── Parse failure report ────────────────────────────────────────────────
    parse_failure_totals: dict[str, dict[str, int]] = {}
    for incentive_name, results_dicts in all_results_by_condition.items():
        totals: dict[str, int] = {}
        for rd in results_dicts:
            for k, v in rd.get("parse_failures", {}).items():
                if isinstance(v, int):
                    totals[k] = totals.get(k, 0) + v
        if any(v > 0 for v in totals.values()):
            parse_failure_totals[incentive_name] = totals
    if parse_failure_totals:
        log.warning("=== PARSE FAILURE SUMMARY ===")
        for incentive_name, totals in parse_failure_totals.items():
            parts = ", ".join(f"{k}={v}" for k, v in sorted(totals.items()) if v > 0)
            log.warning(f"  [{incentive_name}] {parts}")
        log.warning("=============================")

    # Aggregate cost
    total_usd = 0
    for results in all_results_by_condition.values():
        total_usd += sum(r.get("api_usage", {}).get("estimated_cost_usd", 0) for r in results)
    log.info(f"\nTotal estimated cost: ${total_usd:.4f}")
    log.info(f"Results saved to: {output_dir}/")


if __name__ == "__main__":
    main()
