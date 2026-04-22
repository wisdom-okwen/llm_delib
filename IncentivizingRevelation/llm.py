"""
LLM backend abstraction.

Thin wrapper around the OpenAI client that works with any
OpenAI-compatible API. Tracks token usage and dollar cost.
"""

import os
import logging
import time
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI, RateLimitError, APIStatusError, APIConnectionError

from config import Config

log = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Cumulative token and cost accounting."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    calls: int = 0
    cost_per_1m_input: float = 0.15
    cost_per_1m_output: float = 0.60

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def estimated_cost_usd(self) -> float:
        return (
            self.prompt_tokens * self.cost_per_1m_input / 1_000_000
            + self.completion_tokens * self.cost_per_1m_output / 1_000_000
        )

    def record(self, prompt_tok: int, completion_tok: int):
        self.prompt_tokens += prompt_tok
        self.completion_tokens += completion_tok
        self.calls += 1

    def summary(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "api_calls": self.calls,
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
        }


class LLM:
    """Unified LLM interface with retry and cost tracking."""

    def __init__(self, cfg: Config):
        api_key = os.environ.get(cfg.api_key_env, "no-key-needed")
        kwargs = {"api_key": api_key}
        if cfg.base_url:
            kwargs["base_url"] = cfg.base_url

        self.client = OpenAI(**kwargs)
        self.model = cfg.model
        self.temperature = cfg.temperature
        self.max_tokens = cfg.max_tokens
        self.usage = TokenUsage(
            cost_per_1m_input=cfg.cost_per_1m_input,
            cost_per_1m_output=cfg.cost_per_1m_output,
        )
        self._max_retries = 5
        self._retry_base_delay = 2.0

    def _call(
        self,
        messages: list[dict],
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> tuple[str, int]:
        temp = temperature if temperature is not None else self.temperature
        mtok = max_tokens or self.max_tokens
        delay = self._retry_base_delay

        for attempt in range(1, self._max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=mtok,
                )
                text = response.choices[0].message.content or ""
                prompt_tok = response.usage.prompt_tokens if response.usage else 0
                completion_tok = response.usage.completion_tokens if response.usage else 0
                self.usage.record(prompt_tok, completion_tok)
                return text, completion_tok

            except RateLimitError as e:
                if attempt == self._max_retries:
                    raise
                log.warning(f"Rate limit (attempt {attempt}); retrying in {delay:.1f}s")
                time.sleep(delay)
                delay *= 2

            except (APIConnectionError, APIStatusError) as e:
                if attempt == self._max_retries:
                    raise
                log.warning(f"API error (attempt {attempt}): {e}; retrying in {delay:.1f}s")
                time.sleep(delay)
                delay *= 2

            except Exception as e:
                log.error(f"LLM call failed (non-retryable): {e}")
                raise

        # Should not reach here, but satisfy type checker
        raise RuntimeError("Exhausted retries without success or exception")

    def generate(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> tuple[str, int]:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return self._call(messages, temperature, max_tokens)

    def generate_with_history(
        self,
        system: str,
        history: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> tuple[str, int]:
        messages = [{"role": "system", "content": system}] + history
        return self._call(messages, temperature, max_tokens)
