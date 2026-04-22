"""
Deliberation engine.

Orchestrates a full deliberation: agent/moderator creation, round-robin
communication, feature disclosure tracking, and result recording.
"""

import hashlib
import logging
import random
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    import tiktoken
except ImportError:
    tiktoken = None

from config import Config
from data import Scenario
from llm import LLM
from agents import (
    Agent, Moderator, AgentTurn,
    parse_stance, extract_free_debate_features,
)
from incentives import compute_payoffs, compute_posthoc_contribution_scores, AgentPayoff

_TOKENIZER_CACHE: dict = {}
_TIKTOKEN_AVAILABLE = tiktoken is not None

def _get_tokenizer(model: str):
    global _TIKTOKEN_AVAILABLE
    if not _TIKTOKEN_AVAILABLE:
        return None
    if model not in _TOKENIZER_CACHE:
        try:
            _TOKENIZER_CACHE[model] = tiktoken.encoding_for_model(model)
        except KeyError:
            try:
                log.info(f"No tiktoken encoding for '{model}'; falling back to cl100k_base")
                _TOKENIZER_CACHE[model] = tiktoken.get_encoding("cl100k_base")
            except Exception:
                log.warning("tiktoken unavailable; using word-based token approximation")
                _TIKTOKEN_AVAILABLE = False
                return None
        except Exception:
            log.warning("tiktoken unavailable; using word-based token approximation")
            _TIKTOKEN_AVAILABLE = False
            return None
    return _TOKENIZER_CACHE[model]

def count_tokens(text: str, model: str) -> int:
    enc = _get_tokenizer(model)
    if enc is not None:
        return len(enc.encode(text))
    # Fallback: ~1.3 tokens per word (reasonable approx for English)
    return max(1, int(len(text.split()) * 1.3))

log = logging.getLogger(__name__)


# ── Data structures ─────────────────────────────────────────────────────

@dataclass
class RoundRecord:
    round_num: int
    moderator_open: dict
    agent_turns: list[dict]
    moderator_summary: str
    moderator_stance_after: dict


@dataclass
class DeliberationResult:
    scenario_id: str
    domain: str
    question: str
    ground_truth: str
    incentive: str
    token_cost: float
    num_agents: int
    num_rounds: int
    agent_order: list[str]                    # logged speaking order

    rounds: list[RoundRecord]
    final_decision: dict
    is_correct: bool

    agent_disclosures: dict[str, list[str]]
    agent_disclosure_costs: dict[str, float]
    agent_tokens: dict[str, int]
    agent_communication_tokens: dict[str, int]
    agent_stakes: dict[str, float]
    agent_payoffs: dict[str, dict]

    decisive_features_surfaced: list[str]
    decisive_surfacing_rate: float
    misleading_features_surfaced: list[str]
    total_tokens: int
    total_communication_tokens: int
    total_disclosure_cost: float

    contribution_scores: dict[str, float]
    posthoc_contribution_scores: dict[str, float]

    misleading_before_wrong: bool
    misleading_preceded_decisive: bool

    moderator_trajectory: list[dict]

    # Which agents held decisive features (for agent-level calibration)
    agents_holding_decisive: list[str]

    # Ablation flag
    ablate_decision_rules: bool

    # Parse failure counts (stance fallbacks, bid fallbacks, final decision fallbacks)
    parse_failures: dict = field(default_factory=dict)

    # Tokens consumed by free_debate feature extraction (not part of deliberation comm cost)
    extraction_api_tokens: int = 0

    # Counterfactual marginal contribution scores (leave-one-out moderator confidence shift)
    counterfactual_contribution_scores: dict = field(default_factory=dict)

    # Novelty: per-agent fraction of disclosures that were new (not already publicly known)
    agent_novelty_rates: dict = field(default_factory=dict)

    # First round in which any decisive feature was surfaced (None if never surfaced)
    first_decisive_round: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _empty_payoffs(agent_ids: list[str]) -> dict[str, dict]:
    return {
        aid: asdict(AgentPayoff(
            agent_id=aid, gross_reward=0.0, disclosure_cost=0.0,
            token_cost=0.0, stake_cost=0.0, net_payoff=0.0,
        ))
        for aid in agent_ids
    }


def _scenario_rng(seed: int, scenario_id: str, run_idx: int) -> random.Random:
    """Deterministic per-scenario, per-run RNG, stable across Python versions.

    Uses SHA-256 of the key string rather than Python's str hash (which is
    randomized by default since Python 3.3 and not guaranteed to be stable
    across minor versions).
    """
    raw = f"{seed}:{scenario_id}:{run_idx}".encode()
    int_seed = int(hashlib.sha256(raw).hexdigest(), 16) % (2 ** 32)
    return random.Random(int_seed)


def _compute_misleading_timing(
    rounds: list[RoundRecord],
    misleading_set: set[str],
    decisive_set: set[str],
    is_correct: bool,
    misleading_surfaced: list[str],
) -> tuple[bool, bool]:
    """Compute misleading influence metrics."""
    misleading_before_wrong = bool(misleading_surfaced) and not is_correct

    first_misleading_round: Optional[int] = None
    first_decisive_round: Optional[int] = None
    for rnd in rounds:
        for t in rnd.agent_turns:
            disc = set(t.get("features_disclosed", {}).keys())
            if first_misleading_round is None and disc & misleading_set:
                first_misleading_round = rnd.round_num
            if first_decisive_round is None and disc & decisive_set:
                first_decisive_round = rnd.round_num

    misleading_preceded_decisive = (
        first_misleading_round is not None
        and (first_decisive_round is None or first_misleading_round < first_decisive_round)
    )
    return misleading_before_wrong, misleading_preceded_decisive


def _compute_cmc_scores(
    rounds: list,
    agent_ids: list[str],
    moderator,
    ground_truth: str,
    is_correct: bool,
) -> dict[str, float]:
    """Counterfactual Marginal Contribution (CMC) scoring.

    For each agent, reconstruct the conversation history with that agent's
    messages removed, then ask the moderator for its stance. The CMC score
    is the total signed confidence delta: positive when the agent's presence
    pushed the moderator toward the correct answer.

    This is O(num_agents × num_rounds) extra LLM calls — opt-in via
    cfg.counterfactual_contribution.
    """
    # Build per-agent, per-round contribution deltas
    cmc: dict[str, float] = {aid: 0.0 for aid in agent_ids}

    for rnd in rounds:
        # Real moderator confidence after this round
        real_conf = rnd.moderator_stance_after.get("confidence", 0.5)
        real_decision = rnd.moderator_stance_after.get("decision", "UNKNOWN")

        for aid in agent_ids:
            # Build history up to and including this round, minus agent aid's messages
            history_without = ""
            for past_rnd in rounds:
                history_without += f"\n--- ROUND {past_rnd.round_num} ---\n"
                for t in past_rnd.agent_turns:
                    if t["agent_id"] != aid:
                        history_without += f"[{t['agent_id']}]: {t['message']}\n"
                if past_rnd.round_num == rnd.round_num:
                    break

            conf_without = moderator.eval_stance_fast(history_without)

            # Confidence delta, sign-corrected for whether the real decision was correct
            delta = real_conf - conf_without
            if real_decision.upper() != ground_truth.upper():
                delta = -delta  # agent made moderator more confident in the wrong direction
            cmc[aid] += delta

    # Clip to non-negative (negative contributions count as zero for payoff purposes)
    return {aid: max(0.0, v) for aid, v in cmc.items()}


# ── Forced-sharing baseline ─────────────────────────────────────────────

def _run_forced_sharing(
    scenario: Scenario, agent_ids: list[str], llm: LLM, cfg: Config,
) -> "DeliberationResult":
    """Forced-sharing baseline: all agents disclose all features at no cost.

    This upper-bounds accuracy when information is freely available —
    isolating the effect of the cost barrier from deliberation quality.
    The moderator sees everything and decides.
    """
    from prompts import format_feature_table

    num_agents = len(agent_ids)
    log.info(f"[{scenario.id}] === Forced-sharing baseline ({num_agents} agents) ===")

    # Build a single combined message with all features from all agents
    all_features_text = ""
    all_disclosures: dict[str, list[str]] = {aid: [] for aid in agent_ids}
    for aid in agent_ids:
        features = scenario.get_agent_feature_objects(aid)
        feat_data = {fn: {"value": f.value, "cost": f.cost} for fn, f in features.items()}
        all_features_text += f"\n[{aid}]: discloses all private information:\n"
        all_features_text += format_feature_table(feat_data) + "\n"
        all_disclosures[aid] = list(features.keys())

    moderator = Moderator(scenario=scenario, llm=llm, num_agents=num_agents)
    final = moderator.final_decision(all_features_text)
    is_correct = final["decision"].upper() == scenario.label.upper()

    all_disclosed = set(f for feats in all_disclosures.values() for f in feats)
    decisive_surfaced = [f for f in scenario.decisive_features if f in all_disclosed]
    decisive_rate = (
        len(decisive_surfaced) / len(scenario.decisive_features)
        if scenario.decisive_features else 1.0
    )
    log.info(f"[{scenario.id}] Forced-sharing: {final['decision']} (truth={scenario.label}, correct={is_correct})")

    z = {aid: 0 for aid in agent_ids}
    return DeliberationResult(
        scenario_id=scenario.id, domain=scenario.domain, question=scenario.question,
        ground_truth=scenario.label, incentive=cfg.incentive, token_cost=0.0,
        num_agents=num_agents, num_rounds=1, agent_order=agent_ids,
        rounds=[], final_decision=final, is_correct=is_correct,
        agent_disclosures=all_disclosures,
        agent_disclosure_costs=z,
        agent_tokens=z,
        agent_communication_tokens=z,
        agent_stakes={}, agent_payoffs=_empty_payoffs(agent_ids),
        decisive_features_surfaced=decisive_surfaced,
        decisive_surfacing_rate=decisive_rate,
        misleading_features_surfaced=[f for f in scenario.misleading_features if f in all_disclosed],
        total_tokens=0, total_communication_tokens=0, total_disclosure_cost=0.0,
        contribution_scores={}, posthoc_contribution_scores={},
        misleading_before_wrong=False, misleading_preceded_decisive=False,
        moderator_trajectory=moderator.state.history,
        agents_holding_decisive=[a for a in agent_ids if scenario.agent_holds_decisive(a)],
        ablate_decision_rules=False,
        first_decisive_round=1 if decisive_surfaced else None,
    )


# ── No-communication baseline ──────────────────────────────────────────

def _run_no_comm_vote(
    scenario: Scenario, agent_ids: list[str], llm: LLM, cfg: Config,
) -> DeliberationResult:
    from prompts import NO_COMM_VOTE_SYSTEM, NO_COMM_VOTE_PROMPT, format_feature_table

    num_agents = len(agent_ids)
    log.info(f"[{scenario.id}] === No-comm baseline ({num_agents} agents) ===")

    votes: dict[str, str] = {}
    agent_tokens: dict[str, int] = {}
    for aid in agent_ids:
        features = scenario.get_agent_feature_objects(aid)
        feat_data = {fn: {"value": f.value, "cost": f.cost} for fn, f in features.items()}
        user_prompt = NO_COMM_VOTE_PROMPT.format(
            question=scenario.question, domain=scenario.domain,
            feature_table=format_feature_table(feat_data),
        )
        response, tokens = llm.generate(
            system=NO_COMM_VOTE_SYSTEM, user=user_prompt, max_tokens=200,
        )
        agent_tokens[aid] = tokens
        vote = parse_stance(
            response.replace("<vote>", "<stance>").replace("</vote>", "</stance>")
        )
        votes[aid] = vote["decision"]
        log.info(f"  [{aid}] vote={vote['decision']} conf={vote.get('confidence', 0.5):.2f}")

    counts = Counter(votes.values())
    final_str = counts.most_common(1)[0][0]
    is_correct = final_str.upper() == scenario.label.upper()

    final = {
        "decision": final_str,
        "confidence": max(counts.get("YES", 0), counts.get("NO", 0)) / num_agents,
        "reasoning": f"Majority: {counts.get('YES', 0)} YES, {counts.get('NO', 0)} NO",
    }
    log.info(f"[{scenario.id}] No-comm: {final_str} (truth={scenario.label}, correct={is_correct})")

    z = {aid: 0 for aid in agent_ids}
    return DeliberationResult(
        scenario_id=scenario.id, domain=scenario.domain, question=scenario.question,
        ground_truth=scenario.label, incentive=cfg.incentive, token_cost=0.0,
        num_agents=num_agents, num_rounds=0, agent_order=agent_ids,
        rounds=[], final_decision=final, is_correct=is_correct,
        agent_disclosures={aid: [] for aid in agent_ids},
        agent_disclosure_costs={aid: 0.0 for aid in agent_ids},
        agent_tokens=agent_tokens,
        agent_communication_tokens=z,
        agent_stakes={}, agent_payoffs=_empty_payoffs(agent_ids),
        decisive_features_surfaced=[], decisive_surfacing_rate=0.0,
        misleading_features_surfaced=[],
        total_tokens=sum(agent_tokens.values()), total_communication_tokens=0,
        total_disclosure_cost=0.0,
        contribution_scores={}, posthoc_contribution_scores={},
        misleading_before_wrong=False, misleading_preceded_decisive=False,
        moderator_trajectory=[],
        agents_holding_decisive=[a for a in agent_ids if scenario.agent_holds_decisive(a)],
        ablate_decision_rules=cfg.ablate_decision_rules,
    )


# ── Free-debate baseline ───────────────────────────────────────────────

def _run_free_debate(
    scenario: Scenario, agent_ids: list[str], llm: LLM, cfg: Config,
    rng: random.Random,
) -> DeliberationResult:
    from prompts import FREE_DEBATE_AGENT_SYSTEM, FREE_DEBATE_AGENT_TURN, format_feature_table

    num_agents = len(agent_ids)
    speaking_order = list(agent_ids)
    if cfg.shuffle_agent_order:
        rng.shuffle(speaking_order)

    log.info(
        f"[{scenario.id}] === Free-debate ({num_agents} agents, "
        f"{cfg.num_rounds} rounds, order={speaking_order[:3]}...) ==="
    )

    agent_systems: dict[str, str] = {}
    agent_feat_data: dict[str, dict] = {}
    for aid in agent_ids:
        features = scenario.get_agent_feature_objects(aid)
        feat_data = {fn: {"value": f.value, "cost": f.cost} for fn, f in features.items()}
        agent_feat_data[aid] = feat_data
        agent_systems[aid] = FREE_DEBATE_AGENT_SYSTEM.format(
            agent_id=aid, num_agents=num_agents,
            question=scenario.question, domain=scenario.domain,
            feature_table=format_feature_table(feat_data),
        )

    moderator = Moderator(scenario=scenario, llm=llm, rate_contributions=False, num_agents=num_agents)

    conversation_history = ""
    rounds: list[RoundRecord] = []
    agent_tokens: dict[str, int] = {aid: 0 for aid in agent_ids}
    agent_comm_tokens: dict[str, int] = {aid: 0 for aid in agent_ids}
    extraction_api_tokens: int = 0   # tokens for post-hoc extraction calls (not deliberation cost)
    # Track features extracted from free-form text
    agent_extracted_features: dict[str, set[str]] = {aid: set() for aid in agent_ids}

    for round_num in range(1, cfg.num_rounds + 1):
        mod_open_text, mod_stance = moderator.open_round(
            round_num, cfg.num_rounds, conversation_history,
        )
        stance_str = f"{mod_stance['decision']} (confidence: {mod_stance['confidence']:.2f})"
        conversation_history += f"\n\n--- ROUND {round_num} ---\n[MODERATOR]: {mod_open_text}\n"

        round_turns = []
        round_messages = ""
        position_map = {a: i + 1 for i, a in enumerate(speaking_order)}

        for aid in speaking_order:
            user_prompt = FREE_DEBATE_AGENT_TURN.format(
                round_num=round_num, total_rounds=cfg.num_rounds,
                conversation_history=conversation_history or "(No conversation yet.)",
                moderator_stance=stance_str,
            )
            response, tokens = llm.generate(system=agent_systems[aid], user=user_prompt)
            agent_tokens[aid] += tokens
            comm_tokens = max(1, count_tokens(response, cfg.model))
            agent_comm_tokens[aid] += comm_tokens

            # Extract features mentioned in free-form text (optional, adds LLM cost).
            # Token usage is tracked separately as extraction_api_tokens — it is
            # evaluation overhead, NOT part of the deliberation communication cost.
            extracted = []
            if cfg.extract_free_debate_features:
                tokens_before = llm.usage.completion_tokens
                extracted = extract_free_debate_features(response, agent_feat_data[aid], llm)
                extraction_api_tokens += llm.usage.completion_tokens - tokens_before
            agent_extracted_features[aid].update(extracted)

            entry = f"[{aid}]: {response}"
            conversation_history += f"\n{entry}\n"
            round_messages += f"\n{entry}\n"

            round_turns.append({
                "agent_id": aid, "round_num": round_num,
                "speaking_position": position_map[aid],
                "message": response,
                "features_disclosed": {f: str(agent_feat_data[aid].get(f, {}).get("value", "")) for f in extracted},
                "disclosure_cost": 0.0, "tokens_used": tokens,
                "communication_tokens": comm_tokens,
            })
            log.info(f"  [{aid}] comm={comm_tokens} extracted={extracted or 'none'}")

        mod_summary, mod_stance_after = moderator.close_round(
            round_num, round_messages, conversation_history,
        )
        conversation_history += f"\n[MODERATOR SUMMARY]: {mod_summary}\n"
        rounds.append(RoundRecord(
            round_num=round_num, moderator_open=mod_stance,
            agent_turns=round_turns, moderator_summary=mod_summary,
            moderator_stance_after=mod_stance_after,
        ))

    final = moderator.final_decision(conversation_history)
    is_correct = final["decision"].upper() == scenario.label.upper()
    log.info(f"[{scenario.id}] Free-debate: {final['decision']} (truth={scenario.label}, correct={is_correct})")

    # Compute disclosure metrics from extracted features
    agent_disclosures = {aid: list(feats) for aid, feats in agent_extracted_features.items()}
    all_disclosed = set()
    for feats in agent_disclosures.values():
        all_disclosed.update(feats)

    decisive_surfaced = [f for f in scenario.decisive_features if f in all_disclosed]
    misleading_surfaced = [f for f in scenario.misleading_features if f in all_disclosed]
    decisive_rate = (
        len(decisive_surfaced) / len(scenario.decisive_features)
        if scenario.decisive_features else 1.0
    )

    mbw, mpd = _compute_misleading_timing(
        rounds, set(scenario.misleading_features), set(scenario.decisive_features),
        is_correct, misleading_surfaced,
    )

    return DeliberationResult(
        scenario_id=scenario.id, domain=scenario.domain, question=scenario.question,
        ground_truth=scenario.label, incentive=cfg.incentive, token_cost=0.0,
        num_agents=num_agents, num_rounds=cfg.num_rounds, agent_order=speaking_order,
        rounds=rounds, final_decision=final, is_correct=is_correct,
        agent_disclosures=agent_disclosures,
        agent_disclosure_costs={aid: 0.0 for aid in agent_ids},
        agent_tokens=agent_tokens, agent_communication_tokens=agent_comm_tokens,
        agent_stakes={}, agent_payoffs=_empty_payoffs(agent_ids),
        decisive_features_surfaced=decisive_surfaced,
        decisive_surfacing_rate=decisive_rate,
        misleading_features_surfaced=misleading_surfaced,
        total_tokens=sum(agent_tokens.values()),
        total_communication_tokens=sum(agent_comm_tokens.values()),
        total_disclosure_cost=0.0,
        contribution_scores={}, posthoc_contribution_scores={},
        misleading_before_wrong=mbw, misleading_preceded_decisive=mpd,
        moderator_trajectory=moderator.state.history,
        agents_holding_decisive=[a for a in agent_ids if scenario.agent_holds_decisive(a)],
        ablate_decision_rules=cfg.ablate_decision_rules,
        parse_failures=moderator.parse_failures,
        extraction_api_tokens=extraction_api_tokens,
    )


# ── Structured deliberation (main conditions) ──────────────────────────

def run_deliberation(
    scenario: Scenario, llm: LLM, cfg: Config,
    run_idx: int = 0,
) -> DeliberationResult:
    """
    Run a complete deliberation on one scenario.

    Dispatches to baseline runners for no_comm / free_debate.
    """
    all_agent_ids = scenario.agent_ids
    rng = _scenario_rng(cfg.seed, scenario.id, run_idx)

    if cfg.num_agents and cfg.num_agents < len(all_agent_ids):
        agent_ids = sorted(rng.sample(all_agent_ids, cfg.num_agents))
    else:
        agent_ids = list(all_agent_ids)

    # Dispatch baselines
    if cfg.incentive == "no_comm":
        return _run_no_comm_vote(scenario, agent_ids, llm, cfg)
    if cfg.incentive == "free_debate":
        return _run_free_debate(scenario, agent_ids, llm, cfg, rng)
    if cfg.incentive == "forced_sharing":
        return _run_forced_sharing(scenario, agent_ids, llm, cfg)

    num_agents = len(agent_ids)
    rate_contributions = cfg.incentive in (
        "contribution", "contribution_oracle", "counterfactual_contribution", "hybrid"
    )

    # Shuffle speaking order
    speaking_order = list(agent_ids)
    if cfg.shuffle_agent_order:
        rng.shuffle(speaking_order)

    log.info(
        f"[{scenario.id}] Deliberation: {num_agents} agents, "
        f"{cfg.num_rounds} rounds, incentive={cfg.incentive}, "
        f"order={speaking_order[:3]}..."
    )

    # Create agents
    agents: dict[str, Agent] = {}
    for aid in agent_ids:
        features = scenario.get_agent_feature_objects(aid)
        agents[aid] = Agent(
            agent_id=aid, features=features, scenario=scenario, llm=llm,
            incentive=cfg.incentive, token_cost=cfg.token_cost,
            stake_budget=cfg.stake_budget, stake_multiplier=cfg.stake_multiplier,
            num_agents=num_agents,
            ablate_decision_rules=cfg.ablate_decision_rules,
            neutral_agent_wording=cfg.neutral_agent_wording,
        )

    moderator = Moderator(
        scenario=scenario, llm=llm,
        rate_contributions=rate_contributions, num_agents=num_agents,
    )

    # Elicit stakes
    bids: dict[str, float] = {}
    agent_turn_bids: dict[str, float] = {aid: 0.0 for aid in agent_ids}
    if cfg.incentive == "stake":
        bid_failures = 0
        for aid, agent in agents.items():
            bid, failed = agent.elicit_stake()
            bids[aid] = bid
            if failed:
                bid_failures += 1
        if bid_failures:
            moderator.parse_failures["bid_fallback"] += bid_failures
        log.info(f"[{scenario.id}] Stakes: { {a: f'{b:.1f}' for a, b in bids.items()} }")

    # Run rounds
    conversation_history = ""
    rounds: list[RoundRecord] = []
    publicly_known: set[str] = set()        # feature names visible to all agents so far
    agent_novel_counts: dict[str, int] = {aid: 0 for aid in agent_ids}
    agent_total_counts: dict[str, int] = {aid: 0 for aid in agent_ids}
    first_decisive_round: Optional[int] = None
    decisive_set = set(scenario.decisive_features)

    for round_num in range(1, cfg.num_rounds + 1):
        log.info(f"[{scenario.id}] === Round {round_num}/{cfg.num_rounds} ===")

        mod_open_text, mod_stance = moderator.open_round(
            round_num, cfg.num_rounds, conversation_history,
        )
        stance_str = f"{mod_stance['decision']} (confidence: {mod_stance['confidence']:.2f})"
        conversation_history += f"\n\n--- ROUND {round_num} ---\n[MODERATOR]: {mod_open_text}\n"

        round_turns: list[dict] = []
        round_messages = ""
        position_map = {a: i + 1 for i, a in enumerate(speaking_order)}

        for aid in speaking_order:
            agent = agents[aid]

            # Per-turn bid elicitation for bid_to_speak condition
            turn_bid = 0.0
            if cfg.incentive == "bid_to_speak":
                turn_bid, bid_failed = agent.elicit_turn_bid(round_num, cfg.num_rounds)
                if bid_failed:
                    moderator.parse_failures["bid_fallback"] += 1
                agent_turn_bids[aid] += turn_bid

            turn = agent.speak(
                round_num=round_num, total_rounds=cfg.num_rounds,
                conversation_history=conversation_history,
                moderator_stance=stance_str,
            )

            # Build public message
            public_msg = turn.message
            if "<disclosed>" in public_msg:
                public_msg = public_msg[:public_msg.index("<disclosed>")].strip()
            if turn.features_disclosed:
                disclosed_lines = "\n".join(
                    f"  {k}: {v}" for k, v in turn.features_disclosed.items()
                )
                public_msg += f"\n[Disclosed: {disclosed_lines}]"

            comm_tokens = max(1, count_tokens(public_msg, cfg.model))

            entry = f"[{aid}]: {public_msg}"
            conversation_history += f"\n{entry}\n"
            round_messages += f"\n{entry}\n"

            # Novelty tracking: is each newly disclosed feature already publicly known?
            for fname in turn.features_disclosed:
                agent_total_counts[aid] += 1
                if fname not in publicly_known:
                    agent_novel_counts[aid] += 1
                publicly_known.add(fname)

            # First decisive round
            if first_decisive_round is None and decisive_set & set(turn.features_disclosed.keys()):
                first_decisive_round = round_num

            round_turns.append({
                "agent_id": aid, "round_num": round_num,
                "speaking_position": position_map[aid],
                "message": public_msg, "raw_model_output": turn.message,
                "features_disclosed": turn.features_disclosed,
                "disclosure_cost": turn.disclosure_cost,
                "tokens_used": turn.tokens_used,
                "communication_tokens": comm_tokens,
                "spoke_without_new_disclosure": not bool(turn.features_disclosed),
                "turn_bid": turn_bid,
            })
            log.info(
                f"  [{aid}] comm={comm_tokens} | "
                f"disclosed={list(turn.features_disclosed.keys()) or 'NONE'} | "
                f"cost={turn.disclosure_cost}"
            )

        mod_summary, mod_stance_after = moderator.close_round(
            round_num, round_messages, conversation_history,
        )
        conversation_history += f"\n[MODERATOR SUMMARY]: {mod_summary}\n"

        rounds.append(RoundRecord(
            round_num=round_num, moderator_open=mod_stance,
            agent_turns=round_turns, moderator_summary=mod_summary,
            moderator_stance_after=mod_stance_after,
        ))

    # Final decision
    final = moderator.final_decision(conversation_history)
    is_correct = final["decision"].upper() == scenario.label.upper()
    log.info(f"[{scenario.id}] Final: {final['decision']} (truth={scenario.label}, correct={is_correct})")

    # Aggregate
    agent_disclosures = {aid: list(a.disclosed_features.keys()) for aid, a in agents.items()}
    agent_disclosure_costs = {aid: a.total_disclosure_cost for aid, a in agents.items()}
    agent_tokens_dict = {aid: a.total_tokens for aid, a in agents.items()}

    agent_comm_tokens: dict[str, int] = {aid: 0 for aid in agent_ids}
    for rnd in rounds:
        for t in rnd.agent_turns:
            agent_comm_tokens[t["agent_id"]] += t.get("communication_tokens", 0)

    contribution_scores: dict[str, float] = {}
    if rate_contributions:
        for aid in agent_ids:
            contribution_scores[aid] = sum(
                moderator.contribution_ratings.get(r, {}).get(aid, 0.0)
                for r in range(1, cfg.num_rounds + 1)
            )

    posthoc_scores = compute_posthoc_contribution_scores(agent_disclosures, scenario)
    token_costs_dict = {
        aid: agent_comm_tokens.get(aid, 0) * cfg.token_cost for aid in agent_ids
    }

    # Counterfactual contribution scoring (expensive: N*R extra LLM calls)
    cmc_scores: dict[str, float] = {}
    if cfg.counterfactual_contribution and cfg.incentive in (
        "counterfactual_contribution", "contribution", "contribution_oracle"
    ):
        log.info(f"[{scenario.id}] Computing CMC scores ({len(agent_ids)} agents × {cfg.num_rounds} rounds)…")
        cmc_scores = _compute_cmc_scores(rounds, agent_ids, moderator, scenario.label, is_correct)
        log.info(f"[{scenario.id}] CMC: { {a: f'{v:.2f}' for a, v in cmc_scores.items()} }")

    # Select contribution scores for payoffs:
    # contribution          → moderator-rated (actual practical mechanism)
    # contribution_oracle   → posthoc ground-truth decisive-feature credit (oracle upper bound)
    # counterfactual_contribution → CMC scores (more principled practical mechanism)
    # hybrid                → moderator-rated contribution (same as contribution)
    if cfg.incentive == "contribution":
        reward_contribution_scores = contribution_scores
    elif cfg.incentive == "contribution_oracle":
        reward_contribution_scores = posthoc_scores
    elif cfg.incentive == "counterfactual_contribution":
        reward_contribution_scores = cmc_scores if cmc_scores else contribution_scores
    elif cfg.incentive == "hybrid":
        reward_contribution_scores = contribution_scores
    else:
        reward_contribution_scores = {}

    # Normalize incentive name for payoff dispatch
    _payoff_incentive = cfg.incentive
    if cfg.incentive in ("contribution_oracle", "counterfactual_contribution"):
        _payoff_incentive = "contribution"
    payoffs = compute_payoffs(
        incentive=_payoff_incentive, agent_ids=agent_ids, is_correct=is_correct,
        reward_pool=cfg.contribution_reward_pool,
        disclosure_costs=agent_disclosure_costs, token_costs=token_costs_dict,
        contribution_scores=reward_contribution_scores, bids=bids,
        bid_multiplier=cfg.stake_multiplier,
        hybrid_alpha=cfg.hybrid_alpha,
        turn_bids=agent_turn_bids,
    )

    all_disclosed = set()
    for feats in agent_disclosures.values():
        all_disclosed.update(feats)

    decisive_surfaced = [f for f in scenario.decisive_features if f in all_disclosed]
    misleading_surfaced = [f for f in scenario.misleading_features if f in all_disclosed]
    decisive_rate = (
        len(decisive_surfaced) / len(scenario.decisive_features)
        if scenario.decisive_features else 1.0
    )

    mbw, mpd = _compute_misleading_timing(
        rounds, set(scenario.misleading_features), set(scenario.decisive_features),
        is_correct, misleading_surfaced,
    )

    # Novelty rates per agent (fraction of their disclosures that were genuinely new)
    agent_novelty_rates = {
        aid: (agent_novel_counts[aid] / agent_total_counts[aid])
        if agent_total_counts[aid] > 0 else 0.0
        for aid in agent_ids
    }

    return DeliberationResult(
        scenario_id=scenario.id, domain=scenario.domain, question=scenario.question,
        ground_truth=scenario.label, incentive=cfg.incentive, token_cost=cfg.token_cost,
        num_agents=num_agents, num_rounds=cfg.num_rounds, agent_order=speaking_order,
        rounds=rounds, final_decision=final, is_correct=is_correct,
        agent_disclosures=agent_disclosures,
        agent_disclosure_costs=agent_disclosure_costs,
        agent_tokens=agent_tokens_dict,
        agent_communication_tokens=agent_comm_tokens,
        agent_stakes=(
            bids if cfg.incentive == "stake"
            else agent_turn_bids if cfg.incentive == "bid_to_speak"
            else {}
        ),
        agent_payoffs={aid: asdict(p) for aid, p in payoffs.items()},
        decisive_features_surfaced=decisive_surfaced,
        decisive_surfacing_rate=decisive_rate,
        misleading_features_surfaced=misleading_surfaced,
        total_tokens=sum(agent_tokens_dict.values()),
        total_communication_tokens=sum(agent_comm_tokens.values()),
        total_disclosure_cost=sum(agent_disclosure_costs.values()),
        contribution_scores=contribution_scores,
        posthoc_contribution_scores=posthoc_scores,
        misleading_before_wrong=mbw, misleading_preceded_decisive=mpd,
        moderator_trajectory=moderator.state.history,
        agents_holding_decisive=[a for a in agent_ids if scenario.agent_holds_decisive(a)],
        ablate_decision_rules=cfg.ablate_decision_rules,
        parse_failures=moderator.parse_failures,
        extraction_api_tokens=0,
        counterfactual_contribution_scores=cmc_scores,
        agent_novelty_rates=agent_novelty_rates,
        first_decisive_round=first_decisive_round,
    )
