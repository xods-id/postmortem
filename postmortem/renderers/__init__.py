"""Abstract base class for all output renderers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from postmortem.models import Timeline


class BaseRenderer(ABC):
    """Contract every renderer must satisfy."""

    def __init__(self, since: datetime, repo_path: str) -> None:
        self.since = since
        self.repo_path = Path(repo_path).resolve()

    @abstractmethod
    def render(self, timeline: Timeline) -> str:
        """Convert *timeline* to a display string."""
