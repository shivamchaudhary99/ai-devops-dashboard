from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

from app.models import EventPayload, EventSource, Severity

REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1", "eu-central-1"]
SERVICES = [
    "api-gateway", "auth-service", "billing-service", "notification-service",
    "search-service", "user-service", "order-service", "payment-service",
    "analytics-service", "cdn-edge",
]


def _random_ts(max_age_minutes: int = 30) -> datetime:
    offset = random.randint(0, max_age_minutes * 60)
    return datetime.now(timezone.utc) - timedelta(seconds=offset)


def _random_severity(weights: tuple[float, ...] = (0.10, 0.25, 0.40, 0.25)) -> Severity:
    return random.choices(list(Severity), weights=weights, k=1)[0]


def generate_infra_alert() -> EventPayload:
    region = random.choice(REGIONS)
    service = random.choice(SERVICES)
    metric = random.choice(["CPU", "Memory", "Disk I/O", "Network latency"])
    value = round(random.uniform(50, 99), 1)
    severity = (
        Severity.CRITICAL if value > 90
        else Severity.HIGH if value > 80
        else Severity.MEDIUM if value > 65
        else Severity.LOW
    )

    return EventPayload(
        id=f"evt-{uuid.uuid4().hex[:8]}",
        source=EventSource.INFRA_MONITOR,
        title=f"{metric} spike at {value}% on {service} ({region})",
        severity=severity,
        timestamp=_random_ts(15),
        region=region,
        service=service,
        metadata={
            "metric": metric.lower().replace(" ", "_"),
            "value_percent": value,
            "threshold": 80.0,
            "host": f"{service}-{random.randint(1, 5)}.{region}.internal",
        },
    )


def generate_deploy_event() -> EventPayload:
    service = random.choice(SERVICES)
    version = f"v{random.randint(1, 5)}.{random.randint(0, 20)}.{random.randint(0, 99)}"
    status = random.choice(["started", "succeeded", "failed", "rolling_back"])
    severity = (
        Severity.CRITICAL if status == "rolling_back"
        else Severity.HIGH if status == "failed"
        else Severity.LOW
    )
    region = random.choice(REGIONS)

    return EventPayload(
        id=f"evt-{uuid.uuid4().hex[:8]}",
        source=EventSource.DEPLOY_PIPELINE,
        title=f"Deploy {version} of {service} — {status}",
        severity=severity,
        timestamp=_random_ts(20),
        region=region,
        service=service,
        metadata={
            "version": version,
            "status": status,
            "rollback_available": status in ("failed", "rolling_back"),
            "deployer": random.choice(["ci-bot", "dev-team", "hotfix-pipeline"]),
        },
    )


def generate_app_error() -> EventPayload:
    service = random.choice(SERVICES)
    error_type = random.choice([
        "NullPointerException", "TimeoutError", "ConnectionRefused",
        "HTTP 502 Bad Gateway", "HTTP 503 Service Unavailable",
        "OutOfMemoryError", "RateLimitExceeded", "DatabaseDeadlock",
    ])
    count = random.randint(1, 500)
    severity = (
        Severity.CRITICAL if count > 200
        else Severity.HIGH if count > 100
        else Severity.MEDIUM if count > 30
        else Severity.LOW
    )
    endpoint = random.choice(["/api/users", "/api/orders", "/api/search", "/api/payments", "/api/auth", "/health"])
    region = random.choice(REGIONS)

    return EventPayload(
        id=f"evt-{uuid.uuid4().hex[:8]}",
        source=EventSource.ERROR_TRACKER,
        title=f"{error_type} on {service}{endpoint} ({count} occurrences)",
        severity=severity,
        timestamp=_random_ts(10),
        region=region,
        service=service,
        metadata={
            "error_type": error_type,
            "count": count,
            "endpoint": endpoint,
            "stack_trace_hash": uuid.uuid4().hex[:12],
        },
    )


GENERATORS = [generate_infra_alert, generate_deploy_event, generate_app_error]


def generate_event_batch(batch_size: int = 15) -> list[EventPayload]:
    events = []
    for _ in range(batch_size):
        gen = random.choice(GENERATORS)
        events.append(gen())
    return events
