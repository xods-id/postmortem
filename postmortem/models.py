"""Domain models for postmortem timeline events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class EventKind(StrEnum):
    COMMIT = "commit"
    MERGE = "merge"
    TAG = "tag"
    FILE_CHANGE = "file_change"
    BRANCH = "branch"
    SENTRY = "sentry"
    HOTSPOT = "hotspot"


@dataclass(frozen=True, order=True)
class Event:
    """A single timestamped event in the incident timeline."""

    timestamp: datetime
    kind: EventKind
    summary: str
    author: str = ""
    sha: str = ""
    meta: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    @property
    def short_sha(self) -> str:
        return self.sha[:7] if self.sha else ""


@dataclass
class HotspotFile:
    """A file ranked by change frequency and co-change coupling."""
    path: str
    change_count: int          # times changed in window
    coupled_files: list[str]   # files most often changed together
    risk_score: float          # 0.0 – 1.0, higher = riskier


@dataclass
class Timeline:
    """Ordered collection of events covering an incident window."""

    since: datetime
    events: list[Event] = field(default_factory=list)
    hotspots: list[HotspotFile] = field(default_factory=list)

    def sorted_events(self) -> list[Event]:
        return sorted(self.events)

    def filter_by_kind(self, *kinds: EventKind) -> list[Event]:
        return [e for e in self.sorted_events() if e.kind in kinds]

    @property
    def authors(self) -> list[str]:
        seen: set[str] = set()
        result = []
        for e in self.sorted_events():
            if e.author and e.author not in seen:
                seen.add(e.author)
                result.append(e.author)
        return result

    @property
    def is_empty(self) -> bool:
        return len(self.events) == 0
