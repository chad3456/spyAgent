"""
RegionalSynth — per-country brief built from feed filtering. Same shape as
RegionalAnalyst (Claude).
"""
from __future__ import annotations


from .base_synth import BaseSynth, in_country, severity_score


COUNTRY_PROFILES: dict[str, dict] = {
    "US": {"name": "United States", "code": "US"},
    "RU": {"name": "Russian Federation", "code": "RU"},
    "CN": {"name": "People's Republic of China", "code": "CN"},
    "IN": {"name": "Republic of India", "code": "IN"},
    "IR": {"name": "Islamic Republic of Iran", "code": "IR"},
}

# Country-name fragments used to flag "this country is mentioned" in salvo/news titles.
COUNTRY_KEYWORDS: dict[str, list[str]] = {
    "US": ["united states", "u.s.", "us military", "us navy", "us air force", "centcom", "pentagon"],
    "RU": ["russia", "russian", "moscow", "kremlin", "putin"],
    "CN": ["china", "chinese", "beijing", "pla", "plan ", "taiwan strait"],
    "IN": ["india", "indian", "new delhi", "iaf", "kashmir"],
    "IR": ["iran", "iranian", "tehran", "irgc", "houthi", "hezbollah"],
}


class RegionalSynth(BaseSynth):
    def __init__(self, country_code: str):
        super().__init__()
        if country_code not in COUNTRY_PROFILES:
            raise ValueError(country_code)
        self.country_code = country_code
        self.country = COUNTRY_PROFILES[country_code]
        self.name = f"regional_synth:{country_code}"

    def synthesise(self, raw: dict) -> dict:
        cc = self.country_code
        kw = COUNTRY_KEYWORDS[cc]
        country_name = self.country["name"]

        own_activity: list[str] = []
        threats_against: list[str] = []
        internal_signals: list[str] = []
        key_assets: list[str] = []
        escalation_weight = 0

        # ── Own military air activity ───────────────────────────────────────
        mil = raw.get("militaryFlights", {}) or {}
        own_mil = [
            a for a in (mil.get("aircraft") or [])
            if (a.get("country", "") or "").upper().startswith(cc)
            or (a.get("nation", "") or "").upper().startswith(cc)
        ]
        if own_mil:
            own_activity.append(
                f"{len(own_mil)} military aircraft attributed to {cc} currently tracked via ADS-B."
            )
            for a in own_mil[:5]:
                cs = (a.get("callsign") or "").strip()
                if cs:
                    key_assets.append(f"callsign {cs} ({a.get('type') or 'mil'})")
            escalation_weight += min(40, len(own_mil) * 2)

        # ── Own submarine bases (always present, low signal) ────────────────
        subs = raw.get("submarines", {}) or {}
        own_bases = [b for b in (subs.get("bases") or []) if b.get("country") == cc]
        if own_bases:
            ssbn = sum(1 for b in own_bases if b.get("type") == "SSBN")
            own_activity.append(
                f"{len(own_bases)} known submarine bases on national territory "
                f"({ssbn} SSBN-class)."
            )
            for b in own_bases[:4]:
                key_assets.append(f"{b.get('name')} ({b.get('type')}, {b.get('fleet')})")

        # ── Salvo anchors involving this country ────────────────────────────
        salvo = raw.get("salvo", {}) or {}
        for a in salvo.get("anchors", []) or []:
            origin_name = (a.get("origin", {}) or {}).get("name", "").lower()
            target_name = (a.get("target", {}) or {}).get("name", "").lower()
            actor = (a.get("actor", "") or "").lower()
            origin_match = any(k in origin_name for k in kw) or any(k in actor for k in kw)
            target_match = any(k in target_name for k in kw)
            if origin_match:
                own_activity.append(
                    f"Documented salvo: {a.get('name', '')} — {a.get('munitions', '')}"
                )
                escalation_weight += severity_score(a.get("severity", "HIGH"))
            if target_match:
                threats_against.append(
                    f"Targeted in: {a.get('name', '')} ({a.get('actor', 'unknown actor')})"
                )
                escalation_weight += severity_score(a.get("severity", "HIGH"))

        # ── Live salvo events mentioning country ────────────────────────────
        for e in (salvo.get("events") or [])[:20]:
            title = (e.get("title", "") or "").lower()
            if any(k in title for k in kw):
                snippet = e.get("title", "")[:120]
                threats_against.append(f"Live report: {snippet}")
                escalation_weight += severity_score(e.get("severity", "MEDIUM")) // 2
            if len(threats_against) >= 8:
                break

        # ── Drone incidents in country ──────────────────────────────────────
        drones = raw.get("drones", {}) or {}
        for i in (drones.get("incidents") or [])[:20]:
            if in_country(i.get("lat", 0), i.get("lon", 0), cc):
                threats_against.append(f"Drone incident: {i.get('title', '')[:100]}")
                escalation_weight += severity_score(i.get("severity", "MEDIUM")) // 3
            if len(threats_against) >= 12:
                break

        # ── Internal signals: fires, outages, protests ──────────────────────
        fires = raw.get("fires", {}) or {}
        own_fires = [f for f in (fires.get("fires") or []) if in_country(f.get("lat", 0), f.get("lon", 0), cc)]
        if own_fires:
            critical = sum(1 for f in own_fires if f.get("severity") == "CRITICAL")
            internal_signals.append(
                f"{len(own_fires)} active fire detections inside national territory "
                f"({critical} CRITICAL)."
            )
            escalation_weight += min(15, critical * 3)

        outages = raw.get("internetOutages", {}) or {}
        own_outages = [
            o for o in (outages.get("outages") or [])
            if (o.get("countryCode") or "").upper() == cc
        ]
        if own_outages:
            internal_signals.append(
                f"{len(own_outages)} internet outage report(s) attributed to {cc}: "
                + "; ".join(o.get("title", "")[:60] for o in own_outages[:3])
            )
            escalation_weight += 8 * len(own_outages)

        protests = raw.get("protests", {}) or {}
        protest_events = [
            e for e in (protests.get("events") or [])
            if (e.get("countryCode") or "").upper() == cc
            or any(k in (e.get("country", "") or "").lower() for k in kw)
        ]
        if protest_events:
            internal_signals.append(
                f"{len(protest_events)} protest/unrest event(s) in {cc} (GDELT/ACLED)."
            )
            escalation_weight += min(20, len(protest_events))

        # ── CCTV / public cameras by country (situational awareness) ────────
        cctv = raw.get("cctv", {}) or {}
        own_cams = [c for c in (cctv.get("cameras") or []) if c.get("country") == cc]
        if own_cams:
            key_assets.append(f"{len(own_cams)} public webcam feeds in {cc}")

        # ── Satellites passing over (best-effort) ───────────────────────────
        sats = raw.get("satellites", {}) or {}
        sat_overhead = [
            s for s in (sats.get("satellites") or [])[:60]
            if in_country(s.get("lat", 0), s.get("lon", 0), cc)
        ]
        if sat_overhead:
            interesting = [s for s in sat_overhead if (s.get("category") or "").lower() in ("military", "earth observation")][:3]
            for s in interesting:
                key_assets.append(f"satellite {s.get('name')} ({s.get('category')}) overhead")

        # ── Escalation ──────────────────────────────────────────────────────
        if escalation_weight >= 200:
            escalation = "CRITICAL"
        elif escalation_weight >= 100:
            escalation = "HIGH"
        elif escalation_weight >= 40:
            escalation = "MEDIUM"
        elif escalation_weight >= 10:
            escalation = "LOW"
        else:
            escalation = "BASELINE"

        # Trim and de-dupe
        def _dedupe_trim(items: list[str], n: int) -> list[str]:
            seen: set[str] = set()
            out: list[str] = []
            for it in items:
                if it not in seen:
                    seen.add(it)
                    out.append(it)
                if len(out) >= n:
                    break
            return out

        own_activity = _dedupe_trim(own_activity, 6)
        threats_against = _dedupe_trim(threats_against, 8)
        internal_signals = _dedupe_trim(internal_signals, 5)
        key_assets = _dedupe_trim(key_assets, 8)

        # Headline
        if escalation in ("CRITICAL", "HIGH"):
            headline = f"{country_name} posture: {escalation} — multiple threat and activity signals active."
        elif own_activity or threats_against:
            headline = f"{country_name} posture: {escalation} — limited but tracked activity."
        else:
            headline = f"{country_name} posture: {escalation} — nothing remarkable in current data."

        return self.envelope({
            "country": country_name,
            "headline": headline,
            "ownActivity": own_activity,
            "threatsAgainst": threats_against,
            "internalSignals": internal_signals,
            "escalationRisk": escalation,
            "keyAssetsObserved": key_assets,
        })
