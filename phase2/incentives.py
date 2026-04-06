"""
Incentive mechanisms.

Computes agent rewards under each scheme after a deliberation completes.
Each function takes the deliberation result and returns per-agent payoffs.
"""

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from data import Scenario


@dataclass
class AgentPayoff:
    """Payoff breakdown for a single agent."""
    agent_id: str
    gross_reward: float        # reward before costs
    disclosure_cost: float     # total feature disclosure cost paid
    token_cost: float          # total token cost paid
    stake_cost: float          # stake invested (stake scheme only)
    net_payoff: float          # final payoff after all costs

    @property
    def total_cost(self) -> float:
        return self.disclosure_cost + self.token_cost + self.stake_cost


def compute_uniform(
    agent_ids: list[str],
    is_correct: bool,
    reward_pool: float,
    disclosure_costs: dict[str, float],
    token_costs: dict[str, float],
) -> dict[str, AgentPayoff]:
    """
    Uniform reward: equal split if correct, zero if wrong.

    Everyone gets reward_pool / N if the group is correct.
    Disclosure and token costs are always deducted.
    """
    n = len(agent_ids)
    share = (reward_pool / n) if is_correct else 0.0

    payoffs = {}
    for aid in agent_ids:
        dc = disclosure_costs.get(aid, 0.0)
        tc = token_costs.get(aid, 0.0)
        payoffs[aid] = AgentPayoff(
            agent_id=aid,
            gross_reward=share,
            disclosure_cost=dc,
            token_cost=tc,
            stake_cost=0.0,
            net_payoff=share - dc - tc,
        )
    return payoffs


def compute_contribution(
    agent_ids: list[str],
    is_correct: bool,
    reward_pool: float,
    contribution_scores: dict[str, float],
    disclosure_costs: dict[str, float],
    token_costs: dict[str, float],
) -> dict[str, AgentPayoff]:
    """
    Contribution-based reward: split proportional to contribution scores.

    Scores come from the moderator's per-round ratings, aggregated.
    If total contribution is 0, falls back to uniform split.
    """
    total_score = sum(contribution_scores.get(aid, 0.0) for aid in agent_ids)

    payoffs = {}
    for aid in agent_ids:
        score = contribution_scores.get(aid, 0.0)
        if total_score > 0:
            share_frac = score / total_score
        else:
            share_frac = 1.0 / len(agent_ids)

        gross = (reward_pool * share_frac) if is_correct else 0.0
        dc = disclosure_costs.get(aid, 0.0)
        tc = token_costs.get(aid, 0.0)

        payoffs[aid] = AgentPayoff(
            agent_id=aid,
            gross_reward=gross,
            disclosure_cost=dc,
            token_cost=tc,
            stake_cost=0.0,
            net_payoff=gross - dc - tc,
        )
    return payoffs


def compute_stake(
    agent_ids: list[str],
    is_correct: bool,
    bids: dict[str, float],
    bid_multiplier: float,
    disclosure_costs: dict[str, float],
    token_costs: dict[str, float],
) -> dict[str, AgentPayoff]:
    """
    Stake-based reward: agents invest a confidence stake, get multiplier back if correct.

    If correct: net from stake = stake * (multiplier - 1)
    If wrong:   net from stake = -stake
    Disclosure and token costs are always deducted additionally.
    """
    payoffs = {}
    for aid in agent_ids:
        stake = bids.get(aid, 0.0)
        dc = disclosure_costs.get(aid, 0.0)
        tc = token_costs.get(aid, 0.0)

        if is_correct:
            gross = stake * bid_multiplier
            stake_net = gross - stake
        else:
            gross = 0.0
            stake_net = -stake

        payoffs[aid] = AgentPayoff(
            agent_id=aid,
            gross_reward=gross,
            disclosure_cost=dc,
            token_cost=tc,
            stake_cost=stake,
            net_payoff=stake_net - dc - tc,
        )
    return payoffs


def compute_hybrid(
    agent_ids: list[str],
    is_correct: bool,
    reward_pool: float,
    contribution_scores: dict[str, float],
    disclosure_costs: dict[str, float],
    token_costs: dict[str, float],
    alpha: float = 0.5,
) -> dict[str, AgentPayoff]:
    """
    Hybrid reward: alpha * uniform + (1-alpha) * contribution.

    Provides a participation floor (uniform base) while still rewarding
    decisive revelation (contribution bonus). Costs deducted once from
    the combined gross reward.
    """
    n = len(agent_ids)
    total_score = sum(contribution_scores.get(aid, 0.0) for aid in agent_ids)
    uniform_pool = reward_pool * alpha if is_correct else 0.0
    contrib_pool = reward_pool * (1.0 - alpha) if is_correct else 0.0

    payoffs = {}
    for aid in agent_ids:
        score = contribution_scores.get(aid, 0.0)
        contrib_frac = (score / total_score) if total_score > 0 else (1.0 / n)
        gross = (uniform_pool / n) + contrib_pool * contrib_frac
        dc = disclosure_costs.get(aid, 0.0)
        tc = token_costs.get(aid, 0.0)
        payoffs[aid] = AgentPayoff(
            agent_id=aid,
            gross_reward=gross,
            disclosure_cost=dc,
            token_cost=tc,
            stake_cost=0.0,
            net_payoff=gross - dc - tc,
        )
    return payoffs


def compute_bid_to_speak(
    agent_ids: list[str],
    is_correct: bool,
    turn_bids: dict[str, float],
    bid_multiplier: float,
    disclosure_costs: dict[str, float],
    token_costs: dict[str, float],
) -> dict[str, AgentPayoff]:
    """
    Bid-to-speak reward: agents bid per turn from a budget.

    Unlike stake (a single pre-deliberation wager), bids are placed turn-by-turn.
    All bids are paid regardless of outcome. If correct, the pool of all bids
    across all agents × multiplier is divided equally. This tests whether
    agents self-select their speaking turns based on private informativeness.
    """
    total_bids = sum(turn_bids.get(aid, 0.0) for aid in agent_ids)
    n = len(agent_ids)
    gross_per_agent = (total_bids * bid_multiplier / n) if is_correct else 0.0

    payoffs = {}
    for aid in agent_ids:
        bid = turn_bids.get(aid, 0.0)
        dc = disclosure_costs.get(aid, 0.0)
        tc = token_costs.get(aid, 0.0)
        payoffs[aid] = AgentPayoff(
            agent_id=aid,
            gross_reward=gross_per_agent,
            disclosure_cost=dc,
            token_cost=tc,
            stake_cost=bid,
            net_payoff=gross_per_agent - bid - dc - tc,
        )
    return payoffs


def compute_posthoc_contribution_scores(
    agent_disclosures: dict[str, list[str]],
    scenario: "Scenario",
) -> dict[str, float]:
    """
    Post-hoc contribution scoring grounded in decisive feature surfacing.

    Agents receive credit proportional to the signal strength of decisive
    features they disclosed. This is computed after deliberation with full
    knowledge of which features were decisive (ground-truth-grounded).

    Signal weights: strong=3, medium=2, weak=1, misleading=0 (no credit).
    """
    signal_weight = {"weak": 1.0, "medium": 2.0, "strong": 3.0, "misleading": 0.0}
    decisive_set = set(scenario.decisive_features)

    scores: dict[str, float] = {}
    for aid, feats in agent_disclosures.items():
        score = 0.0
        for fname in feats:
            if fname in decisive_set and fname in scenario.features:
                feat = scenario.features[fname]
                score += signal_weight.get(feat.signal_strength, 1.0)
        scores[aid] = score
    return scores


def compute_payoffs(
    incentive: str,
    agent_ids: list[str],
    is_correct: bool,
    reward_pool: float,
    disclosure_costs: dict[str, float],
    token_costs: dict[str, float],
    contribution_scores: Optional[dict[str, float]] = None,
    bids: Optional[dict[str, float]] = None,
    bid_multiplier: float = 3.0,
    hybrid_alpha: float = 0.5,
    turn_bids: Optional[dict[str, float]] = None,
) -> dict[str, AgentPayoff]:
    """Dispatch to the appropriate incentive computation."""
    if incentive == "uniform":
        return compute_uniform(
            agent_ids, is_correct, reward_pool, disclosure_costs, token_costs,
        )
    elif incentive in ("contribution", "counterfactual_contribution"):
        return compute_contribution(
            agent_ids, is_correct, reward_pool,
            contribution_scores or {}, disclosure_costs, token_costs,
        )
    elif incentive == "hybrid":
        return compute_hybrid(
            agent_ids, is_correct, reward_pool,
            contribution_scores or {}, disclosure_costs, token_costs,
            alpha=hybrid_alpha,
        )
    elif incentive == "stake":
        return compute_stake(
            agent_ids, is_correct, bids or {}, bid_multiplier,
            disclosure_costs, token_costs,
        )
    elif incentive == "bid_to_speak":
        return compute_bid_to_speak(
            agent_ids, is_correct, turn_bids or {}, bid_multiplier,
            disclosure_costs, token_costs,
        )
    else:
        raise ValueError(f"Unknown incentive: {incentive}")
