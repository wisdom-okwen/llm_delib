"""
Agent and Moderator classes.

Agents hold private features, decide what to disclose, and generate messages.
The Moderator steers the deliberation and tracks its evolving stance.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from llm import LLM
from data import Scenario, Feature
from prompts import (
    AGENT_SYSTEM, AGENT_SYSTEM_NEUTRAL, AGENT_TURN, STAKE_ELICIT, BID_TO_SPEAK_ELICIT,
    DECISION_RULES_BLOCK, DECISION_RULES_BLOCK_NEUTRAL,
    MODERATOR_SYSTEM, MODERATOR_ROUND_START, MODERATOR_ROUND_SUMMARY,
    MODERATOR_FINAL, CONTRIBUTION_RATING_PROMPT,
    FREE_DEBATE_EXTRACT_PROMPT,
    INCENTIVE_DESCRIPTIONS,
    format_feature_table, format_token_cost_note,
)

log = logging.getLogger(__name__)


# ── Parsing helpers ─────────────────────────────────────────────────────

def parse_disclosed(text: str) -> dict[str, str]:
    match = re.search(r"<disclosed>(.*?)</disclosed>", text, re.DOTALL)
    if not match:
        return {}
    block = match.group(1).strip()
    if block.upper() == "NONE":
        return {}
    result = {}
    for line in block.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            name, value = line.split(":", 1)
            result[name.strip()] = value.strip()
    return result


def parse_stance(text: str) -> dict:
    """Parse a <stance> block. Returns decision=UNKNOWN on failure (never silently defaults)."""
    match = re.search(r"<stance>(.*?)</stance>", text, re.DOTALL)
    if not match:
        return {"decision": "UNKNOWN", "confidence": 0.5, "reasoning": "", "_parse_ok": False}
    block = match.group(1).strip()
    result: dict = {"decision": "UNKNOWN", "confidence": 0.5, "reasoning": "", "_parse_ok": True}
    for line in block.split("\n"):
        line = line.strip()
        if line.lower().startswith("decision:"):
            val = line.split(":", 1)[1].strip().upper()
            # Require an unambiguous YES or NO; otherwise leave as UNKNOWN
            has_yes = "YES" in val
            has_no  = "NO" in val
            if has_yes and not has_no:
                result["decision"] = "YES"
            elif has_no and not has_yes:
                result["decision"] = "NO"
            else:
                result["decision"] = "UNKNOWN"
                result["_parse_ok"] = False
        elif line.lower().startswith("confidence:"):
            try:
                result["confidence"] = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.lower().startswith("reasoning:"):
            result["reasoning"] = line.split(":", 1)[1].strip()
    return result


def parse_final_decision(text: str) -> dict:
    """Parse a <final_decision> block. Falls back to token-count heuristic only if needed,
    and marks the result with _fallback=True so callers can detect and retry."""
    match = re.search(r"<final_decision>(.*?)</final_decision>", text, re.DOTALL)
    if not match:
        # Heuristic fallback: count YES vs NO tokens in the full response
        upper = text.upper()
        yes_count = upper.count("YES")
        no_count  = upper.count("NO")
        decision = "YES" if yes_count > no_count else "NO"
        log.warning(
            f"parse_final_decision: no <final_decision> block found — "
            f"heuristic fallback (YES={yes_count}, NO={no_count}) → {decision}"
        )
        return {"decision": decision, "confidence": 0.5,
                "reasoning": text[:200], "_fallback": True, "_parse_ok": False}
    result = parse_stance(f"<stance>{match.group(1)}</stance>")
    result["_fallback"] = False
    return result


def parse_bid(text: str, budget: float) -> tuple[float, str]:
    try:
        cleaned = text.strip()
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
        obj = json.loads(cleaned)
        bid = float(obj.get("bid", 0))
        reasoning = obj.get("reasoning", "")
        return (min(max(bid, 0), budget), reasoning)
    except (json.JSONDecodeError, ValueError):
        numbers = re.findall(r"[\d.]+", text)
        if numbers:
            return (min(max(float(numbers[0]), 0), budget), "")
        return (budget * 0.5, "parse_failed")


def parse_contributions(text: str) -> dict[str, float]:
    match = re.search(r"<contributions>(.*?)</contributions>", text, re.DOTALL)
    if not match:
        return {}
    result = {}
    for line in match.group(1).strip().split("\n"):
        line = line.strip()
        if ":" in line:
            agent_id, score = line.split(":", 1)
            try:
                result[agent_id.strip()] = float(score.strip())
            except ValueError:
                pass
    return result


def extract_free_debate_features(
    agent_message: str,
    feature_table: dict,
    llm: LLM,
) -> list[str]:
    """Extract which features were revealed in a free-form message via LLM."""
    prompt = FREE_DEBATE_EXTRACT_PROMPT.format(
        agent_message=agent_message,
        feature_table=format_feature_table(feature_table),
    )
    try:
        response, _ = llm.generate(
            system="You extract structured information from text. Respond only with JSON.",
            user=prompt,
            max_tokens=100,
        )
        cleaned = response.strip()
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
        result = json.loads(cleaned)
        if isinstance(result, list):
            return [f for f in result if isinstance(f, str) and f in feature_table]
        return []
    except Exception as e:
        log.debug(f"Feature extraction failed: {e}")
        return []


# ── Prose leakage helpers ───────────────────────────────────────────────

_COMMON_TOKENS = frozenset({
    "yes", "no", "low", "high", "none", "true", "false",
    "normal", "positive", "negative", "unknown", "male", "female",
})


def detect_prose_leakage(
    prose: str,
    features: dict[str, Feature],
    already_disclosed: set[str],
) -> list[str]:
    """Return feature names whose values appear verbatim in prose."""
    leaked = []
    prose_lower = prose.lower()
    for fname, feat in features.items():
        if fname in already_disclosed:
            continue
        val_str = str(feat.value).strip()
        if (
            len(val_str) >= 4
            and val_str.lower() not in _COMMON_TOKENS
            and val_str.lower() in prose_lower
        ):
            leaked.append(fname)
    return leaked


# ── Agent ───────────────────────────────────────────────────────────────

@dataclass
class AgentTurn:
    agent_id: str
    round_num: int
    message: str
    features_disclosed: dict[str, str]
    disclosure_cost: float
    tokens_used: int
    bid: Optional[float] = None


class Agent:
    """A deliberation agent holding private features."""

    def __init__(
        self,
        agent_id: str,
        features: dict[str, Feature],
        scenario: Scenario,
        llm: LLM,
        incentive: str,
        token_cost: float = 0.0,
        stake_amount: Optional[float] = None,
        stake_budget: float = 20.0,
        stake_multiplier: float = 3.0,
        num_agents: int = 10,
        ablate_decision_rules: bool = False,
        neutral_agent_wording: bool = False,
    ):
        self.agent_id = agent_id
        self.features = features
        self.scenario = scenario
        self.llm = llm
        self.incentive = incentive
        self.token_cost = token_cost
        self.stake_amount = stake_amount
        self.stake_budget = stake_budget
        self.stake_multiplier = stake_multiplier
        self.num_agents = num_agents
        self.ablate_decision_rules = ablate_decision_rules
        self.neutral_agent_wording = neutral_agent_wording
        self.remaining_bid_budget: float = stake_budget  # for bid_to_speak; decremented each turn

        self.disclosed_features: dict[str, str] = {}
        self.total_disclosure_cost: float = 0.0
        self.total_tokens: int = 0
        self.turns: list[AgentTurn] = []

        self._system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        feat_table_data = {
            fname: {"value": feat.value, "cost": feat.cost}
            for fname, feat in self.features.items()
        }
        incentive_desc = INCENTIVE_DESCRIPTIONS[self.incentive]
        if self.incentive == "stake" and self.stake_amount is not None:
            incentive_desc = incentive_desc.format(
                bid_amount=self.stake_amount,
                bid_budget=self.stake_budget,
                bid_multiplier=self.stake_multiplier,
            )
        elif self.incentive == "bid_to_speak":
            incentive_desc = incentive_desc.format(
                bid_budget=self.stake_budget,
                bid_multiplier=self.stake_multiplier,
            )

        if self.ablate_decision_rules:
            decision_rules = ""
        elif self.neutral_agent_wording:
            decision_rules = DECISION_RULES_BLOCK_NEUTRAL
        else:
            decision_rules = DECISION_RULES_BLOCK

        template = AGENT_SYSTEM_NEUTRAL if self.neutral_agent_wording else AGENT_SYSTEM

        return template.format(
            agent_id=self.agent_id,
            num_agents=self.num_agents,
            question=self.scenario.question,
            domain=self.scenario.domain,
            feature_table=format_feature_table(feat_table_data),
            incentive_description=incentive_desc,
            token_cost_note=format_token_cost_note(self.token_cost),
            decision_rules=decision_rules,
        )

    def speak(
        self,
        round_num: int,
        total_rounds: int,
        conversation_history: str,
        moderator_stance: str,
    ) -> AgentTurn:
        user_prompt = AGENT_TURN.format(
            round_num=round_num,
            total_rounds=total_rounds,
            conversation_history=conversation_history or "(No conversation yet.)",
            moderator_stance=moderator_stance or "(No stance yet.)",
        )
        response, tokens = self.llm.generate(
            system=self._system_prompt,
            user=user_prompt,
        )

        # Parse disclosed; validate against actual feature names and use stored values
        newly_disclosed_raw = parse_disclosed(response)
        newly_disclosed = {
            fname: str(self.features[fname].value)
            for fname in newly_disclosed_raw
            if fname in self.features
        }

        # Detect prose leakage and auto-charge
        prose_part = (
            response[:response.index("<disclosed>")].strip()
            if "<disclosed>" in response else response.strip()
        )
        leaked = detect_prose_leakage(
            prose_part, self.features,
            set(newly_disclosed.keys()) | set(self.disclosed_features.keys()),
        )
        for fname in leaked:
            log.warning(
                f"{self.agent_id}: private value for '{fname}' leaked in prose — auto-charging."
            )
            newly_disclosed[fname] = str(self.features[fname].value)

        # Cost accounting (only genuinely new disclosures)
        round_cost = 0.0
        for fname in newly_disclosed:
            if fname not in self.disclosed_features:
                round_cost += self.features[fname].cost
                self.disclosed_features[fname] = newly_disclosed[fname]

        self.total_disclosure_cost += round_cost
        self.total_tokens += tokens

        turn = AgentTurn(
            agent_id=self.agent_id,
            round_num=round_num,
            message=response,
            features_disclosed=newly_disclosed,
            disclosure_cost=round_cost,
            tokens_used=tokens,
            bid=self.stake_amount,
        )
        self.turns.append(turn)
        return turn

    def elicit_stake(self) -> tuple[float, bool]:
        feat_table_data = {
            fn: {"value": f.value, "cost": f.cost}
            for fn, f in self.features.items()
        }
        prompt = STAKE_ELICIT.format(
            question=self.scenario.question,
            feature_table=format_feature_table(feat_table_data),
            bid_budget=self.stake_budget,
            bid_multiplier=self.stake_multiplier,
        )
        response, _ = self.llm.generate(
            system="You are a strategic agent deciding how much to stake.",
            user=prompt,
            max_tokens=150,
        )
        bid, reasoning = parse_bid(response, self.stake_budget)
        if reasoning == "parse_failed":
            log.warning(f"{self.agent_id}: bid parse failed — defaulting to budget/2")
        self.stake_amount = bid
        self._system_prompt = self._build_system_prompt()
        log.debug(f"{self.agent_id} stake={bid:.1f}: {reasoning}")
        return bid, reasoning == "parse_failed"

    def elicit_turn_bid(self, round_num: int, total_rounds: int) -> tuple[float, bool]:
        """Elicit a per-turn bid for the bid_to_speak mechanism.

        Returns (bid_amount, parse_failed). Bid is capped at remaining_bid_budget.
        """
        if self.remaining_bid_budget <= 0:
            return 0.0, False

        undisclosed = {
            fname: {"value": feat.value, "cost": feat.cost}
            for fname, feat in self.features.items()
            if fname not in self.disclosed_features
        }
        prompt = BID_TO_SPEAK_ELICIT.format(
            question=self.scenario.question,
            round_num=round_num,
            total_rounds=total_rounds,
            remaining_budget=self.remaining_bid_budget,
            total_budget=self.stake_budget,
            bid_multiplier=self.stake_multiplier,
            feature_table=(
                format_feature_table(undisclosed) if undisclosed
                else "(all features already disclosed)"
            ),
        )
        response, _ = self.llm.generate(
            system="You are a strategic agent deciding how much to bid to speak this turn.",
            user=prompt,
            max_tokens=150,
        )
        bid, reasoning = parse_bid(response, self.remaining_bid_budget)
        parse_failed = reasoning == "parse_failed"
        if parse_failed:
            log.warning(f"{self.agent_id}: turn-bid parse failed r{round_num} — defaulting to budget/4")
            bid = self.remaining_bid_budget * 0.25
        self.remaining_bid_budget = max(0.0, self.remaining_bid_budget - bid)
        log.debug(
            f"{self.agent_id} r{round_num} bid={bid:.1f} "
            f"remaining={self.remaining_bid_budget:.1f}: {reasoning}"
        )
        return bid, parse_failed


# ── Moderator ───────────────────────────────────────────────────────────

@dataclass
class ModeratorState:
    decision: str = "UNKNOWN"
    confidence: float = 0.5
    reasoning: str = ""
    history: list[dict] = field(default_factory=list)


class Moderator:
    """Moderator: announces stance, summarizes, optionally rates contributions."""

    def __init__(
        self,
        scenario: Scenario,
        llm: LLM,
        rate_contributions: bool = False,
        num_agents: int = 10,
    ):
        self.scenario = scenario
        self.llm = llm
        self.rate_contributions = rate_contributions
        self.num_agents = num_agents
        self.state = ModeratorState()
        self.contribution_ratings: dict[int, dict[str, float]] = {}
        self.parse_failures: dict[str, int] = {
            "stance_unknown": 0,   # open/close rounds returned UNKNOWN decision
            "final_fallback": 0,   # final decision used heuristic fallback
            "final_unknown": 0,    # final decision still UNKNOWN after retry
            "bid_fallback": 0,     # bid parsing fell back to heuristic
        }

        self._system_prompt = MODERATOR_SYSTEM.format(
            num_agents=num_agents,
            question=scenario.question,
            domain=scenario.domain,
        )

    def open_round(self, round_num, total_rounds, conversation_history):
        user_prompt = MODERATOR_ROUND_START.format(
            round_num=round_num,
            total_rounds=total_rounds,
            conversation_history=conversation_history or "(Deliberation is just beginning.)",
        )
        response, _ = self.llm.generate(system=self._system_prompt, user=user_prompt)
        stance = parse_stance(response)
        if not stance.get("_parse_ok", True):
            self.parse_failures["stance_unknown"] += 1
            log.warning(f"[MOD open r{round_num}] parse failure — stance UNKNOWN")
        self.state.decision = stance["decision"]
        self.state.confidence = stance["confidence"]
        self.state.reasoning = stance["reasoning"]
        self.state.history.append({"round": round_num, "event": "open", **stance})
        log.info(
            f"[MOD open r{round_num}] {stance['decision']} "
            f"conf={stance['confidence']:.2f} | {stance['reasoning']}"
        )
        return response, stance

    def close_round(self, round_num, round_messages, conversation_history):
        # Summary call — identical across conditions
        user_prompt = MODERATOR_ROUND_SUMMARY.format(
            round_num=round_num,
            round_messages=round_messages,
            conversation_history=conversation_history,
        )
        response, _ = self.llm.generate(
            system=self._system_prompt, user=user_prompt, max_tokens=700,
        )
        stance = parse_stance(response)
        if not stance.get("_parse_ok", True):
            self.parse_failures["stance_unknown"] += 1
            log.warning(f"[MOD close r{round_num}] parse failure — stance UNKNOWN")
        self.state.decision = stance["decision"]
        self.state.confidence = stance["confidence"]
        self.state.reasoning = stance["reasoning"]
        self.state.history.append({"round": round_num, "event": "close", **stance})
        log.info(
            f"[MOD close r{round_num}] {stance['decision']} "
            f"conf={stance['confidence']:.2f} | {stance['reasoning']}"
        )

        # Separate contribution rating call
        if self.rate_contributions:
            rating_prompt = CONTRIBUTION_RATING_PROMPT.format(
                round_num=round_num, round_messages=round_messages,
            )
            rating_resp, _ = self.llm.generate(
                system=self._system_prompt, user=rating_prompt, max_tokens=200,
            )
            ratings = parse_contributions(rating_resp)
            if ratings:
                self.contribution_ratings[round_num] = ratings

        return response, stance

    def final_decision(self, conversation_history):
        user_prompt = MODERATOR_FINAL.format(conversation_history=conversation_history)

        # Retry up to 2 times if parsing fails
        decision = None
        for attempt in range(2):
            response, _ = self.llm.generate(system=self._system_prompt, user=user_prompt)
            decision = parse_final_decision(response)
            if decision.get("_fallback"):
                self.parse_failures["final_fallback"] += 1
                log.warning(
                    f"[MOD final] attempt {attempt+1}: no <final_decision> block — heuristic used"
                )
            if decision["decision"] != "UNKNOWN":
                break
            log.warning(f"[MOD final] attempt {attempt+1}: decision still UNKNOWN, retrying")

        if decision["decision"] == "UNKNOWN":
            self.parse_failures["final_unknown"] += 1
            log.error("[MOD final] decision UNKNOWN after all retries — defaulting to NO")
            decision["decision"] = "NO"

        self.state.decision = decision["decision"]
        self.state.confidence = decision["confidence"]
        self.state.history.append({"round": "final", "event": "decision", **decision})
        return decision

    def eval_stance_fast(self, conversation_history: str) -> float:
        """Evaluate moderator confidence on a given conversation (for CMC scoring).

        Returns the confidence value (0.0–1.0) in the moderator's current
        leaning direction. Used for leave-one-out counterfactual scoring.
        Lower token budget keeps cost manageable.
        """
        user_prompt = (
            "Based on the conversation below, state your current stance.\n\n"
            f"CONVERSATION:\n{conversation_history}\n\n"
            "Use the <stance> format only. Be brief."
        )
        try:
            response, _ = self.llm.generate(
                system=self._system_prompt, user=user_prompt, max_tokens=80,
            )
            stance = parse_stance(response)
            return stance["confidence"]
        except Exception as e:
            log.debug(f"eval_stance_fast failed: {e}")
            return 0.5
