from __future__ import annotations

from typing import Any, Dict, List


def build_system_prompt(max_message_words: int = 80) -> str:
    return f"""
        You are an agent in a multi-agent deliberation task.

        CRITICAL INCENTIVE STRUCTURE:
        - You have private information (features) that others cannot see.
        - Each feature has a cost if you reveal it. YOU PAY THIS COST DIRECTLY.
        - If the group answers correctly, ALL agents share the reward equally (including those who revealed nothing).
        - If the group answers incorrectly, nobody gets a reward.

        THE DILEMMA: If you reveal a high-cost feature that helps the group, you bear the cost personally.
        But the reward is split equally among all agents, including those who contributed nothing.

        YOUR IMPACT: However, your contribution can be the difference between group success and failure.
        If your information helps the group answer correctly, ALL agents benefit—but only because YOU paid the cost.

        DECISION: You may:
        1. Reveal specific features that you think will help the group answer correctly
        2. Say "defer" if you believe you have nothing valuable to add
        3. Give your honest assessment without revealing private features

        If you choose to defer, simply respond with:
        {{
        "revealed_features": [],
        "message": "defer",
        "reasoning_summary": "brief reason why you're not contributing this round"
        }}

        If you choose to contribute, provide substantive information:
        {{
        "revealed_features": ["feature_name_1", "feature_name_2"],
        "message": "your analysis or findings",
        "reasoning_summary": "cost-benefit reasoning for your choices"
        }}

        Rules:
        - "revealed_features" must contain only private feature names you actually hold.
        - "message" must be at most {max_message_words} words (or "defer").
        - Do not use markdown fences.
        - Do not output anything except JSON.
        """.strip()


def build_user_prompt(
    agent_id: str,
    question: str,
    private_features: List[Any],
    conversation_history: List[Dict[str, Any]],
    round_idx: int,
    include_costs_in_prompt: bool = True,
    include_shared_reward_in_prompt: bool = True,
    shared_reward_if_correct: float = 1.0,
    allow_empty_message: bool = True,
) -> str:
    private_info_block = _format_private_features(
        private_features=private_features,
        include_costs_in_prompt=include_costs_in_prompt,
    )
    history_block = _format_conversation_history(conversation_history)

    reward_text = ""
    if include_shared_reward_in_prompt:
        reward_text = (
            f"If the group answer is correct, all agents receive the same shared reward "
            f"of {shared_reward_if_correct}.\n"
        )

    silence_text = (
        "You may choose to say nothing if revealing information is not worth the cost."
        if allow_empty_message
        else "You must provide some message, even if brief."
    )

    return f"""
        Agent ID: {agent_id}
        Round: {round_idx}

        Group question:
        {question}

        Your private information:
        {private_info_block}

        Conversation so far:
        {history_block}

        Decision context:
        {reward_text}{silence_text}

        Decide what to reveal in this round and return the required JSON only.
        """.strip()


def build_final_vote_prompt(
    agent_id: str,
    question: str,
    private_features: List[Any],
    conversation_history: List[Dict[str, Any]],
) -> str:
    private_info_block = _format_private_features(
        private_features=private_features,
        include_costs_in_prompt=True,
    )
    history_block = _format_conversation_history(conversation_history)

    return f"""
        You are Agent {agent_id}. After the discussion, make a final decision.

        Question:
        {question}

        Your private information:
        {private_info_block}

        Conversation history:
        {history_block}

        The question has a yes/no answer. You MUST map your conclusion to exactly
        "Yes" or "No" — no other words, synonyms, or phrases are permitted.

        Return ONLY valid JSON with exactly these fields:
        {{
        "answer": "Yes or No ONLY",
        "confidence": 0.0,
        "reasoning_summary": "brief explanation"
        }}
        """.strip()


def _format_private_features(private_features: List[Any], include_costs_in_prompt: bool) -> str:
    if not private_features:
        return "None"

    lines = []
    for feature in private_features:
        signal_text = (
            f", signal_strength={feature.signal_strength}"
            if feature.signal_strength is not None
            else ""
        )
        cost_text = f", cost={feature.cost}" if include_costs_in_prompt else ""
        lines.append(
            f"- {feature.name}: value={feature.value}{cost_text}{signal_text}"
        )
    return "\n".join(lines)


def _format_conversation_history(conversation_history: List[Dict[str, Any]]) -> str:
    if not conversation_history:
        return "No prior messages."

    lines = []
    for turn in conversation_history:
        speaker = turn.get("agent_id", "unknown_agent")
        message = turn.get("message", "")
        round_idx = turn.get("round", "?")
        lines.append(f"- Round {round_idx} | {speaker}: {message}")
    return "\n".join(lines)