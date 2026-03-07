"""Rich terminal renderer for postmortem timelines."""

from __future__ import annotations

from datetime import UTC, datetime
from io import StringIO

from postmortem.models import EventKind, HotspotFile, Timeline
from postmortem.renderers import BaseRenderer

# Split multiple statements into separate lines to fix ruff E702
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_MAGENTA = "\033[35m"
_BLUE = "\033[34m"
_WHITE = "\033[97m"
_ORANGE = "\033[38;5;208m"

_KIND_STYLE: dict[EventKind, tuple[str, str]] = {
    EventKind.COMMIT:      ("●", _GREEN),
    EventKind.MERGE:       ("⇄", _BLUE),
    EventKind.TAG:         ("◆", _YELLOW),
    EventKind.BRANCH:      ("⎇", _MAGENTA),
    EventKind.FILE_CHANGE: ("~", _CYAN),
    EventKind.SENTRY:      ("⚠", _RED),
    EventKind.HOTSPOT:     ("🔥", _ORANGE),
}

_RISK_COLOUR = {
    (0.0, 0.3): _GREEN,
    (0.3, 0.6): _YELLOW,
    (0.6, 0.8): _ORANGE,
    (0.8, 1.1): _RED,
}


def _risk_colour(score: float) -> str:
    for (lo, hi), colour in _RISK_COLOUR.items():
        if lo <= score < hi:
            return colour
    return _RED


class TerminalRenderer(BaseRenderer):
    def __init__(self, since: datetime, repo_path: str, color: bool = True) -> None:
        super().__init__(since=since, repo_path=repo_path)
        self.color = color

    def render(self, timeline: Timeline) -> str:
        buf = StringIO()
        self._write_header(buf, timeline)
        if timeline.hotspots:
            self._write_hotspots(buf, timeline.hotspots)
        if timeline.is_empty:
            buf.write(
                self._c(
                    _DIM,
                    f"  No events found in the last {self._fmt_window()}.\n\n",
                )
            )
        else:
            self._write_events(buf, timeline)
        self._write_summary(buf, timeline)
        return buf.getvalue()

    def _c(self, code: str, text: str) -> str:
        return f"{code}{text}{_RESET}" if self.color else text

    def _write_header(self, buf: StringIO, timeline: Timeline) -> None:
        now = datetime.now(tz=UTC).astimezone()
        buf.write("\n")
        buf.write(self._c(_BOLD + _WHITE, "─" * 72) + "\n")
        buf.write(self._c(_BOLD + _WHITE, f"  🔍  postmortem  ·  {self.repo_path.name}") + "\n")
        buf.write(self._c(_DIM, f"  Since {self._fmt_window()}  ·  {now.strftime('%H:%M:%S %Z')}") + "\n")
        buf.write(self._c(_BOLD + _WHITE, "─" * 72) + "\n\n")

    def _write_hotspots(self, buf: StringIO, hotspots: list[HotspotFile]) -> None:
        buf.write(self._c(_BOLD + _ORANGE, "  🔥  File Hotspots\n\n"))
        for h in hotspots[:5]:
            colour = _risk_colour(h.risk_score)
            risk = f"{h.risk_score:.0%}"
            bar = self._c(colour, "■■■"[:max(1, int(h.risk_score * 3))] + "□□□"[max(1, int(h.risk_score * 3)):])
            path = self._c(_WHITE, h.path)
            meta = self._c(_DIM, f"changed {h.change_count}x  risk {risk}")
            buf.write(f"  {bar}  {path}  {meta}\n")
            if h.coupled_files:
                coupled = "  ".join(self._c(_DIM, f) for f in h.coupled_files)
                buf.write(self._c(_DIM, f"       coupled: {coupled}\n"))
        buf.write("\n")

    def _write_events(self, buf: StringIO, timeline: Timeline) -> None:
        events = [e for e in timeline.sorted_events() if e.kind != EventKind.HOTSPOT]
        current_date: str | None = None
        for event in events:
            date_str = event.timestamp.astimezone().strftime("%a %d %b %Y")
            if date_str != current_date:
                current_date = date_str
                buf.write(self._c(_BOLD + _CYAN, f"  ── {date_str} ──\n\n"))

            icon, colour = _KIND_STYLE.get(event.kind, ("•", _WHITE))
            ts = self._c(_DIM, event.timestamp.astimezone().strftime("%H:%M:%S"))
            badge = self._c(colour, icon)
            summ = self._c(_WHITE, event.summary)
            sha = self._c(_DIM, f"[{event.short_sha}]") if event.short_sha else ""
            auth = self._c(_DIM, f"  ← {event.author}") if event.author else ""
            buf.write(f"  {ts}  {badge}  {summ}  {sha}{auth}\n")

            # Sentry: show occurrence count
            if event.kind == EventKind.SENTRY:
                count = event.meta.get("count", "")
                proj = event.meta.get("project", "")
                if count or proj:
                    buf.write(self._c(_DIM, f"              {proj}  ·  {count} occurrences\n"))

            # Commits: show changed files
            files: list[str] = event.meta.get("files", [])
            if files and event.kind in (EventKind.COMMIT, EventKind.MERGE):
                for f in files[:5]:
                    buf.write(self._c(_DIM, f"              ↳ {f}\n"))
                if len(files) > 5:
                    buf.write(self._c(_DIM, f"              ↳ … and {len(files) - 5} more\n"))

            buf.write("\n")

    def _write_summary(self, buf: StringIO, timeline: Timeline) -> None:
        events = [e for e in timeline.sorted_events() if e.kind != EventKind.HOTSPOT]
        sentry = timeline.filter_by_kind(EventKind.SENTRY)
        buf.write(self._c(_BOLD + _WHITE, "─" * 72) + "\n")
        parts = [f"{len(events)} events", f"{len(timeline.authors)} author(s)"]
        if sentry:
            parts.append(f"{len(sentry)} Sentry error(s)")
        if timeline.hotspots:
            parts.append(f"top hotspot: {timeline.hotspots[0].path}")
        buf.write(self._c(_DIM, "  " + "  ·  ".join(parts) + "\n\n"))

    def _fmt_window(self) -> str:
        delta = datetime.now(tz=UTC) - self.since
        total = int(delta.total_seconds())
        if total < 3600:
            return f"{total // 60}m"
        if total < 86400:
            return f"{total // 3600}h"
        return f"{total // 86400}d"
