from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from simulation.deliberation import run_deliberation
from simulation.loader import build_agent_objects_for_scenario, load_scenarios
from simulation.utils import load_yaml, save_json, set_seed


def run_from_config(config_path: str) -> List[Dict[str, Any]]:
    config = load_yaml(config_path)
    set_seed(config["experiment"].get("seed", 42))

    scenarios = load_scenarios(config)
    results: List[Dict[str, Any]] = []

    repeats = config["experiment"].get("num_repeats_per_scenario", 1)
    
    model_name = config["model"].get("model_type", "unknown")
    base_output_dir = Path(config["logging"]["output_dir"])
    output_dir = base_output_dir / model_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Model: {model_name} | Output: {output_dir}", flush=True)

    total_runs = len(scenarios) * repeats
    run_count = 0

    for scenario_idx, scenario in enumerate(scenarios, 1):
        for repeat_idx in range(repeats):
            run_count += 1
            scenario_id = scenario.get("id", f"scenario_{scenario_idx}")
            print(f"\n[{run_count}/{total_runs}] Running {scenario_id} (repeat {repeat_idx + 1}/{repeats})...", flush=True)

            agents, agent_feature_map, metadata = build_agent_objects_for_scenario(
                scenario=scenario,
                config=config,
            )

            result = run_deliberation(
                agents=agents,
                question=metadata["question"],
                label=metadata["label"],
                config=config,
                scenario_metadata=metadata,
            )

            result["repeat_idx"] = repeat_idx
            result["agent_private_features"] = {
                agent_id: [feature.name for feature in features]
                for agent_id, features in agent_feature_map.items()
            }
            result["decisive_features"] = metadata["decisive_features"]
            result["misleading_features"] = metadata["misleading_features"]

            file_name = f"{metadata['scenario_id']}_repeat{repeat_idx}.json"
            file_path = output_dir / file_name
            save_json(result, str(file_path))
            
            # Log completion
            contributions = sum(1 for t in result["trajectory"] if t.get("contributed"))
            correct_str = "✓" if result["correct"] else "✗"
            print(f"  {correct_str} Saved: {file_name} | Contributions: {contributions}", flush=True)
            
            results.append(result)

    print(f"\n✓ All {total_runs} runs completed. Results in: {output_dir}\n", flush=True)
    return results