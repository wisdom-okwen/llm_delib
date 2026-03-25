#!/usr/bin/env python3
"""
Generate CSV conversation logs from run trajectories.
"""
import json
import csv
from pathlib import Path
from typing import Any, Dict


def log_all_conversations_csv(runs_dir: str, output_file: str) -> None:
    """Generate a single CSV with all runs combined."""
    runs_path = Path(runs_dir)
    output_path = Path(output_file).parent
    output_path.mkdir(parents=True, exist_ok=True)

    run_files = sorted(runs_path.glob("*/*.json"))
    if not run_files:
        run_files = sorted(runs_path.glob("*.json"))
    
    print(f"Generating CSV logs for {len(run_files)} runs...")
    
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            "scenario_id", "repeat_idx", "round", "agent_id", "message", 
            "revealed_features", "disclosure_cost", "contributed", 
            "reasoning_summary", "final_answer", "confidence", "correct", "group_answer",
            "total_cost", "shared_reward", "net_payoff"
        ])
        
        for run_file in run_files:
            with open(run_file) as rf:
                run_data = json.load(rf)
            
            # Build final votes map
            final_votes_map = {}
            for vote in run_data.get("final_votes", []):
                final_votes_map[vote.get("agent_id")] = {
                    "answer": vote.get("answer", ""),
                    "confidence": vote.get("confidence", "")
                }
            
            # Get rewards and costs
            agent_costs = run_data.get("agent_cost_tracker", {})
            agent_rewards = run_data.get("agent_rewards", {})
            agent_payoffs = run_data.get("agent_net_payoffs", {})
            
            # Write trajectory rows
            trajectory = run_data.get("trajectory", [])
            for turn in trajectory:
                agent_id = turn.get("agent_id", "")
                final_vote = final_votes_map.get(agent_id, {})
                
                writer.writerow([
                    run_data.get("scenario_id", ""),
                    run_data.get("repeat_idx", ""),
                    turn.get("round", ""),
                    agent_id,
                    turn.get("message", ""),
                    "|".join(turn.get("revealed_features", [])),
                    turn.get("total_disclosure_cost", 0),
                    "Yes" if turn.get("contributed") else "No",
                    turn.get("reasoning_summary", ""),
                    final_vote.get("answer", ""),
                    final_vote.get("confidence", ""),
                    "Yes" if run_data.get("correct") else "No",
                    run_data.get("group_answer", ""),
                    agent_costs.get(agent_id, 0),
                    agent_rewards.get(agent_id, 0),
                    agent_payoffs.get(agent_id, 0)
                ])
    
    print(f"✓ Conversation logs saved to: {output_file}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 log_conversations_csv.py <runs_dir> [output_file]")
        sys.exit(1)
    
    runs_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "conversations.csv"
    log_all_conversations_csv(runs_dir, output_file)
