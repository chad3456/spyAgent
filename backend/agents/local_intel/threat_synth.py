"""
ThreatSynth — extracts ranked threats from the raw swarm payload using
deterministic rules. Output shape matches ThreatAnalyst (Claude).
"""
from __future__ import annotations


import hashlib

from .base_synth import BaseSynth, severity_score


def _id(prefix: str, *parts) -> str:
    h = hashlib.sha1(":".join(str(p) for p in parts).encode()).hexdigest()[:10]
    return f"{prefix}-{h}"


class ThreatSynth(BaseSynth):
    name = "threat_synth"

    def synthesise(self, raw: dict) -> dict:
        threats: list[dict] = []

        # ── 1. Salvo anchors (documented exchanges) ─────────────────────────
        salvo = raw.get("salvo", {}) or {}
        for a in (salvo.get("anchors") or [])[:8]:
            threats.append({
                "id": _id("salvo-anchor", a.get("id", "")),
                "title": a.get("name", "Documented salvo exchange"),
                "severity": (a.get("severity") or "HIGH").upper(),
                "region": f"{a.get('origin', {}).get('name', '?')} → {a.get('target', {}).get('name', '?')}",
                "summary": (
                    f"{a.get('actor', 'Unknown actor')}: {a.get('munitions', 'munitions not specified')}. "
                    f"Status: {'mostly intercepted' if a.get('intercepted') else 'impact reported'}."
                ),
                "confidence": 0.95,
                "supportingSignals": ["salvo.anchors"],
            })

        # ── 2. Live salvo events ─────────────────────────────────────────────
        for e in (salvo.get("events") or [])[:6]:
            sev = (e.get("severity") or "MEDIUM").upper()
            if severity_score(sev) < 30:
                continue
            threats.append({
                "id": _id("salvo-event", e.get("id", "")),
                "title": e.get("title", "Salvo activity reported")[:120],
                "severity": sev,
                "region": e.get("region", "unknown"),
                "summary": f"Reported via {e.get('source', 'OSINT')}; {e.get('publishedAt', '')}.",
                "confidence": 0.6 if sev == "HIGH" else 0.45,
                "supportingSignals": ["salvo.events"],
            })

        # ── 3. Critical fires (FRP > 200 MW) ─────────────────────────────────
        fires = raw.get("fires", {}) or {}
        fires_summary = fires.get("summary", {}) or {}
        if fires_summary.get("critical", 0) >= 3:
            top = sorted(fires.get("fires", []) or [], key=lambda f: f.get("frp", 0), reverse=True)[:1]
            top_f = top[0] if top else {}
            threats.append({
                "id": _id("fires", fires_summary.get("source", ""), fires_summary.get("critical", 0)),
                "title": f"Active wildfire crisis — {fires_summary.get('critical', 0)} CRITICAL detections",
                "severity": "HIGH",
                "region": f"global ({fires_summary.get('source', 'NASA FIRMS')})",
                "summary": (
                    f"{fires_summary.get('total', 0)} total active fires in last 24h; "
                    f"hottest {top_f.get('frp', '?')} MW at {top_f.get('lat', '?')}, {top_f.get('lon', '?')}."
                    if top_f else
                    f"{fires_summary.get('total', 0)} total active fires reported in last 24h."
                ),
                "confidence": 0.85,
                "supportingSignals": ["fires", "fires.summary"],
            })

        # ── 4. Internet outages — active disruption ─────────────────────────
        outages = raw.get("internetOutages", {}) or {}
        out_summary = outages.get("summary", {}) or {}
        if out_summary.get("active", 0) >= 1 or out_summary.get("total", 0) >= 5:
            active = [
                o for o in (outages.get("outages") or [])
                if o.get("type") == "active" or (o.get("severity") in ("CRITICAL", "HIGH"))
            ][:3]
            sample = "; ".join(
                f"{o.get('country') or o.get('countryCode') or '?'} ({o.get('source', '')})"
                for o in active
            ) or "multiple regions"
            threats.append({
                "id": _id("outage", out_summary.get("active", 0), out_summary.get("total", 0)),
                "title": f"Internet connectivity disruptions — {out_summary.get('active', 0)} active reports",
                "severity": "HIGH" if out_summary.get("active", 0) >= 2 else "MEDIUM",
                "region": sample,
                "summary": (
                    f"{out_summary.get('total', 0)} reports across "
                    f"{out_summary.get('countries', 0)} countries. Sources: "
                    f"{', '.join(outages.get('sources', []) or ['GDELT'])}."
                ),
                "confidence": 0.7,
                "supportingSignals": ["internetOutages", "internetOutages.summary"],
            })

        # ── 5. Earthquakes — CRITICAL only ──────────────────────────────────
        eq = raw.get("earthquakes", {}) or {}
        eq_events = [e for e in (eq.get("events") or []) if (e.get("severity") or "").upper() == "CRITICAL"][:3]
        for e in eq_events:
            threats.append({
                "id": _id("eq", e.get("id", "")),
                "title": f"M{e.get('magnitude', '?')} earthquake — {e.get('place', 'unknown')}",
                "severity": "CRITICAL",
                "region": e.get("place", "unknown"),
                "summary": (
                    f"USGS reports M{e.get('magnitude')} at depth {e.get('depth')} km. "
                    f"Tsunami flag: {'yes' if e.get('tsunami') else 'no'}."
                ),
                "confidence": 0.95,
                "supportingSignals": ["earthquakes"],
            })

        # ── 6. Military air activity surge ──────────────────────────────────
        mil = raw.get("militaryFlights", {}) or {}
        mil_aircraft = mil.get("aircraft") or []
        if len(mil_aircraft) >= 20:
            # Aggregate by reporting country
            by_country: dict[str, int] = {}
            for a in mil_aircraft:
                cc = (a.get("country") or "").strip() or "unknown"
                by_country[cc] = by_country.get(cc, 0) + 1
            top_country, top_count = max(by_country.items(), key=lambda kv: kv[1])
            threats.append({
                "id": _id("mil", len(mil_aircraft), top_country),
                "title": f"Elevated military air activity — {len(mil_aircraft)} aircraft tracked",
                "severity": "HIGH" if len(mil_aircraft) >= 40 else "MEDIUM",
                "region": f"{top_country} ({top_count} aircraft) + {len(by_country) - 1} other origins",
                "summary": (
                    f"ADS-B / OpenSky picked up {len(mil_aircraft)} military callsigns "
                    f"across {len(by_country)} reporting origins."
                ),
                "confidence": 0.65,
                "supportingSignals": ["militaryFlights"],
            })

        # ── 7. Drone incidents in hotspots ──────────────────────────────────
        drones = raw.get("drones", {}) or {}
        drone_high = [i for i in (drones.get("incidents") or []) if (i.get("severity") or "").upper() == "HIGH"][:4]
        if len(drone_high) >= 2:
            regions = list({d.get("region", "unknown") for d in drone_high})
            threats.append({
                "id": _id("drone", len(drone_high), regions[0] if regions else ""),
                "title": f"Drone activity surge — {len(drone_high)} HIGH-severity incidents",
                "severity": "HIGH",
                "region": ", ".join(regions[:3]),
                "summary": (
                    f"{len(drone_high)} drone-related incidents flagged HIGH across "
                    f"{len(regions)} active hotspots."
                ),
                "confidence": 0.6,
                "supportingSignals": ["drones", "drones.incidents"],
            })

        # ── 8. Conflict events (HAPI / ACLED) ───────────────────────────────
        protests = raw.get("protests", {}) or {}
        hapi = raw.get("hapiEvents", {}) or {}
        protest_count = len(protests.get("events", []) or [])
        hapi_count = len(hapi.get("conflictEvents", []) or [])
        if protest_count + hapi_count >= 50:
            threats.append({
                "id": _id("conflict", protest_count, hapi_count),
                "title": f"Elevated unrest signal — {protest_count + hapi_count} events",
                "severity": "MEDIUM",
                "region": "global",
                "summary": (
                    f"GDELT/ACLED: {protest_count} protests, HAPI/OCHA: {hapi_count} conflict events."
                ),
                "confidence": 0.55,
                "supportingSignals": ["protests", "hapiEvents"],
            })

        # ── Rank & cap ───────────────────────────────────────────────────────
        threats.sort(
            key=lambda t: (severity_score(t["severity"]), t.get("confidence", 0)),
            reverse=True,
        )
        threats = threats[:12]

        # Data quality assessment
        feed_count = sum(
            1 for f in ("salvo", "fires", "internetOutages", "militaryFlights",
                        "drones", "earthquakes", "satellites", "protests", "hapiEvents")
            if raw.get(f) and not (isinstance(raw.get(f), dict) and raw[f].get("error"))
        )
        data_quality = "RICH" if feed_count >= 7 else "ADEQUATE" if feed_count >= 4 else "SPARSE"

        headline = self._headline(threats, data_quality)

        return self.envelope({
            "headline": headline,
            "dataQuality": data_quality,
            "threats": threats,
        })

    @staticmethod
    def _headline(threats: list[dict], data_quality: str) -> str:
        if not threats:
            return f"Threat surface quiet. Data quality: {data_quality.lower()}."
        critical = sum(1 for t in threats if t["severity"] == "CRITICAL")
        high = sum(1 for t in threats if t["severity"] == "HIGH")
        if critical:
            return (
                f"{critical} CRITICAL and {high} HIGH threats active; "
                f"top item: {threats[0]['title'][:90]}."
            )
        if high:
            return f"{high} HIGH-severity threats active; no CRITICAL items in current data."
        return f"{len(threats)} threats tracked at MEDIUM or below. No CRITICAL items."
