"""
ThreatAnalyst — ranks the most acute threats across the raw OSINT feeds.

Input:  the aggregated swarm payload (flights, military aircraft, salvo events,
        outages, fires, drones, conflicts, ...).
Output: a ranked threats list with severity, region, summary, and supporting
        signal references.
"""
from __future__ import annotations


from .base_analyst import BaseAnalyst, DEFAULT_ANALYST_MODEL


SYSTEM_PROMPT = """You are a senior open-source intelligence (OSINT) threat analyst on a national-security desk. You work from publicly available data only and you do not speculate beyond it.

Your job: from the structured OSINT payload provided by the user, identify the top threats currently visible in the data. For each threat:

- Be concrete. Reference specific events, regions, actors, or assets present in the data — do not invent.
- Severity must be one of CRITICAL / HIGH / MEDIUM / LOW and must be calibrated to potential loss of life, geopolitical escalation risk, or critical-infrastructure impact.
- Geographic focus must be a real region/country/feature from the data.
- Confidence reflects how strongly the data supports the assessment (0.0-1.0).
- "supportingSignals" must reference the actual feed names from the payload (e.g. "salvo.anchors", "militaryFlights", "internetOutages", "fires").

Rules:
- Surface 5-10 threats, ordered by severity then confidence.
- Do not editorialise. Do not recommend policy responses. Do not predict.
- If the data is thin, say so in `dataQuality` and keep the threats list short rather than padding.
- Output MUST conform exactly to the supplied JSON schema."""


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "headline": {
            "type": "string",
            "description": "One-sentence framing of the current threat picture.",
        },
        "dataQuality": {
            "type": "string",
            "enum": ["RICH", "ADEQUATE", "SPARSE"],
        },
        "threats": {
            "type": "array",
            "minItems": 0,
            "maxItems": 12,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                    },
                    "region": {"type": "string"},
                    "summary": {"type": "string"},
                    "confidence": {"type": "number"},
                    "supportingSignals": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "id",
                    "title",
                    "severity",
                    "region",
                    "summary",
                    "confidence",
                    "supportingSignals",
                ],
            },
        },
    },
    "required": ["headline", "dataQuality", "threats"],
}


class ThreatAnalyst(BaseAnalyst):
    name = "threat_analyst"
    model = DEFAULT_ANALYST_MODEL
    system_prompt = SYSTEM_PROMPT
    output_schema = SCHEMA
    max_tokens = 4096

    def build_user_message(self, raw_data: dict) -> str:
        import json
        compact = _compact_payload(raw_data)
        return (
            "Here is the latest aggregated OSINT swarm payload. "
            "Identify the top threats and respond per the schema.\n\n"
            f"```json\n{json.dumps(compact, default=str)[:60_000]}\n```"
        )


def _compact_payload(raw: dict) -> dict:
    """Reduce the raw swarm payload so we stay well inside Haiku's context window."""
    out: dict = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            out[key] = value
            continue
        slim: dict = {}
        for k, v in value.items():
            if isinstance(v, list):
                slim[k] = v[:25]  # cap any list to 25 entries
            elif isinstance(v, dict):
                slim[k] = {ik: iv for ik, iv in list(v.items())[:25]}
            else:
                slim[k] = v
        out[key] = slim
    return out
