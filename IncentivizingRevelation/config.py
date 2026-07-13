"""
Experiment configuration.

Single source of truth for all parameters. Override via CLI (see run.py)
or by constructing a Config object directly in notebooks/scripts.
"""

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class Config:
    # ── Dataset ──────────────────────────────────────────────────────────
    data_path: str = "data/scenarios.json"
    scenario_ids: Optional[list[str]] = None  # None = run all

    # ── LLM backend ─────────────────────────────────────────────────────
    model: str = "gpt-4o-mini"
    api_key_env: str = "OPENAI_API_KEY"
    base_url: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 512

    # ── Deliberation ────────────────────────────────────────────────────
    num_rounds: int = 3
    num_agents: Optional[int] = None
    shuffle_agent_order: bool = True   # randomize speaking order per scenario/run

    # ── Incentive mechanism ─────────────────────────────────────────────
    incentive: Literal[
        "uniform",
        "uniform_no_cost",             # uniform reward, no disclosure costs (2×2 ablation)
        "contribution",                # proportional to moderator-rated contribution (actual mechanism)
        "contribution_no_cost",        # contribution reward, no disclosure costs (2×2 ablation)
        "contribution_oracle",         # proportional to posthoc decisive-feature credit (oracle upper bound)
        "counterfactual_contribution", # leave-one-out moderator confidence shift (principled CMC)
        "hybrid",                      # alpha*uniform + (1-alpha)*contribution
        "stake",
        "bid_to_speak",        # per-turn confidence bidding from a speaking budget
        "free_debate",
        "forced_sharing",              # all agents disclose all features (perfect-info upper bound)
        "no_comm",
    ] = "uniform"
    contribution_reward_pool: float = 100.0
    hybrid_alpha: float = 0.5          # blend weight: alpha=uniform share, (1-alpha)=contribution share
    stake_budget: float = 20.0
    stake_multiplier: float = 3.0
    counterfactual_contribution: bool = False  # enable CMC scoring (adds N*R extra LLM calls)

    # ── Token-level costs ───────────────────────────────────────────────
    token_cost: float = 0.0

    # ── Prompt ablations ────────────────────────────────────────────────
    ablate_decision_rules: bool = False  # strip DECISION RULES from agent prompt
    neutral_agent_wording: bool = False  # group-benefit framing instead of self-interested (ablation)
    extract_free_debate_features: bool = True  # LLM-based extraction (adds cost)

    # ── Execution ───────────────────────────────────────────────────────
    max_concurrent: int = 4   # parallel scenario threads (1 = sequential)
    resume: bool = True       # skip completed scenario/run pairs on restart

    # ── Logging ─────────────────────────────────────────────────────────
    output_dir: str = "results"
    run_id: Optional[str] = None
    verbose: bool = True

    # ── Reproducibility ─────────────────────────────────────────────────
    seed: int = 42
    num_runs: int = 3

    # ── Cost tracking (approx $/M-token) ────────────────────────────────
    cost_per_1m_input: float = 0.15
    cost_per_1m_output: float = 0.60


PRESETS: dict[str, dict] = {
    "quick_test": dict(
        num_rounds=2, num_runs=1, max_concurrent=1,
        scenario_ids=["S01_diabetes_escalate", "S02_loan_standard_terms"],
    ),
    "openai_mini": dict(
        model="gpt-4o-mini", api_key_env="OPENAI_API_KEY",
        cost_per_1m_input=0.15, cost_per_1m_output=0.60,
    ),
    "llama_together": dict(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        api_key_env="TOGETHER_API_KEY",
        base_url="https://api.together.xyz/v1",
        cost_per_1m_input=0.88, cost_per_1m_output=0.88,
    ),
    "qwen_together": dict(
        model="Qwen/Qwen2.5-72B-Instruct-Turbo",
        api_key_env="TOGETHER_API_KEY",
        base_url="https://api.together.xyz/v1",
        cost_per_1m_input=0.60, cost_per_1m_output=0.60,
    ),
    "local_ollama": dict(
        model="llama3.3:70b", api_key_env="",
        base_url="http://localhost:11434/v1",
        cost_per_1m_input=0.0, cost_per_1m_output=0.0,
    ),
    "ablate_no_rules": dict(ablate_decision_rules=True),
    "neutral_wording": dict(neutral_agent_wording=True),
    "full_merged": dict(data_path="data/scenarios_merged.json"),
    # 2×2 ablation models
    "gpt4o_mini": dict(
        model="gpt-4o-mini", api_key_env="OPENAI_API_KEY",
        cost_per_1m_input=0.15, cost_per_1m_output=0.60,
    )
}
