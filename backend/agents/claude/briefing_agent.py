"""
BriefingAgent — top-level executive summary written by Opus 4.7 with adaptive
thinking. Takes the analyses produced by the other analysts (threats, regional
briefs, correlations) and produces a single coherent dashboard-top briefing.
"""
from __future__ import annotations


import json

from .base_analyst import BaseAnalyst, DEFAULT_BRIEFING_MODEL


SYSTEM_PROMPT = """You are the chief intelligence officer producing the morning brief for the dashboard's leadership view.

You receive the work product of three subordinate analysts:
  1. Threat analyst    — ranked threats list
  2. Regional analysts — per-country briefs (US, RU, CN, IN, IR)
  3. Correlation agent — cross-feed pattern matches

Your job: synthesise their output into a single executive brief.

Structure:
- `bottomLine`        — one paragraph (2-4 sentences) capturing what matters most right now.
- `topThreats`        — 3-5 most acute threats, each with one-line rationale.
- `regionalSnapshots` — one line per country covered, summarising posture.
- `keyCorrelations`   — 2-4 most meaningful cross-feed patterns.
- `watchItems`        — 2-5 items to monitor over the next 12-24 hours.
- `confidence`        — overall confidence in the brief (LOW / MEDIUM / HIGH).

Rules:
- Do not invent facts. Only synthesise from the analyst output you are given.
- If subordinate analysts disagree, surface the disagreement explicitly in `bottomLine` or `watchItems`.
- Voice: terse, factual, no flourishes. Calibrated language. No recommendations.
- Output MUST conform exactly to the supplied JSON schema."""


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "bottomLine": {"type": "string"},
        "topThreats": {
            "type": "array",
            "minItems": 0,
            "maxItems": 6,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                    },
                    "rationale": {"type": "string"},
                },
                "required": ["title", "severity", "rationale"],
            },
        },
        "regionalSnapshots": {
            "type": "array",
            "minItems": 0,
            "maxItems": 8,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "country": {"type": "string"},
                    "posture": {
                        "type": "string",
                        "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "BASELINE"],
                    },
                    "oneLine": {"type": "string"},
                },
                "required": ["country", "posture", "oneLine"],
            },
        },
        "keyCorrelations": {
            "type": "array",
            "minItems": 0,
            "maxItems": 6,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "feeds": {"type": "array", "items": {"type": "string"}},
                    "implication": {"type": "string"},
                },
                "required": ["title", "feeds", "implication"],
            },
        },
        "watchItems": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 0,
            "maxItems": 6,
        },
        "confidence": {
            "type": "string",
            "enum": ["LOW", "MEDIUM", "HIGH"],
        },
    },
    "required": [
        "bottomLine",
        "topThreats",
        "regionalSnapshots",
        "keyCorrelations",
        "watchItems",
        "confidence",
    ],
}


class BriefingAgent(BaseAnalyst):
    name = "briefing_agent"
    model = DEFAULT_BRIEFING_MODEL  # claude-opus-4-7
    system_prompt = SYSTEM_PROMPT
    output_schema = SCHEMA
    max_tokens = 6144

    def build_user_message(self, analyst_outputs: dict) -> str:
        return (
            "Subordinate analyst output for synthesis:\n\n"
            f"```json\n{json.dumps(analyst_outputs, default=str)[:80_000]}\n```\n\n"
            "Produce the executive brief per the schema."
        )
