from __future__ import annotations

import threading
from typing import Optional

from app.models import AuditAction, AuditEntry


class AuditLogger:
    def __init__(self, max_entries: int = 5000) -> None:
        self._lock = threading.Lock()
        self._entries: list[AuditEntry] = []
        self._max_entries = max_entries

    def log(
        self,
        action: AuditAction,
        event_id: Optional[str] = None,
        detail: str = "",
    ) -> AuditEntry:
        entry = AuditEntry(action=action, event_id=event_id, detail=detail)
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-self._max_entries:]
        return entry

    def get_entries(
        self,
        limit: int = 100,
        event_id: Optional[str] = None,
    ) -> list[AuditEntry]:
        with self._lock:
            entries = self._entries[:]
        if event_id:
            entries = [e for e in entries if e.event_id == event_id]
        return list(reversed(entries))[:limit]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


audit_logger = AuditLogger()
