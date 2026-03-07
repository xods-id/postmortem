"""Sentry collector — surfaces errors that spiked during the incident window.

Setup (one-time):
    export SENTRY_TOKEN=sntrys_...     # Settings > API > Auth Tokens (read:issues)
    export SENTRY_ORG=my-org           # your org slug
    export SENTRY_PROJECT=my-project   # your project slug (optional, searches all if omitted)

postmortem will pick these up automatically, or you can pass them via CLI flags.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from postmortem.collectors import BaseCollector
from postmortem.models import Event, EventKind

_API_BASE = "https://sentry.io/api/0"
_MAX_ISSUES = 10


def _get(url: str, token: str) -> list | dict:
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"Sentry API {exc.code}: {body[:200]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cannot reach Sentry: {exc.reason}") from exc


def _fmt_ts(ts_str: str) -> datetime:
    """Parse Sentry's ISO-8601 timestamps (with or without microseconds)."""
    ts_str = ts_str.rstrip("Z").split(".")[0]
    return datetime.fromisoformat(ts_str).replace(tzinfo=UTC)


class SentryCollector(BaseCollector):
    """
    Fetches Sentry issues whose *last seen* time falls within the incident window.

    Requires:
        token    — Sentry auth token  (env: SENTRY_TOKEN)
        org      — organisation slug  (env: SENTRY_ORG)
        project  — project slug       (env: SENTRY_PROJECT, optional)
    """

    def __init__(
        self,
        repo_path: Path,
        since: datetime,
        token: str | None = None,
        org: str | None = None,
        project: str | None = None,
    ) -> None:
        super().__init__(repo_path=repo_path, since=since)
        self.token = token or os.environ.get("SENTRY_TOKEN", "")
        self.org = org or os.environ.get("SENTRY_ORG", "")
        self.project = project or os.environ.get("SENTRY_PROJECT", "")

    @property
    def _configured(self) -> bool:
        return bool(self.token and self.org)

    def collect(self) -> list[Event]:
        if not self._configured:
            return []   # silently skip if not configured — not an error

        try:
            return self._fetch_issues()
        except RuntimeError:
            return []   # network issues shouldn't break the whole report

    # ------------------------------------------------------------------

    def _fetch_issues(self) -> list[Event]:
        since_iso = self.since.strftime("%Y-%m-%dT%H:%M:%S")
        datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%S")

        if self.project:
            url = (
                f"{_API_BASE}/projects/{self.org}/{self.project}/issues/"
                f"?query=lastSeen%3A%3E{since_iso}&limit={_MAX_ISSUES}&sort=date"
            )
        else:
            url = (
                f"{_API_BASE}/organizations/{self.org}/issues/"
                f"?query=lastSeen%3A%3E{since_iso}&limit={_MAX_ISSUES}&sort=date"
            )

        raw = _get(url, self.token)
        if not isinstance(raw, list):
            return []

        events = []
        for issue in raw:
            try:
                last_seen = _fmt_ts(issue.get("lastSeen", ""))
            except (ValueError, AttributeError):
                continue

            if last_seen < self.since:
                continue

            title = issue.get("title", "Unknown error")
            culprit = issue.get("culprit", "")
            level = issue.get("level", "error")
            count = issue.get("count", "?")
            issue_id = issue.get("id", "")
            project_name = issue.get("project", {}).get("slug", self.project)
            url_link = issue.get("permalink", "")

            summary = f"[{level.upper()}] {title}"
            if culprit:
                summary += f" in {culprit}"

            events.append(
                Event(
                    timestamp=last_seen,
                    kind=EventKind.SENTRY,
                    summary=summary,
                    meta={
                        "count": count,
                        "level": level,
                        "culprit": culprit,
                        "project": project_name,
                        "issue_id": issue_id,
                        "url": url_link,
                        "title": title,
                    },
                )
            )

        return events
