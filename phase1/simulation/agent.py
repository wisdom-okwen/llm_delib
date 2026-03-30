from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from simulation.prompts import build_system_prompt, build_user_prompt, build_final_vote_prompt
from simulation.models import MODEL_REGISTRY


@dataclass
class Feature:
    name: str
    value: Any
    cost: int
    signal_strength: Optional[float] = None
    tags: List[str] = field(default_factory=list)

    @property
    def is_decisive(self) -> bool:
        return "decisive" in self.tags

    @property
    def is_misleading(self) -> bool:
        return "misleading" in self.tags


@dataclass
class AgentAction:
    agent_id: str
    revealed_features: List[str]
    message: str
    reasoning_summary: str
    total_disclosure_cost: int
    raw_response: str
    contributed: bool


@dataclass
class AgentVote:
    agent_id: str
    answer: str
    confidence: Optional[float]
    reasoning_summary: str
    raw_response: str


class Agent:
    def __init__(
        self,
        agent_id: str,
        private_features: List[Feature],
        model_type: str,
        model_name: str,
        temperature: float = 0.2,
        max_message_words: int = 80,
    ) -> None:
        self.agent_id = agent_id
        self.private_features = private_features
        self.model_type = model_type
        self.model_name = model_name
        self.temperature = temperature
        self.max_message_words = max_message_words

        self.feature_map: Dict[str, Feature] = {f.name: f for f in private_features}
        self.contribution_count: int = 0

    def speak(
        self,
        question: str,
        conversation_history: List[Dict[str, Any]],
        round_idx: int,
        include_costs_in_prompt: bool = True,
        include_shared_reward_in_prompt: bool = True,
        shared_reward_if_correct: float = 1.0,
        allow_empty_message: bool = True,
    ) -> AgentAction:
        system_prompt = build_system_prompt(max_message_words=self.max_message_words)

        user_prompt = build_user_prompt(
            agent_id=self.agent_id,
            question=question,
            private_features=self.private_features,
            conversation_history=conversation_history,
            round_idx=round_idx,
            include_costs_in_prompt=include_costs_in_prompt,
            include_shared_reward_in_prompt=include_shared_reward_in_prompt,
            shared_reward_if_correct=shared_reward_if_correct,
            allow_empty_message=allow_empty_message,
        )

        raw_text = self._call_model(system_prompt=system_prompt, user_prompt=user_prompt)
        parsed = self._parse_json_response(raw_text)

        revealed_features = self._validate_revealed_features(parsed.get("revealed_features", []))
        message = str(parsed.get("message", "")).strip()
        reasoning_summary = str(parsed.get("reasoning_summary", "")).strip()
        total_cost = sum(self.feature_map[name].cost for name in revealed_features)

        has_substantive_message = message and message.lower() not in ["defer", "pass", "no", "skip"]
        contributed = bool(revealed_features or has_substantive_message)
        
        if contributed:
            self.contribution_count += 1

        return AgentAction(
            agent_id=self.agent_id,
            revealed_features=revealed_features,
            message=message,
            reasoning_summary=reasoning_summary,
            total_disclosure_cost=total_cost,
            raw_response=raw_text,
            contributed=contributed,
        )

    def final_vote(
        self,
        question: str,
        conversation_history: List[Dict[str, Any]],
    ) -> AgentVote:
        system_prompt = (
            "You are making a final decision after group deliberation. "
            "Return only valid JSON."
        )
        user_prompt = build_final_vote_prompt(
            agent_id=self.agent_id,
            question=question,
            private_features=self.private_features,
            conversation_history=conversation_history,
        )

        raw_text = self._call_model(system_prompt=system_prompt, user_prompt=user_prompt)
        parsed = self._parse_json_response(raw_text)

        answer = str(parsed.get("answer", "UNKNOWN")).strip()
        confidence = parsed.get("confidence", None)
        reasoning_summary = str(parsed.get("reasoning_summary", "")).strip()

        try:
            if confidence is not None:
                confidence = float(confidence)
        except Exception:
            confidence = None

        return AgentVote(
            agent_id=self.agent_id,
            answer=answer,
            confidence=confidence,
            reasoning_summary=reasoning_summary,
            raw_response=raw_text,
        )

    def get_private_feature_names(self) -> List[str]:
        return [f.name for f in self.private_features]

    def _call_model(self, system_prompt: str, user_prompt: str) -> str:
        try:
            model_fn = MODEL_REGISTRY[self.model_type]
            return model_fn(
                model=self.model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature,
            )
        except Exception as e:
            return json.dumps(
                {
                    "revealed_features": [],
                    "message": "",
                    "reasoning_summary": f"Model call failed: {str(e)}",
                }
            )


    def _parse_json_response(self, raw_text: str) -> Dict[str, Any]:
        # print(f"[RAW RESPONSE]: {raw_text[:500]}")
        cleaned = raw_text.strip()
        # Strip Qwen3 thinking blocks
        if "<think>" in cleaned and "</think>" in cleaned:
            cleaned = cleaned.split("</think>")[-1].strip()
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        return {}

    def _validate_revealed_features(self, names: List[Any]) -> List[str]:
        if not isinstance(names, list):
            return []

        valid_names: List[str] = []
        for item in names:
            if isinstance(item, str) and item in self.feature_map:
                valid_names.append(item)

        seen = set()
        deduped = []
        for name in valid_names:
            if name not in seen:
                deduped.append(name)
                seen.add(name)

        return deduped