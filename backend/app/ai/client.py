"""OpenAI client accessor. Returns None when no API key is configured."""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger("sentinel.ai")


def get_client():
    """Return an OpenAI client, or ``None`` if AI is not configured/available."""
    if not settings.ai_enabled:
        return None
    try:
        from openai import OpenAI

        return OpenAI(api_key=settings.openai_api_key)
    except Exception:  # noqa: BLE001 - openai not installed or import failure
        logger.warning("OpenAI client unavailable; using template fallback.")
        return None
