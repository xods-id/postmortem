"""Git collector — extracts commits, merges, tags, and branches from git log."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from postmortem.collectors import BaseCollector
from postmortem.models import Event, EventKind

# git log format: <unix-timestamp>|<sha>|<author>|<subject>
_LOG_FORMAT = "%at|%H|%an|%s"
_SEP = "|"


def _run(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git command failed: {' '.join(args)}\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def _classify(subject: str) -> EventKind:
    lower = subject.lower()
    if lower.startswith("merge"):
        return EventKind.MERGE
    return EventKind.COMMIT


def _since_flag(since: datetime) -> str:
    """Return ISO-8601 string git understands."""
    return since.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class GitCollector(BaseCollector):
    """Collects commits and tags from a local git repository."""

    def collect(self) -> list[Event]:
        self._assert_git_repo()
        events: list[Event] = []
        events.extend(self._collect_commits())
        events.extend(self._collect_tags())
        return events

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _assert_git_repo(self) -> None:
        try:
            _run(["git", "rev-parse", "--git-dir"], cwd=self.repo_path)
        except RuntimeError as exc:
            raise RuntimeError(
                f"'{self.repo_path}' does not appear to be a git repository."
            ) from exc

    def _collect_commits(self) -> list[Event]:
        raw = _run(
            [
                "git",
                "log",
                "--all",
                f"--pretty=format:{_LOG_FORMAT}",
                f"--after={_since_flag(self.since)}",
            ],
            cwd=self.repo_path,
        )
        events = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            parts = line.split(_SEP, maxsplit=3)
            if len(parts) < 4:
                continue
            ts_raw, sha, author, subject = parts
            try:
                ts = datetime.fromtimestamp(int(ts_raw), tz=UTC)
            except ValueError:
                continue

            # gather changed files for this commit
            files = self._changed_files(sha)

            events.append(
                Event(
                    timestamp=ts,
                    kind=_classify(subject),
                    summary=subject,
                    author=author,
                    sha=sha,
                    meta={"files": files, "file_count": len(files)},
                )
            )
        return events

    def _collect_tags(self) -> list[Event]:
        """Collect annotated and lightweight tags within the window."""
        try:
            raw = _run(
                ["git", "tag", "--sort=-creatordate", "--format=%(creatordate:unix)|%(refname:short)|%(subject)"],
                cwd=self.repo_path,
            )
        except RuntimeError:
            return []

        events = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            parts = line.split(_SEP, maxsplit=2)
            if len(parts) < 2:
                continue
            ts_raw, tag_name = parts[0], parts[1]
            subject = parts[2] if len(parts) > 2 else ""
            try:
                ts = datetime.fromtimestamp(int(ts_raw), tz=UTC)
            except ValueError:
                continue
            if ts < self.since:
                continue
            events.append(
                Event(
                    timestamp=ts,
                    kind=EventKind.TAG,
                    summary=f"Tagged {tag_name}" + (f": {subject}" if subject else ""),
                    sha="",
                    meta={"tag": tag_name},
                )
            )
        return events

    def _changed_files(self, sha: str) -> list[str]:
        try:
            raw = _run(
                ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", sha],
                cwd=self.repo_path,
            )
            return [f for f in raw.splitlines() if f]
        except RuntimeError:
            return []
