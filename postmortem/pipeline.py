"""Orchestrates collectors and assembles the final Timeline."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from postmortem.collectors.git import GitCollector
from postmortem.collectors.hotspot import HotspotCollector
from postmortem.collectors.sentry import SentryCollector
from postmortem.models import EventKind, Timeline


def build_timeline(
    repo_path: str,
    since: datetime,
    sentry_token: str | None = None,
    sentry_org: str | None = None,
    sentry_project: str | None = None,
) -> Timeline:
    """
    Run all collectors against the repository and return a merged Timeline.

    Sentry credentials are optional — if absent (and not in env vars),
    the Sentry collector silently skips.
    """
    path = Path(repo_path).resolve()

    collectors = [
        GitCollector(repo_path=path, since=since),
        HotspotCollector(repo_path=path, since=since),
        SentryCollector(
            repo_path=path,
            since=since,
            token=sentry_token,
            org=sentry_org,
            project=sentry_project,
        ),
    ]

    timeline = Timeline(since=since)

    for collector in collectors:
        events = collector.collect()

        # HotspotCollector embeds HotspotFile objects in event meta —
        # pull them out so renderers can access them via timeline.hotspots
        for event in events:
            if event.kind == EventKind.HOTSPOT and "hotspots" in event.meta:
                timeline.hotspots = event.meta["hotspots"]

        timeline.events.extend(events)

    return timeline
