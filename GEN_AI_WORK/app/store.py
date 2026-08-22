from __future__ import annotations

import threading
from collections import defaultdict
from datetime import datetime, timezone

from app.models import EventPayload, ScoredEvent


class EventStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._raw_events: dict[str, EventPayload] = {}
        self._scored_events: dict[str, ScoredEvent] = {}
        self._source_index: dict[str, list[str]] = defaultdict(list)
        self._service_counts: dict[str, int] = defaultdict(int)
        self._region_counts: dict[str, int] = defaultdict(int)

    def add_raw_event(self, event: EventPayload) -> None:
        with self._lock:
            self._raw_events[event.id] = event
            self._source_index[event.source.value].append(event.id)
            if event.service:
                self._service_counts[event.service] += 1
            if event.region:
                self._region_counts[event.region] += 1

    def upsert_scored_event(self, scored: ScoredEvent) -> None:
        with self._lock:
            self._scored_events[scored.id] = scored

    def get_raw_event(self, event_id: str) -> EventPayload | None:
        return self._raw_events.get(event_id)

    def get_scored_event(self, event_id: str) -> ScoredEvent | None:
        return self._scored_events.get(event_id)

    def get_all_raw_events(self) -> list[EventPayload]:
        return list(self._raw_events.values())

    def get_ranked_events(self, limit: int = 50, offset: int = 0) -> list[ScoredEvent]:
        sorted_events = sorted(
            self._scored_events.values(),
            key=lambda e: e.score,
            reverse=True,
        )
        for idx, ev in enumerate(sorted_events):
            ev.rank = idx + 1
        return sorted_events[offset : offset + limit]

    def total_scored(self) -> int:
        return len(self._scored_events)

    def count_similar_recent(
        self,
        event: EventPayload,
        window_minutes: int = 5,
    ) -> int:
        now = datetime.now(timezone.utc)
        count = 0
        for eid in self._source_index.get(event.source.value, []):
            other = self._raw_events.get(eid)
            if other and other.id != event.id:
                age = (now - other.timestamp).total_seconds() / 60
                if age <= window_minutes and other.severity == event.severity:
                    count += 1
        return count

    def affected_services_count(self, event: EventPayload) -> int:
        services = set()
        for eid in self._source_index.get(event.source.value, []):
            other = self._raw_events.get(eid)
            if other and other.service:
                services.add(other.service)
        return max(len(services), 1)

    def affected_regions_count(self, event: EventPayload) -> int:
        regions = set()
        for eid in self._source_index.get(event.source.value, []):
            other = self._raw_events.get(eid)
            if other and other.region:
                regions.add(other.region)
        return max(len(regions), 1)

    def clear(self) -> None:
        with self._lock:
            self._raw_events.clear()
            self._scored_events.clear()
            self._source_index.clear()
            self._service_counts.clear()
            self._region_counts.clear()


store = EventStore()
