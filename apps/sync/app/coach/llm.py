"""Anthropic Sonnet wrapper for the optional closing line. Fail-soft."""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Eres el coach personal de Alberto. Tono ejecutivo, directo, sin paja.
Genera 0-2 frases en español como cierre de un briefing nocturno.

Reglas duras:
- 0 frases si todo está verde y no hay nada accionable.
- 1 frase si hay un detalle accionable.
- 2 frases si el cuerpo está en ámbar/rojo: nombra el problema y propón el ajuste concreto.
- NO usar "considera", "tal vez", "puedes". Imperativo o descriptivo.
- NO repetir números que ya están en el briefing arriba.
- NO motivacional. NO emoji.
- Jerga técnica EN sin traducir cuando aplique (TSB, HRV, Z1, threshold).

Devuelve SOLO el texto del cierre, sin comillas, sin prefijos.\
"""


def _build_user_prompt(ctx: dict) -> str:
    return (
        f"Semáforo: {ctx['semaphore']}\n"
        f"HRV: {ctx['hrv']} (Δ {ctx['delta']} vs 7d)\n"
        f"Sueño: {ctx['sleep_h']}h ({ctx['sleep_eff']}%)\n"
        f"TSB: {ctx['tsb']}\n"
        f"Hoy: {ctx['today_workout_summary']}\n"
        f"Mañana: {ctx['tomorrow_workout_summary']}\n"
        f"Recs: cena {ctx['kcal']}kcal · {ctx['c']}/{ctx['p']}/{ctx['g']} · bed {ctx['bed']}\n\n"
        "Cierre:\n"
    )


def compose_closing_line(ctx: dict, *, timeout_s: float = 5.0) -> str | None:
    """Call Anthropic Sonnet 4 for a 0-2 sentence closing line.

    Returns the trimmed string, or None on any failure (network, timeout,
    empty response, missing API key, SDK not installed).
    """
    if os.environ.get("COACH_LLM_ENABLED", "true").lower() in ("false", "0", "no"):
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.info("coach.llm: ANTHROPIC_API_KEY missing, skipping closing line")
        return None

    try:
        import anthropic  # type: ignore

        client = anthropic.Anthropic(api_key=api_key, timeout=timeout_s)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=80,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_prompt(ctx)}],
        )
        parts = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        out = "".join(parts).strip()
        return out or None
    except Exception as exc:
        logger.warning("coach.llm: closing-line generation failed: %s", exc)
        return None
