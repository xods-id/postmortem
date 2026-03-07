"""Abstract base class for all event collectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from postmortem.models import Event


class BaseCollector(ABC):
    """
    Contract every collector must satisfy.

    A collector is responsible for producing zero or more Events from a
    single data source (git log, CI API, log files, etc.).
    """

    def __init__(self, repo_path: Path, since: datetime) -> None:
        self.repo_path = repo_path
        self.since = since

    @abstractmethod
    def collect(self) -> list[Event]:
        """Return events from this data source since *self.since*."""
