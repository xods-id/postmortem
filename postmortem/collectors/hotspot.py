"""Hotspot collector — ranks files by change frequency and co-change coupling.

No external API needed. Pure git history analysis.

Risk scoring logic:
  - base score: how often the file changed vs the most-changed file (0-1)
  - coupling bonus: if the file consistently changes with others, it's a
    coordination risk (changes that touch many files at once are more likely
    to introduce bugs)
  - recency weight: changes in the last 25% of the window score higher
"""

from __future__ import annotations

import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from postmortem.collectors import BaseCollector
from postmortem.models import Event, EventKind, HotspotFile


_LOG_FORMAT = "%at|%H"
_SEP = "|"
_TOP_N = 10          # how many hotspot files to surface
_MIN_CHANGES = 2     # ignore files changed only once (noise)


def _run(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _since_flag(since: datetime) -> str:
    return since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class HotspotCollector(BaseCollector):
    """
    Analyses git history to surface risky files and their coupling.

    Produces:
      - Timeline.hotspots  (list[HotspotFile]) — ranked by risk score
      - A single HOTSPOT Event summarising the top finding, so it appears
        inline in the timeline at the correct timestamp.
    """

    def collect(self) -> list[Event]:
        try:
            commits = self._load_commits()
        except RuntimeError:
            return []

        if not commits:
            return []

        # Build: file -> list of (timestamp, sha) it appeared in
        file_appearances: dict[str, list[tuple[datetime, str]]] = defaultdict(list)
        # Build: (fileA, fileB) -> count of commits where both appeared
        pair_counts: Counter[tuple[str, str]] = Counter()

        for ts, sha, files in commits:
            for f in files:
                file_appearances[f].append((ts, sha))
            # co-change pairs (only consider commits touching <=20 files to
            # avoid massive refactors skewing the coupling matrix)
            if len(files) <= 20:
                sorted_files = sorted(files)
                for i, fa in enumerate(sorted_files):
                    for fb in sorted_files[i + 1:]:
                        pair_counts[(fa, fb)] += 1

        # Filter to files changed more than once
        active = {f: v for f, v in file_appearances.items() if len(v) >= _MIN_CHANGES}
        if not active:
            return []

        max_changes = max(len(v) for v in active.values())
        window_seconds = max(
            1,
            (datetime.now(tz=timezone.utc) - self.since).total_seconds()
        )
        recency_cutoff = datetime.now(tz=timezone.utc).timestamp() - window_seconds * 0.25

        hotspots: list[HotspotFile] = []
        for filepath, appearances in active.items():
            change_count = len(appearances)
            base_score = change_count / max_changes

            # Recency: proportion of changes in the last 25% of the window
            recent = sum(1 for ts, _ in appearances if ts.timestamp() >= recency_cutoff)
            recency_bonus = (recent / change_count) * 0.3

            # Coupling: top coupled files
            coupled: list[tuple[str, int]] = []
            for (fa, fb), count in pair_counts.items():
                if fa == filepath:
                    coupled.append((fb, count))
                elif fb == filepath:
                    coupled.append((fa, count))
            coupled.sort(key=lambda x: x[1], reverse=True)
            top_coupled = [f for f, _ in coupled[:3]]

            coupling_bonus = min(len(top_coupled) * 0.05, 0.15)
            risk_score = min(base_score + recency_bonus + coupling_bonus, 1.0)

            hotspots.append(
                HotspotFile(
                    path=filepath,
                    change_count=change_count,
                    coupled_files=top_coupled,
                    risk_score=round(risk_score, 3),
                )
            )

        hotspots.sort(key=lambda h: h.risk_score, reverse=True)
        hotspots = hotspots[:_TOP_N]

        # Attach to the timeline via the pipeline (returned via meta on the event)
        # The pipeline pulls hotspots out of the meta dict.
        if not hotspots:
            return []

        top = hotspots[0]
        summary = f"Hotspot: {top.path} changed {top.change_count}x (risk {top.risk_score:.0%})"

        event = Event(
            timestamp=self.since,   # pinned to window start so it sorts first
            kind=EventKind.HOTSPOT,
            summary=summary,
            meta={"hotspots": hotspots},
        )
        return [event]

    # ------------------------------------------------------------------

    def _load_commits(self) -> list[tuple[datetime, str, list[str]]]:
        raw = _run(
            ["git", "log", "--all",
             f"--pretty=format:{_LOG_FORMAT}",
             f"--after={_since_flag(self.since)}"],
            cwd=self.repo_path,
        )
        commits = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            parts = line.split(_SEP, maxsplit=1)
            if len(parts) < 2:
                continue
            ts_raw, sha = parts
            try:
                ts = datetime.fromtimestamp(int(ts_raw), tz=timezone.utc)
            except ValueError:
                continue
            files = self._files_for(sha)
            if files:
                commits.append((ts, sha, files))
        return commits

    def _files_for(self, sha: str) -> list[str]:
        try:
            raw = _run(
                ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", sha],
                cwd=self.repo_path,
            )
            return [f for f in raw.splitlines() if f]
        except RuntimeError:
            return []
