import json
from pathlib import Path
from typing import Any, Dict, List


def log_run_conversation(run_data: Dict[str, Any], output_file: str) -> None:
    """Create a readable conversation log for a single run."""
    with open(output_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write(f"Scenario: {run_data.get('scenario_id', 'Unknown')}\n")
        f.write(f"Question: {run_data.get('question', 'Unknown')}\n")
        f.write(f"Correct Answer (Label): {run_data.get('label', 'Unknown')}\n")
        f.write(f"Group Answer: {run_data.get('group_answer', 'UNKNOWN')}\n")
        f.write(f"Result: {'✓ CORRECT' if run_data.get('correct') else '✗ INCORRECT'}\n")
        f.write("=" * 80 + "\n\n")

        # Deliberation trajectory
        trajectory = run_data.get("trajectory", [])
        if trajectory:
            f.write("DELIBERATION TRAJECTORY\n")
            f.write("-" * 80 + "\n\n")
            
            for turn in trajectory:
                f.write(f"Round {turn.get('round', '?')} | Agent {turn.get('agent_id', '?')}\n")
                f.write(f"  Message: {turn.get('message', '(no message)')}\n")
                
                revealed = turn.get("revealed_features", [])
                if revealed:
                    f.write(f"  Revealed: {', '.join(revealed)}\n")
                
                cost = turn.get("total_disclosure_cost", 0)
                if cost > 0:
                    f.write(f"  Cost Incurred: {cost}\n")
                
                f.write(f"  Contributed: {'Yes' if turn.get('contributed') else 'No'}\n")
                f.write("\n")

        # Final votes
        final_votes = run_data.get("final_votes", [])
        if final_votes:
            f.write("\nFINAL VOTES\n")
            f.write("-" * 80 + "\n")
            for vote in final_votes:
                f.write(f"{vote.get('agent_id', '?')}: {vote.get('answer', 'UNKNOWN')}\n")

        # Summary stats
        f.write("\n\nSUMMARY STATISTICS\n")
        f.write("-" * 80 + "\n")
        contributions = run_data.get("agent_contribution_counts", {})
        total_contrib = sum(contributions.values())
        f.write(f"Total Agent Contributions: {total_contrib}\n")
        f.write(f"Contributions by Agent: {json.dumps(contributions, indent=2)}\n")

        decisive = run_data.get("decisive_features", [])
        f.write(f"Decisive Features (ground truth): {', '.join(decisive) if decisive else 'None'}\n")

        misleading = run_data.get("misleading_features", [])
        f.write(f"Misleading Features (ground truth): {', '.join(misleading) if misleading else 'None'}\n")


def log_all_conversations(runs_dir: str, output_dir: str) -> None:
    """Generate logs for all runs in a directory."""
    runs_path = Path(runs_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    run_files = sorted(runs_path.glob("*.json"))
    
    print(f"Generating conversation logs for {len(run_files)} runs...")
    
    for run_file in run_files:
        with open(run_file) as f:
            run_data = json.load(f)
        
        log_name = run_file.stem + ".txt"
        log_path = output_path / log_name
        log_run_conversation(run_data, str(log_path))
        print(f"  ✓ {log_name}")
    
    print(f"\n✓ All conversation logs saved to: {output_dir}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 log_conversations.py <runs_dir> [output_dir]")
        sys.exit(1)
    
    runs_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else runs_dir + "_logs"
    log_all_conversations(runs_dir, output_dir)
