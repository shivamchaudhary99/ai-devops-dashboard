import asyncio
from app.models import EventPayload, EventSource, Severity, ScoreBreakdown, ScoredEvent
from app.explainer import explain_event, explain_top_events


async def main():
    print("Testing Gen AI Explainer...")

    sample_event = ScoredEvent(
        id="evt-demo-01",
        source=EventSource.INFRA_MONITOR,
        title="CPU spike at 96.4% on payment-service (us-east-1)",
        severity=Severity.CRITICAL,
        region="us-east-1",
        service="payment-service",
        score=0.88,
        score_breakdown=ScoreBreakdown(
            severity=0.35,
            recency=0.24,
            frequency=0.15,
            blast_radius=0.14,
        ),
    )

    explanation = await explain_event(sample_event)
    print("\nGenerated Explanation:")
    print("-" * 50)
    print(explanation)
    print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
