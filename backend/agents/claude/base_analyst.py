"""
Base class for every Claude-powered analyst in the team.

Wraps `anthropic.AsyncAnthropic` with:
  - Lazy client construction so missing API key fails gracefully
  - Shared TTL cache (5 min) so the dashboard doesn't re-bill on every poll
  - Standardised JSON-output call using `output_config.format` (no prefills)
  - Prompt caching on the (large, frozen) system prompt
  - Adaptive thinking for Opus models
"""
from __future__ import annotations


import json
import logging
import os
from typing import Any, Optional

from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Sensible defaults — opus for the top briefing, haiku for the per-analyst syntheses.
DEFAULT_BRIEFING_MODEL = "claude-opus-4-7"
DEFAULT_ANALYST_MODEL = "claude-haiku-4-5"

# 5-minute analyst-result cache. The underlying OSINT data refreshes on similar
# cadences, so this stops the dashboard from re-billing every panel refresh.
_analyst_cache: TTLCache = TTLCache(maxsize=128, ttl=300)


def claude_available() -> bool:
    """True iff ANTHROPIC_API_KEY is set so the team can actually run."""
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


class BaseAnalyst:
    """
    Subclasses define:
      - `name`        — analyst label (for logs + cache keys)
      - `model`       — Claude model ID (defaults to Haiku 4.5)
      - `system_prompt` — the analyst's role / instructions (cached)
      - `output_schema` — JSON Schema the response must conform to
      - `build_user_message(raw_data: dict) -> str` — turns OSINT payload into prompt
    """

    name: str = "analyst"
    model: str = DEFAULT_ANALYST_MODEL
    system_prompt: str = ""
    output_schema: dict[str, Any] = {}
    max_tokens: int = 4096

    def __init__(self):
        self._client = None  # lazy

    # ------------------------------------------------------------------
    # Client
    # ------------------------------------------------------------------
    @property
    def client(self):
        if self._client is not None:
            return self._client
        if not claude_available():
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set — Claude analyst team is disabled."
            )
        # Imported lazily so the rest of the backend still boots without anthropic installed.
        import anthropic
        self._client = anthropic.AsyncAnthropic()
        return self._client

    # ------------------------------------------------------------------
    # Subclass hook
    # ------------------------------------------------------------------
    def build_user_message(self, raw_data: dict) -> str:
        raise NotImplementedError

    def cache_key(self, raw_data: dict) -> str:
        # Cache on a coarse signature so near-identical payloads hit the cache.
        # Use updated-timestamp + top-level counts rather than the full payload.
        sig_parts: list[str] = [self.name]
        for k, v in sorted(raw_data.items()):
            if isinstance(v, dict):
                inner = v.get("fetchedAt") or v.get("lastUpdated") or len(str(v))
                sig_parts.append(f"{k}={inner}")
            elif isinstance(v, list):
                sig_parts.append(f"{k}=len{len(v)}")
        return ":".join(sig_parts)[:512]

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------
    async def analyse(self, raw_data: dict) -> dict:
        """
        Run the analyst against a raw OSINT payload. Returns the parsed JSON
        response, or a structured error envelope on failure.
        """
        key = self.cache_key(raw_data)
        if key in _analyst_cache:
            return _analyst_cache[key]

        if not claude_available():
            return self._disabled_envelope()

        user_message = self.build_user_message(raw_data)

        # Adaptive thinking is supported on Opus 4.7 / Sonnet 4.6 / Haiku 4.5+.
        # On Opus 4.7 it defaults to display=omitted; we don't surface thinking
        # to the user here so omitted is fine.
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": [
                {
                    "type": "text",
                    "text": self.system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": [{"role": "user", "content": user_message}],
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "schema": self.output_schema,
                }
            },
        }

        # Adaptive thinking on Opus models — Haiku doesn't support it.
        if self.model.startswith("claude-opus"):
            request_kwargs["thinking"] = {"type": "adaptive"}
            request_kwargs["output_config"]["effort"] = "high"

        try:
            response = await self.client.messages.create(**request_kwargs)
        except Exception as exc:
            logger.error("%s analyst failed: %s", self.name, exc, exc_info=True)
            return {
                "error": f"{self.name} analyst failed: {exc}",
                "analyst": self.name,
                "model": self.model,
            }

        # Find the first text block and parse it.
        text_block = next(
            (b.text for b in response.content if getattr(b, "type", None) == "text"),
            "",
        )
        try:
            parsed = json.loads(text_block) if text_block else {}
        except json.JSONDecodeError as exc:
            logger.error("%s returned non-JSON: %s", self.name, exc)
            return {
                "error": f"{self.name} returned non-JSON output",
                "raw": text_block[:500],
                "analyst": self.name,
                "model": self.model,
            }

        result = {
            "analyst": self.name,
            "model": self.model,
            "stopReason": response.stop_reason,
            "usage": {
                "inputTokens": response.usage.input_tokens,
                "outputTokens": response.usage.output_tokens,
                "cacheReadInputTokens": getattr(response.usage, "cache_read_input_tokens", 0),
                "cacheCreationInputTokens": getattr(response.usage, "cache_creation_input_tokens", 0),
            },
            "analysis": parsed,
        }
        _analyst_cache[key] = result
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _disabled_envelope(self) -> dict:
        return {
            "analyst": self.name,
            "model": self.model,
            "disabled": True,
            "reason": (
                "ANTHROPIC_API_KEY is not configured. Set it in the backend "
                "environment to enable the Claude analyst team."
            ),
            "analysis": None,
        }
