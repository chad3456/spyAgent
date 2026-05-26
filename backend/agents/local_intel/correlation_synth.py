"""
CorrelationSynth — finds cross-feed patterns via geo proximity + simple
content overlap. Output shape matches CorrelationAgent (Claude).
"""
from __future__ import annotations


import hashlib

from .base_synth import BaseSynth, haversine_km


def _id(prefix: str, *parts) -> str:
    h = hashlib.sha1(":".join(str(p) for p in parts).encode()).hexdigest()[:10]
    return f"{prefix}-{h}"


PROXIMITY_KM = 800.0  # threshold for "in the same theatre"


class CorrelationSynth(BaseSynth):
    name = "correlation_synth"

    def synthesise(self, raw: dict) -> dict:
        correlations: list[dict] = []

        # ── 1. Military flights ↔ salvo events (same theatre) ───────────────
        mil = (raw.get("militaryFlights", {}) or {}).get("aircraft") or []
        salvo_events = (raw.get("salvo", {}) or {}).get("events") or []
        for ev in salvo_events[:10]:
            if not ev.get("lat") and not ev.get("lon"):
                continue
            nearby = [
                a for a in mil
                if a.get("lat") is not None and a.get("lon") is not None
                and haversine_km(ev["lat"], ev["lon"], a["lat"], a["lon"]) < PROXIMITY_KM
            ]
            if len(nearby) >= 3:
                correlations.append({
                    "id": _id("mil-salvo", ev.get("id", "")),
                    "title": f"Military air activity coincides with salvo reporting near {ev.get('region', 'theatre')}",
                    "feeds": ["militaryFlights", "salvo.events"],
                    "region": ev.get("region", "unknown"),
                    "summary": (
                        f"{len(nearby)} military aircraft tracked within {PROXIMITY_KM:.0f} km "
                        f"of salvo report '{ev.get('title', '')[:80]}'."
                    ),
                    "strength": min(0.95, 0.5 + 0.05 * len(nearby)),
                    "implication": (
                        "Combined air-tracking + salvo signal raises confidence the reported "
                        "exchange is real rather than rumour."
                    ),
                })
            if len(correlations) >= 8:
                break

        # ── 2. Drone hotspots ↔ active fires (FPV vs accident discriminator) ─
        hotspots = (raw.get("drones", {}) or {}).get("hotspots") or []
        fires = (raw.get("fires", {}) or {}).get("fires") or []
        for hs in hotspots:
            nearby_fires = [
                f for f in fires
                if haversine_km(hs["lat"], hs["lon"], f["lat"], f["lon"]) < 300.0
            ]
            if len(nearby_fires) >= 5:
                correlations.append({
                    "id": _id("drone-fire", hs.get("name", "")),
                    "title": f"Drone hotspot overlaps with active fires — {hs.get('name', 'unknown')}",
                    "feeds": ["drones.hotspots", "fires"],
                    "region": hs.get("name", "unknown"),
                    "summary": (
                        f"{len(nearby_fires)} FIRMS fire detections within 300 km of "
                        f"drone hotspot '{hs.get('name')}' (tag: {hs.get('tag', 'n/a')})."
                    ),
                    "strength": min(0.85, 0.4 + 0.05 * len(nearby_fires)),
                    "implication": (
                        "Drone activity in a region with active fires warrants discriminating "
                        "kinetic strikes from accidental ignition."
                    ),
                })
            if len(correlations) >= 10:
                break

        # ── 3. Internet outages ↔ political conflict (same country) ─────────
        outages = (raw.get("internetOutages", {}) or {}).get("outages") or []
        protest_events = (raw.get("protests", {}) or {}).get("events") or []
        hapi_events = (raw.get("hapiEvents", {}) or {}).get("conflictEvents") or []
        outage_cc = {o.get("countryCode", "").upper(): o for o in outages if o.get("countryCode")}
        conflict_by_cc: dict[str, int] = {}
        for e in protest_events + hapi_events:
            cc = (e.get("countryCode") or e.get("country_code") or "").upper()
            if not cc and (country := e.get("country")):
                # Try to infer from country name — best effort
                cc = country[:2].upper() if len(country) >= 2 else ""
            if cc:
                conflict_by_cc[cc] = conflict_by_cc.get(cc, 0) + 1

        for cc, outage in outage_cc.items():
            if conflict_by_cc.get(cc, 0) >= 3:
                correlations.append({
                    "id": _id("outage-conflict", cc),
                    "title": f"Internet outage in {cc} coincides with elevated conflict events",
                    "feeds": ["internetOutages", "protests", "hapiEvents"],
                    "region": cc,
                    "summary": (
                        f"{conflict_by_cc[cc]} conflict/protest events in {cc} reported alongside "
                        f"outage flagged by {outage.get('source', 'OSINT')}."
                    ),
                    "strength": 0.75,
                    "implication": (
                        "Outage during civil unrest is a strong indicator of deliberate "
                        "connectivity restriction by a state actor."
                    ),
                })
            if len(correlations) >= 10:
                break

        # ── 4. Submarine bases ↔ submarine sightings news ───────────────────
        subs = raw.get("submarines", {}) or {}
        bases = subs.get("bases") or []
        sightings = subs.get("sightings") or []
        if len(sightings) >= 5 and len(bases) >= 3:
            # Look for base-country mentions in sighting titles
            base_countries = {b.get("country", "").upper() for b in bases if b.get("country")}
            hits = 0
            matched_countries: set[str] = set()
            for s in sightings:
                title_upper = (s.get("title", "") or "").upper()
                for cc in base_countries:
                    # naive country-code/name match
                    if cc in title_upper:
                        hits += 1
                        matched_countries.add(cc)
                        break
            if hits >= 3:
                correlations.append({
                    "id": _id("sub-news", hits),
                    "title": f"Submarine OSINT activity — {hits} news items reference base-host countries",
                    "feeds": ["submarines.bases", "submarines.sightings"],
                    "region": ", ".join(sorted(matched_countries)),
                    "summary": (
                        f"{hits} of {len(sightings)} OSINT submarine news items mention "
                        f"countries that host known submarine bases."
                    ),
                    "strength": 0.55,
                    "implication": (
                        "Concentrated reporting on home-base countries may indicate observed "
                        "deployment cycle activity (departures, port returns, exercises)."
                    ),
                })

        # ── 5. Iran/US salvo anchors ↔ drone hotspot in same theatre ────────
        anchors = (raw.get("salvo", {}) or {}).get("anchors") or []
        for a in anchors:
            origin = a.get("origin", {}) or {}
            target = a.get("target", {}) or {}
            if not origin.get("lat") or not target.get("lat"):
                continue
            mid_lat = (origin["lat"] + target["lat"]) / 2
            mid_lon = (origin["lon"] + target["lon"]) / 2
            nearby_drones = [
                hs for hs in hotspots
                if haversine_km(mid_lat, mid_lon, hs["lat"], hs["lon"]) < 1200.0
            ]
            if nearby_drones:
                correlations.append({
                    "id": _id("salvo-drone", a.get("id", "")),
                    "title": f"Salvo corridor '{a.get('name', '')[:60]}' overlaps drone hotspot",
                    "feeds": ["salvo.anchors", "drones.hotspots"],
                    "region": f"{origin.get('name', '?')} → {target.get('name', '?')}",
                    "summary": (
                        f"Documented {a.get('actor', 'actor')} salvo corridor passes within 1200 km of "
                        f"{len(nearby_drones)} active drone hotspot(s)."
                    ),
                    "strength": 0.7,
                    "implication": (
                        "Drone and missile vectors share the same battlespace; expect compound "
                        "saturation tactics in any future exchange."
                    ),
                })
            if len(correlations) >= 10:
                break

        correlations.sort(key=lambda c: c["strength"], reverse=True)
        correlations = correlations[:10]

        headline = (
            f"{len(correlations)} cross-feed correlation(s) detected via geo + temporal overlap."
            if correlations else
            "No significant cross-feed correlations detected in current data."
        )
        return self.envelope({
            "headline": headline,
            "correlations": correlations,
        })
