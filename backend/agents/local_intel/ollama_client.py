"""
Optional Ollama integration. If the user has Ollama running on localhost:11434
the briefing prose gets polished by their local model. Everything is fully
functional WITHOUT Ollama — this is pure enhancement.

Auto-detected on each request (cached for 60s); no config required if Ollama
is on the default port. Override via:
  - OLLAMA_HOST  (default http://localhost:11434)
  - OLLAMA_MODEL (default llama3.2:3b — pick whatever you've pulled)
"""
from __future__ import annotations


import os
import time
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def _host() -> str:
    return os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def _model() -> str:
    return os.environ.get("OLLAMA_MODEL", "llama3.2:3b")


_availability_cache: dict[str, tuple[float, bool]] = {}


def ollama_available() -> bool:
    """True iff Ollama is reachable and has the configured model pulled."""
    key = f"{_host()}::{_model()}"
    now = time.time()
    cached = _availability_cache.get(key)
    if cached and (now - cached[0]) < 60:
        return cached[1]

    try:
        with httpx.Client(timeout=2.0) as client:
            r = client.get(f"{_host()}/api/tags")
            if r.status_code != 200:
                _availability_cache[key] = (now, False)
                return False
            models = [m.get("name", "") for m in (r.json().get("models") or [])]
            # Match exact name or prefix (e.g. "llama3.2" matches "llama3.2:3b")
            wanted = _model()
            available = any(m == wanted or m.startswith(wanted.split(":")[0]) for m in models)
            _availability_cache[key] = (now, available)
            return available
    except Exception:
        _availability_cache[key] = (now, False)
        return False


async def polish_with_ollama(prompt: str, timeout: float = 20.0) -> Optional[str]:
    """
    Send a prompt to Ollama's /api/generate. Returns the response text, or None
    if Ollama is unreachable or returns an error. Never raises.
    """
    if not ollama_available():
        return None

    payload = {
        "model": _model(),
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 400,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{_host()}/api/generate", json=payload)
            if r.status_code != 200:
                logger.info("Ollama returned HTTP %s", r.status_code)
                return None
            data = r.json()
            text = (data.get("response") or "").strip()
            return text or None
    except Exception as exc:
        logger.info("Ollama call failed: %s", exc)
        return None
