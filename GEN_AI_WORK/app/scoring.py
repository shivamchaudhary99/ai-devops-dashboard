from __future__ import annotations

import math
import threading
from datetime import datetime, timezone

from app.audit import AuditAction, audit_logger
from app.models import (
    EventPayload,
    FeedbackRequest,
    RankingWeights,
    ScoreBreakdown,
    Severity,
    ScoredEvent,
)
from app.store import store

SEVERITY_SCORES: dict[Severity, float] = {
    Severity.CRITICAL: 1.0,
    Severity.HIGH: 0.75,
    Severity.MEDIUM: 0.5,
    Severity.LOW: 0.25,
}

RECENCY_LAMBDA = 0.05


class ScoringEngine:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._weights = RankingWeights()

    @property
    def weights(self) -> RankingWeights:
        with self._lock:
            return self._weights.model_copy()

    def update_weights(self, feedback: FeedbackRequest) -> RankingWeights:
        total = feedback.severity + feedback.recency + feedback.frequency + feedback.blast_radius
        if total == 0:
            total = 1.0
        with self._lock:
            self._weights = RankingWeights(
                severity=round(feedback.severity / total, 4),
                recency=round(feedback.recency / total, 4),
                frequency=round(feedback.frequency / total, 4),
                blast_radius=round(feedback.blast_radius / total, 4),
            )
            new_w = self._weights.model_copy()

        audit_logger.log(
            AuditAction.WEIGHTS_UPDATED,
            detail=f"New weights: sev={new_w.severity}, rec={new_w.recency}, "
                   f"freq={new_w.frequency}, blast={new_w.blast_radius}",
        )
        return new_w

    @staticmethod
    def _severity_score(event: EventPayload) -> float:
        return SEVERITY_SCORES.get(event.severity, 0.5)

    @staticmethod
    def _recency_score(event: EventPayload) -> float:
        now = datetime.now(timezone.utc)
        age_minutes = max((now - event.timestamp).total_seconds() / 60, 0)
        return math.exp(-RECENCY_LAMBDA * age_minutes)

    @staticmethod
    def _frequency_score(event: EventPayload, max_freq: int = 20) -> float:
        count = store.count_similar_recent(event, window_minutes=5)
        return min(count / max_freq, 1.0)

    @staticmethod
    def _blast_radius_score(event: EventPayload, max_blast: int = 10) -> float:
        services = store.affected_services_count(event)
        regions = store.affected_regions_count(event)
        blast = services + regions
        return min(blast / max_blast, 1.0)

    def score_event(self, event: EventPayload) -> ScoredEvent:
        w = self.weights

        sev = self._severity_score(event)
        rec = self._recency_score(event)
        freq = self._frequency_score(event)
        blast = self._blast_radius_score(event)

        breakdown = ScoreBreakdown(
            severity=round(sev * w.severity, 4),
            recency=round(rec * w.recency, 4),
            frequency=round(freq * w.frequency, 4),
            blast_radius=round(blast * w.blast_radius, 4),
        )

        total_score = round(
            breakdown.severity + breakdown.recency + breakdown.frequency + breakdown.blast_radius,
            4,
        )

        scored = ScoredEvent(
            id=event.id,
            source=event.source,
            title=event.title,
            severity=event.severity,
            timestamp=event.timestamp,
            region=event.region,
            service=event.service,
            metadata=event.metadata,
            score=total_score,
            score_breakdown=breakdown,
        )

        store.upsert_scored_event(scored)
        audit_logger.log(
            AuditAction.SCORED,
            event_id=event.id,
            detail=f"score={total_score} | sev={breakdown.severity} rec={breakdown.recency} "
                   f"freq={breakdown.frequency} blast={breakdown.blast_radius}",
        )

        return scored

    def score_all(self) -> list[ScoredEvent]:
        events = store.get_all_raw_events()
        scored = [self.score_event(e) for e in events]
        scored.sort(key=lambda s: s.score, reverse=True)
        for idx, s in enumerate(scored):
            s.rank = idx + 1
        return scored


scoring_engine = ScoringEngine()
