"""Markdown renderer - produces a GitHub/Slack-ready incident report."""

from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO

from postmortem.models import Event, EventKind, HotspotFile, Timeline
from postmortem.renderers import BaseRenderer

_KIND_EMOJI: dict[EventKind, str] = {
    EventKind.COMMIT: "🟢",
    EventKind.MERGE: "🔀",
    EventKind.TAG: "🏷️",
    EventKind.BRANCH: "🌿",
    EventKind.FILE_CHANGE: "📝",
    EventKind.SENTRY: "🔴",
    EventKind.HOTSPOT: "🔥",
}

_RISK_BAR = {(0.0, 0.3): "🟢 Low", (0.3, 0.6): "🟡 Medium", (0.6, 0.8): "🟠 High", (0.8, 1.1): "🔴 Critical"}


def _risk_label(score: float) -> str:
    for (lo, hi), label in _RISK_BAR.items():
        if lo <= score < hi:
            return label
    return "🔴 Critical"


def _fmt_ts(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%H:%M UTC")


def _fmt_date(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%d")


class MarkdownRenderer(BaseRenderer):
    """Renders a Timeline as a polished GitHub-flavoured incident report."""

    def render(self, timeline: Timeline) -> str:
        buf = StringIO()
        self._write_header(buf, timeline)
        self._write_tldr(buf, timeline)

        if timeline.hotspots:
            self._write_hotspots(buf, timeline.hotspots)

        sentry_events = timeline.filter_by_kind(EventKind.SENTRY)
        if sentry_events:
            self._write_sentry(buf, sentry_events)

        self._write_timeline(buf, timeline)
        self._write_footer(buf, timeline)
        return buf.getvalue()

    # ------------------------------------------------------------------

    def _write_header(self, buf: StringIO, timeline: Timeline) -> None:
        now = datetime.now(tz=timezone.utc)
        repo_name = self.repo_path.name
        buf.write(f"# 🔍 Incident Report — `{repo_name}`\n\n")
        buf.write(f"> **Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}  \n")
        buf.write(f"> **Window:** last {self._fmt_window()} ")
        buf.write(f"(`{self.since.strftime('%Y-%m-%d %H:%M UTC')}` → now)\n\n")
        buf.write("---\n\n")

    def _write_tldr(self, buf: StringIO, timeline: Timeline) -> None:
        events = timeline.sorted_events()
        commits = timeline.filter_by_kind(EventKind.COMMIT, EventKind.MERGE)
        sentry = timeline.filter_by_kind(EventKind.SENTRY)
        top_hotspot = timeline.hotspots[0] if timeline.hotspots else None

        buf.write("## TL;DR\n\n")
        buf.write(f"| Metric | Value |\n|--------|-------|\n")
        buf.write(f"| Commits / Merges | {len(commits)} |\n")
        buf.write(f"| Authors | {', '.join(timeline.authors) or '—'} |\n")

        all_files: set[str] = set()
        for e in commits:
            all_files.update(e.meta.get("files", []))
        buf.write(f"| Files touched | {len(all_files)} |\n")

        if sentry:
            levels = [e.meta.get("level", "error") for e in sentry]
            critical = sum(1 for l in levels if l in ("fatal", "error"))
            buf.write(f"| Sentry errors | {len(sentry)} ({critical} error/fatal) |\n")

        if top_hotspot:
            buf.write(f"| Riskiest file | `{top_hotspot.path}` ({_risk_label(top_hotspot.risk_score)}) |\n")

        buf.write("\n")

        if timeline.is_empty:
            buf.write("> _No events found in this window._\n\n")

    def _write_hotspots(self, buf: StringIO, hotspots: list[HotspotFile]) -> None:
        buf.write("## 🔥 File Hotspots\n\n")
        buf.write("Files that changed most frequently — highest risk of being the blast radius.\n\n")
        buf.write("| Risk | File | Changes | Co-changes with |\n")
        buf.write("|------|------|---------|----------------|\n")
        for h in hotspots:
            coupled = ", ".join(f"`{f}`" for f in h.coupled_files) if h.coupled_files else "—"
            bar = _risk_label(h.risk_score)
            buf.write(f"| {bar} | `{h.path}` | {h.change_count}x | {coupled} |\n")
        buf.write("\n")

    def _write_sentry(self, buf: StringIO, events: list[Event]) -> None:
        buf.write("## 🔴 Sentry Errors\n\n")
        buf.write("Errors that were active during the incident window.\n\n")
        buf.write("| Time | Level | Error | Occurrences | Link |\n")
        buf.write("|------|-------|-------|-------------|------|\n")
        for e in sorted(events):
            ts = _fmt_ts(e.timestamp)
            level = e.meta.get("level", "error").upper()
            title = e.meta.get("title", e.summary).replace("|", "\\|")[:80]
            count = e.meta.get("count", "?")
            url = e.meta.get("url", "")
            link = f"[#{e.meta.get('issue_id', '?')}]({url})" if url else f"#{e.meta.get('issue_id', '?')}"
            buf.write(f"| {ts} | `{level}` | {title} | {count} | {link} |\n")
        buf.write("\n")

    def _write_timeline(self, buf: StringIO, timeline: Timeline) -> None:
        # Exclude hotspot meta-events from the timeline table — they're in their own section
        events = [e for e in timeline.sorted_events() if e.kind != EventKind.HOTSPOT]
        if not events:
            return

        buf.write("## 📋 Timeline\n\n")

        current_date: str | None = None
        for e in events:
            date = _fmt_date(e.timestamp)
            if date != current_date:
                current_date = date
                buf.write(f"### {date}\n\n")
                buf.write("| Time | Type | Summary | Author | SHA |\n")
                buf.write("|------|------|---------|--------|-----|\n")

            emoji = _KIND_EMOJI.get(e.kind, "•")
            ts = _fmt_ts(e.timestamp)
            kind = e.kind.value
            summary = e.summary.replace("|", "\\|")
            author = e.author or "—"
            sha = f"`{e.short_sha}`" if e.short_sha else "—"
            buf.write(f"| {ts} | {emoji} `{kind}` | {summary} | {author} | {sha} |\n")

            # Show changed files as a collapsible block for commits
            files: list[str] = e.meta.get("files", [])
            if files and e.kind in (EventKind.COMMIT, EventKind.MERGE):
                # We can't do collapsible mid-table in GitHub MD, so we add a
                # follow-up details block after completing the table row.
                pass

        buf.write("\n")

        # Now write file details as collapsible blocks beneath the table
        buf.write("<details>\n<summary>Changed files per commit</summary>\n\n")
        for e in events:
            files = e.meta.get("files", [])
            if files and e.kind in (EventKind.COMMIT, EventKind.MERGE):
                buf.write(f"**`{e.short_sha}`** — {e.summary}  \n")
                for f in files:
                    buf.write(f"- `{f}`\n")
                buf.write("\n")
        buf.write("</details>\n\n")

    def _write_footer(self, buf: StringIO, timeline: Timeline) -> None:
        buf.write("---\n\n")
        buf.write("_Generated by [postmortem](https://github.com/phlx0/postmortem)_\n")

    def _fmt_window(self) -> str:
        delta = datetime.now(tz=timezone.utc) - self.since
        total = int(delta.total_seconds())
        if total < 3600:
            return f"{total // 60}m"
        if total < 86400:
            return f"{total // 3600}h"
        return f"{total // 86400}d"
