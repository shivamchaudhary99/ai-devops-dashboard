from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from app.audit import AuditAction, audit_logger
from app.models import ScoredEvent

load_dotenv()

logger = logging.getLogger(__name__)

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")
HF_TIMEOUT = 20.0

_hf_client: Optional[InferenceClient] = None
_explanation_cache: dict[str, str] = {}


def _get_hf_client() -> Optional[InferenceClient]:
    global _hf_client
    if _hf_client is None and HF_API_TOKEN:
        _hf_client = InferenceClient(token=HF_API_TOKEN, timeout=HF_TIMEOUT)
    return _hf_client


def _cache_key(event: ScoredEvent) -> str:
    raw = f"{event.id}:{event.score}:{event.title}"
    return hashlib.md5(raw.encode()).hexdigest()


def _build_messages(event: ScoredEvent) -> list[dict]:
    bd = event.score_breakdown
    user_content = (
        f"Cloud event details:\n"
        f"  Title: {event.title}\n"
        f"  Source: {event.source.value}\n"
        f"  Severity: {event.severity.value}\n"
        f"  Region: {event.region or 'N/A'}\n"
        f"  Service: {event.service or 'N/A'}\n"
        f"  Score: {event.score:.2f} "
        f"(severity={bd.severity:.2f}, recency={bd.recency:.2f}, "
        f"frequency={bd.frequency:.2f}, blast_radius={bd.blast_radius:.2f})\n\n"
        f"Write a concise 1-2 sentence explanation of why this event matters "
        f"and what action the operator should consider."
    )
    return [
        {
            "role": "system",
            "content": "You are a concise SRE assistant for a cloud operations team. "
                       "Respond with exactly 1-2 sentences. No bullet points, no headers.",
        },
        {"role": "user", "content": user_content},
    ]


def _template_explanation(event: ScoredEvent) -> str:
    severity_label = event.severity.value.upper()
    region_part = f" in {event.region}" if event.region else ""
    service_part = f" affecting {event.service}" if event.service else ""

    if event.score >= 0.75:
        urgency = "Requires immediate attention"
    elif event.score >= 0.50:
        urgency = "Should be investigated soon"
    else:
        urgency = "Monitor for escalation"

    return (
        f"{severity_label} priority: {event.title}{region_part}{service_part}. "
        f"Scored {event.score:.2f} — {urgency}."
    )


async def _call_hf_api(event: ScoredEvent) -> Optional[str]:
    client = _get_hf_client()
    if not client:
        logger.warning("HF_API_TOKEN not set, using template fallback")
        return None

    messages = _build_messages(event)

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat_completion(
                messages=messages,
                model=HF_MODEL,
                max_tokens=120,
                temperature=0.5,
            ),
        )

        text = response.choices[0].message.content.strip()
        if text:
            logger.info("HF returned explanation for %s", event.id)
            return text

        return None

    except Exception:
        logger.exception("Failed to fetch explanation from HF for %s", event.id)
        return None


async def explain_event(event: ScoredEvent) -> str:
    key = _cache_key(event)
    if key in _explanation_cache:
        return _explanation_cache[key]

    explanation = await _call_hf_api(event)
    if not explanation:
        explanation = _template_explanation(event)

    _explanation_cache[key] = explanation
    return explanation


async def explain_top_events(
    events: list[ScoredEvent],
    top_n: int = 10,
) -> list[ScoredEvent]:
    top_events = events[:top_n]

    # Run explanations in parallel for top ranked items
    tasks = [explain_event(ev) for ev in top_events]
    explanations = await asyncio.gather(*tasks)

    for ev, expl in zip(top_events, explanations):
        ev.explanation = expl
        audit_logger.log(
            AuditAction.EXPLAINED,
            event_id=ev.id,
            detail=f"explanation={expl[:80]}...",
        )

    # Fallback template for remainder
    for ev in events[top_n:]:
        if not ev.explanation:
            ev.explanation = _template_explanation(ev)

    return events
