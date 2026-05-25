"""
RegionalAnalyst — per-country intelligence brief for US / RU / CN / IN / IR.

One instance is parameterised by country; `analyse(raw_data)` returns a brief
focused on signals relevant to that country (own military movements, threats
against it, internal stability, infra).
"""

import json

from .base_analyst import BaseAnalyst, DEFAULT_ANALYST_MODEL


COUNTRY_PROFILES: dict[str, dict] = {
    "US": {"name": "United States", "code": "US", "iso2": "US"},
    "RU": {"name": "Russian Federation", "code": "RU", "iso2": "RU"},
    "CN": {"name": "People's Republic of China", "code": "CN", "iso2": "CN"},
    "IN": {"name": "Republic of India", "code": "IN", "iso2": "IN"},
    "IR": {"name": "Islamic Republic of Iran", "code": "IR", "iso2": "IR"},
}


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "country": {"type": "string"},
        "headline": {"type": "string"},
        "ownActivity": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Notable military / state / asset activity originating from this country.",
        },
        "threatsAgainst": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Threats targeting this country in the current data.",
        },
        "internalSignals": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Internal stability signals: outages, protests, fires, health, infra.",
        },
        "escalationRisk": {
            "type": "string",
            "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "BASELINE"],
        },
        "keyAssetsObserved": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific aircraft, bases, satellites, vessels, etc. observed in the data.",
        },
    },
    "required": [
        "country",
        "headline",
        "ownActivity",
        "threatsAgainst",
        "internalSignals",
        "escalationRisk",
        "keyAssetsObserved",
    ],
}


def _system_prompt_for(country_name: str) -> str:
    return f"""You are a regional intelligence analyst on a national-security desk, briefing on the {country_name}.

Your job: from the structured OSINT payload provided by the user, write a focused brief on {country_name}. The brief covers:

- ownActivity        — what is {country_name} itself doing in the data (military aircraft, naval bases, satellites, drone ops, salvo launches)?
- threatsAgainst      — what threats target {country_name} in the data?
- internalSignals     — internal stability (internet outages, fires, protests, health, infra) inside {country_name}?
- escalationRisk      — current escalation posture, one of CRITICAL / HIGH / MEDIUM / LOW / BASELINE.
- keyAssetsObserved   — concrete assets named in the data (specific callsigns, base names, NORAD IDs, port names).

Rules:
- Reference only items present in the payload. No external knowledge, no speculation.
- Use ISO/standard names where possible.
- If a section has no relevant data, return an empty array rather than padding.
- Output MUST conform exactly to the supplied JSON schema."""


class RegionalAnalyst(BaseAnalyst):
    model = DEFAULT_ANALYST_MODEL
    output_schema = SCHEMA
    max_tokens = 3072

    def __init__(self, country_code: str):
        super().__init__()
        if country_code not in COUNTRY_PROFILES:
            raise ValueError(f"Unsupported country code: {country_code}")
        self.country_code = country_code
        self.country = COUNTRY_PROFILES[country_code]
        self.name = f"regional_analyst:{country_code}"
        self.system_prompt = _system_prompt_for(self.country["name"])

    def build_user_message(self, raw_data: dict) -> str:
        from .threat_analyst import _compact_payload
        compact = _compact_payload(raw_data)
        return (
            f"Country focus: {self.country['name']} ({self.country['code']}).\n\n"
            "Aggregated OSINT swarm payload:\n\n"
            f"```json\n{json.dumps(compact, default=str)[:55_000]}\n```\n\n"
            "Produce the regional brief per the schema."
        )
