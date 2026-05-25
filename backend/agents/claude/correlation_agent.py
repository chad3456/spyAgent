"""
CorrelationAgent — finds cross-feed patterns the per-feed agents would miss.

E.g. "drone activity in region X coincides with internet outage in country Y"
or "military aircraft surge over Bab-el-Mandeb coincides with reported Houthi
salvo events".
"""

import json

from .base_analyst import BaseAnalyst, DEFAULT_ANALYST_MODEL


SYSTEM_PROMPT = """You are a cross-domain pattern analyst on a national-security OSINT desk.

The user gives you a structured payload aggregated from multiple independent feeds: live flights, military aircraft, satellites, vessels, submarines, salvo events, drone incidents, fires, internet outages, conflict events, etc.

Your job: identify pattern correlations across two or more feeds that a single-feed analyst would miss. Examples of the kind of correlation to look for (not an exhaustive list):

- Spike in military air activity over a region coincident with a salvo anchor/event in the same region.
- Internet outage in a country coincident with reported political conflict events.
- Submarine base in country X plus surge in naval news mentions for the same fleet.
- Drone hotspot activity coincident with active fires (possible attack vs accident discrimination).
- Cross-border tension signals: military flights of A near borders of B + drone events in B + outage reports in B.

Rules:
- Each correlation must cite at least two distinct feeds from the payload.
- Reference real items in the data, not invented examples.
- Strength is your confidence the correlation is meaningful, not coincidental (0.0-1.0).
- Surface 3-8 correlations. Quality over quantity.
- Output MUST conform exactly to the supplied JSON schema."""


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "headline": {"type": "string"},
        "correlations": {
            "type": "array",
            "minItems": 0,
            "maxItems": 10,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "feeds": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                    },
                    "region": {"type": "string"},
                    "summary": {"type": "string"},
                    "strength": {"type": "number"},
                    "implication": {"type": "string"},
                },
                "required": [
                    "id",
                    "title",
                    "feeds",
                    "region",
                    "summary",
                    "strength",
                    "implication",
                ],
            },
        },
    },
    "required": ["headline", "correlations"],
}


class CorrelationAgent(BaseAnalyst):
    name = "correlation_agent"
    model = DEFAULT_ANALYST_MODEL
    system_prompt = SYSTEM_PROMPT
    output_schema = SCHEMA
    max_tokens = 4096

    def build_user_message(self, raw_data: dict) -> str:
        from .threat_analyst import _compact_payload
        compact = _compact_payload(raw_data)
        return (
            "Aggregated multi-feed OSINT payload. Surface cross-feed correlations "
            "per the schema.\n\n"
            f"```json\n{json.dumps(compact, default=str)[:60_000]}\n```"
        )
