from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.audit import AuditAction, audit_logger
from app.explainer import explain_top_events
from app.models import (
    AuditEntry,
    BriefingResponse,
    EventBatch,
    FeedbackRequest,
    RankingWeights,
    ScoredEvent,
)
from app.scoring import scoring_engine
from app.store import store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("GlanceApp 93 service starting")
    yield
    logger.info("GlanceApp 93 service stopped")


app = FastAPI(
    title="GlanceApp 93 — Gen AI + Ranking",
    description="Cloud briefings MVP: ingest events, rank by priority, explain with AI.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS setup for mobile/frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "module": "gen-ai-ranking",
        "events_stored": store.total_scored(),
    }


@app.post("/api/events/ingest", tags=["Ingestion"])
async def ingest_events(batch: EventBatch):
    ingested_ids = []

    for event in batch.events:
        store.add_raw_event(event)
        audit_logger.log(
            AuditAction.INGESTED,
            event_id=event.id,
            detail=f"source={event.source.value} severity={event.severity.value} title={event.title[:60]}",
        )

        scoring_engine.score_event(event)
        ingested_ids.append(event.id)

    logger.info("Ingested and scored %d events", len(batch.events))
    return {
        "message": f"Ingested {len(batch.events)} events",
        "event_ids": ingested_ids,
    }


@app.get("/api/briefings", response_model=BriefingResponse, tags=["Briefings"])
async def get_briefings(
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    explain_top: int = Query(10, ge=0, le=50, description="Generate AI explanations for top N"),
):
    ranked = store.get_ranked_events(limit=limit, offset=offset)

    if ranked and explain_top > 0:
        ranked = await explain_top_events(ranked, top_n=explain_top)

    audit_logger.log(
        AuditAction.SERVED,
        detail=f"Served {len(ranked)} briefings (offset={offset}, limit={limit})",
    )

    return BriefingResponse(
        briefings=ranked,
        total=store.total_scored(),
        weights=scoring_engine.weights,
    )


@app.get("/api/briefings/{event_id}", response_model=ScoredEvent, tags=["Briefings"])
async def get_briefing_detail(event_id: str):
    scored = store.get_scored_event(event_id)
    if not scored:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    if not scored.explanation:
        from app.explainer import explain_event
        scored.explanation = await explain_event(scored)

    return scored


@app.get("/api/audit", response_model=list[AuditEntry], tags=["Audit"])
async def get_audit_trail(
    limit: int = Query(100, ge=1, le=500, description="Max entries to return"),
    event_id: str | None = Query(None, description="Filter by event ID"),
):
    return audit_logger.get_entries(limit=limit, event_id=event_id)


@app.post("/api/feedback", response_model=RankingWeights, tags=["Feedback"])
async def submit_feedback(feedback: FeedbackRequest):
    new_weights = scoring_engine.update_weights(feedback)
    scoring_engine.score_all()
    logger.info("Weights updated and %d events re-scored", store.total_scored())
    return new_weights


@app.get("/api/weights", response_model=RankingWeights, tags=["Feedback"])
async def get_weights():
    return scoring_engine.weights
