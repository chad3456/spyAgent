"""
BriefingSynth — executive summary built from ThreatSynth + CorrelationSynth +
RegionalSynth output. Optional Ollama polish on the bottom-line prose.
"""
from __future__ import annotations


import asyncio

from .base_synth import BaseSynth, severity_score
from .ollama_client import ollama_available, polish_with_ollama


class BriefingSynth(BaseSynth):
    name = "briefing_synth"

    async def synthesise_async(self, analyst_outputs: dict) -> dict:
        threats = (analyst_outputs.get("threats") or {}) or {}
        correlations = (analyst_outputs.get("correlations") or {}) or {}
        regional = analyst_outputs.get("regional") or {}

        threat_items = threats.get("threats", []) or []
        correlation_items = correlations.get("correlations", []) or []

        # ── Top threats (3-5) ───────────────────────────────────────────────
        top_threats = []
        for t in threat_items[:5]:
            top_threats.append({
                "title": t.get("title", ""),
                "severity": t.get("severity", "MEDIUM"),
                "rationale": t.get("summary", "")[:200],
            })

        # ── Regional snapshots ──────────────────────────────────────────────
        regional_snapshots = []
        for cc, brief in regional.items():
            if not brief:
                continue
            regional_snapshots.append({
                "country": brief.get("country", cc),
                "posture": brief.get("escalationRisk", "BASELINE"),
                "oneLine": brief.get("headline", f"{cc} — no data."),
            })
        regional_snapshots.sort(key=lambda r: severity_score(r["posture"]), reverse=True)

        # ── Key correlations ────────────────────────────────────────────────
        key_correlations = []
        for c in correlation_items[:4]:
            key_correlations.append({
                "title": c.get("title", ""),
                "feeds": c.get("feeds", []),
                "implication": c.get("implication", "")[:240],
            })

        # ── Watch items ─────────────────────────────────────────────────────
        watch_items: list[str] = []
        for t in threat_items[:6]:
            if severity_score(t.get("severity", "")) >= 60:
                watch_items.append(
                    f"{t['title']} — {t.get('region', 'global')} (confidence {t.get('confidence', 0):.0%})"
                )
        for r in regional_snapshots:
            if r["posture"] in ("CRITICAL", "HIGH"):
                watch_items.append(f"{r['country']}: posture {r['posture']}")
            if len(watch_items) >= 5:
                break
        watch_items = watch_items[:6]

        # ── Confidence ──────────────────────────────────────────────────────
        data_quality = threats.get("dataQuality", "ADEQUATE")
        if data_quality == "RICH" and len(threat_items) >= 5:
            confidence = "HIGH"
        elif data_quality == "SPARSE" or len(threat_items) < 2:
            confidence = "LOW"
        else:
            confidence = "MEDIUM"

        # ── Bottom line — deterministic prose, optionally Ollama-polished ──
        bottom_line = _compose_bottom_line(top_threats, regional_snapshots, key_correlations)
        polish_model = "local-heuristic-v1"

        if ollama_available():
            polished = await polish_with_ollama(
                "You are a national-security briefing editor. Rewrite the supplied "
                "bottom-line paragraph to be sharper and more direct — 2 to 4 sentences, "
                "calibrated language, no flourishes, no recommendations. Return ONLY "
                "the rewritten paragraph, no preamble.\n\n"
                f"Draft:\n{bottom_line}"
            )
            if polished:
                bottom_line = polished
                polish_model = "ollama+local-heuristic"

        analysis = {
            "bottomLine": bottom_line,
            "topThreats": top_threats,
            "regionalSnapshots": regional_snapshots,
            "keyCorrelations": key_correlations,
            "watchItems": watch_items,
            "confidence": confidence,
        }
        return self.envelope(analysis, model=polish_model)

    def synthesise(self, raw: dict) -> dict:
        # Sync entrypoint for `BaseSynth.synthesise` contract.
        return asyncio.run(self.synthesise_async(raw))


def _compose_bottom_line(
    top_threats: list[dict],
    regional_snapshots: list[dict],
    key_correlations: list[dict],
) -> str:
    if not top_threats:
        return (
            "Quiet operational picture. No CRITICAL or HIGH threats in current OSINT "
            "swarm output; regional postures at baseline."
        )

    critical = [t for t in top_threats if t["severity"] == "CRITICAL"]
    high = [t for t in top_threats if t["severity"] == "HIGH"]
    hot_countries = [r for r in regional_snapshots if r["posture"] in ("CRITICAL", "HIGH")]

    sentences: list[str] = []

    if critical:
        sentences.append(
            f"{len(critical)} CRITICAL threat(s) active, led by: {critical[0]['title']}."
        )
    elif high:
        sentences.append(
            f"{len(high)} HIGH-severity threat(s) active; no CRITICAL items in current data."
        )

    if hot_countries:
        # Use short country names (US, Russia, China, India, Iran) for tighter prose.
        short_names = {
            "United States": "US",
            "Russian Federation": "Russia",
            "People's Republic of China": "China",
            "Republic of India": "India",
            "Islamic Republic of Iran": "Iran",
        }
        names = ", ".join(short_names.get(r["country"], r["country"]) for r in hot_countries[:3])
        postures = "/".join(r["posture"] for r in hot_countries[:3])
        sentences.append(f"Elevated regional posture: {names} ({postures}).")

    if key_correlations:
        sentences.append(
            f"{len(key_correlations)} cross-feed correlation(s) detected — top pattern: "
            f"{key_correlations[0]['title']}."
        )

    if not sentences:
        sentences.append(f"{len(top_threats)} threat(s) at MEDIUM severity or below being tracked.")

    return " ".join(sentences)
