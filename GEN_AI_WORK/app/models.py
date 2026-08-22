from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EventSource(str, Enum):
    INFRA_MONITOR = "infra-monitor"
    DEPLOY_PIPELINE = "deploy-pipeline"
    ERROR_TRACKER = "error-tracker"


class EventPayload(BaseModel):
    id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    source: EventSource
    title: str
    severity: Severity = Severity.MEDIUM
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    region: Optional[str] = None
    service: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventBatch(BaseModel):
    events: list[EventPayload]


class ScoreBreakdown(BaseModel):
    severity: float = 0.0
    recency: float = 0.0
    frequency: float = 0.0
    blast_radius: float = 0.0


class ScoredEvent(BaseModel):
    id: str
    source: EventSource
    title: str
    severity: Severity
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    region: Optional[str] = None
    service: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    explanation: str = ""
    rank: int = 0


class RankingWeights(BaseModel):
    severity: float = 0.35
    recency: float = 0.25
    frequency: float = 0.20
    blast_radius: float = 0.20


class BriefingResponse(BaseModel):
    briefings: list[ScoredEvent]
    total: int
    weights: RankingWeights
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeedbackRequest(BaseModel):
    severity: float = 0.35
    recency: float = 0.25
    frequency: float = 0.20
    blast_radius: float = 0.20


class AuditAction(str, Enum):
    INGESTED = "ingested"
    SCORED = "scored"
    EXPLAINED = "explained"
    SERVED = "served"
    WEIGHTS_UPDATED = "weights_updated"


class AuditEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: Optional[str] = None
    action: AuditAction
    detail: str = ""
