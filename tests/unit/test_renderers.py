"""Unit tests for postmortem renderers."""
import unittest
from datetime import UTC, datetime

from postmortem.models import Event, EventKind, Timeline
from postmortem.renderers.markdown import MarkdownRenderer
from postmortem.renderers.terminal import TerminalRenderer

_SINCE = datetime(2024, 6, 1, 10, 0, tzinfo=UTC)


def _event(kind=EventKind.COMMIT, summary="fix: bug", author="alice"):
    return Event(
        timestamp=datetime(2024, 6, 1, 11, 0, tzinfo=UTC),
        kind=kind,
        summary=summary,
        author=author,
        sha="deadbeef1234",
        meta={"files": ["src/main.py", "tests/test_main.py"]},
    )


def _tl(*events):
    tl = Timeline(since=_SINCE)
    tl.events = list(events)
    return tl


class TestTerminalRenderer(unittest.TestCase):
    def r(self):
        return TerminalRenderer(since=_SINCE, repo_path=".", color=False)

    def test_renders_content(self):
        out = self.r().render(_tl(_event()))
        assert "fix: bug" in out
        assert "alice" in out
        assert "deadbee" in out

    def test_empty_message(self):
        out = self.r().render(_tl())
        assert "No events" in out

    def test_shows_files(self):
        out = self.r().render(_tl(_event()))
        assert "src/main.py" in out

    def test_truncates_many_files(self):
        e = Event(
            timestamp=datetime(2024, 6, 1, 11, 0, tzinfo=UTC),
            kind=EventKind.COMMIT,
            summary="big",
            author="bob",
            sha="abc",
            meta={"files": [f"f{i}.py" for i in range(10)]},
        )
        out = self.r().render(_tl(e))
        assert "more" in out


class TestMarkdownRenderer(unittest.TestCase):
    def r(self):
        return MarkdownRenderer(since=_SINCE, repo_path=".")

    def test_renders_table(self):
        out = self.r().render(_tl(_event()))
        assert "| Time |" in out
        assert "fix: bug" in out

    def test_summary_section(self):
        out = self.r().render(_tl(_event()))
        assert "## TL;DR" in out

    def test_empty(self):
        out = self.r().render(_tl())
        assert "No events" in out


if __name__ == "__main__":
    unittest.main()
