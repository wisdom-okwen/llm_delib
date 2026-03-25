from __future__ import annotations

import random
from collections import Counter
from typing import Any, Dict, List

from simulation.agent import Agent


def run_deliberation(
    agents: List[Agent],
    question: str,
    label: str,
    config: Dict[str, Any],
    scenario_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    deliberation_cfg = config["deliberation"]
    incentive_cfg = config["incentives"]
    prompt_cfg = config["prompts"]
    agent_cfg = config["agents"]

    num_rounds = deliberation_cfg["num_rounds"]
    speaking_order = deliberation_cfg.get("speaking_order", "random")  # Default to random for voluntary contribution

    conversation_history: List[Dict[str, Any]] = []
    agent_contribution_tracker = {agent.agent_id: 0 for agent in agents}
    agent_cost_tracker = {agent.agent_id: 0 for agent in agents}

    for round_idx in range(1, num_rounds + 1):
        round_agents = list(agents)
        if speaking_order == "random":
            random.shuffle(round_agents)

        if num_rounds > 1:
            print(f"    Round {round_idx}/{num_rounds}...", flush=True)

        for agent in round_agents:
            action = agent.speak(
                question=question,
                conversation_history=conversation_history if deliberation_cfg.get("include_history_each_round", True) else [],
                round_idx=round_idx,
                include_costs_in_prompt=prompt_cfg.get("include_costs_in_prompt", True),
                include_shared_reward_in_prompt=prompt_cfg.get("include_shared_reward_in_prompt", True),
                shared_reward_if_correct=incentive_cfg.get("shared_reward_if_correct", 1.0),
                allow_empty_message=agent_cfg.get("allow_empty_message", True),
            )

            conversation_history.append(
                {
                    "round": round_idx,
                    "agent_id": action.agent_id,
                    "message": action.message,
                    "revealed_features": action.revealed_features,
                    "reasoning_summary": action.reasoning_summary,
                    "total_disclosure_cost": action.total_disclosure_cost,
                    "contributed": action.contributed,
                }
            )

            if action.contributed:
                agent_contribution_tracker[action.agent_id] += 1
                agent_cost_tracker[action.agent_id] += action.total_disclosure_cost

    final_votes = []
    for agent in agents:
        vote = agent.final_vote(question=question, conversation_history=conversation_history)
        final_votes.append(
            {
                "agent_id": vote.agent_id,
                "answer": vote.answer,
                "confidence": vote.confidence,
                "reasoning_summary": vote.reasoning_summary,
            }
        )

    group_answer = _majority_vote(final_votes)
    correct = str(group_answer).strip().lower() == str(label).strip().lower()

    # Calculate rewards for each agent
    shared_reward = incentive_cfg.get("shared_reward_if_correct", 1.0) if correct else 0.0
    agent_rewards = {}
    agent_net_payoffs = {}
    
    for agent in agents:
        agent_id = agent.agent_id
        total_cost = agent_cost_tracker[agent_id]
        agent_rewards[agent_id] = shared_reward
        agent_net_payoffs[agent_id] = shared_reward - total_cost

    return {
        "scenario_id": scenario_metadata["scenario_id"],
        "question": question,
        "label": label,
        "trajectory": conversation_history,
        "final_votes": final_votes,
        "group_answer": group_answer,
        "correct": correct,
        "agent_contribution_counts": agent_contribution_tracker,
        "agent_cost_tracker": agent_cost_tracker,
        "agent_rewards": agent_rewards,
        "agent_net_payoffs": agent_net_payoffs,
    }


def _majority_vote(final_votes: List[Dict[str, Any]]) -> str:
    answers = [str(v.get("answer", "UNKNOWN")).strip() for v in final_votes]
    if not answers:
        return "UNKNOWN"

    counts = Counter(answers)
    return counts.most_common(1)[0][0]