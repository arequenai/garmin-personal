"""ntfy.sh push helper. Best-effort; returns the response status code or None."""
from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

NTFY_BASE = "https://ntfy.sh"


def _emoji_tag(semaphore: str) -> str:
    return {
        "green": "green_circle",
        "amber": "yellow_circle",
        "red": "red_circle",
    }.get(semaphore, "white_circle")


def push(
    *,
    body: str,
    semaphore: str,
    topic: str | None = None,
    timeout_s: float = 5.0,
) -> int | None:
    topic = topic if topic is not None else os.environ.get("COACH_NTFY_TOPIC", "")
    if not topic:
        logger.warning("coach.ntfy: no topic configured, skipping push")
        return None
    try:
        resp = httpx.post(
            f"{NTFY_BASE}/{topic}",
            content=body.encode("utf-8"),
            headers={
                "Title": "Briefing 20:30",
                "Tags": _emoji_tag(semaphore),
                "Priority": "3",
            },
            timeout=timeout_s,
        )
        return int(resp.status_code)
    except Exception as exc:
        logger.warning("coach.ntfy: push failed: %s", exc)
        return None
