"""Unit tests for postmortem renderers."""
import unittest
from datetime import datetime, timezone
from postmortem.models import Event, EventKind, Timeline
from postmortem.renderers.terminal import TerminalRenderer
from postmortem.renderers.markdown import MarkdownRenderer

_SINCE = datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc)

def _event(kind=EventKind.COMMIT, summary="fix: bug", author="alice"):
    return Event(
        timestamp=datetime(2024, 6, 1, 11, 0, tzinfo=timezone.utc),
        kind=kind, summary=summary, author=author, sha="deadbeef1234",
        meta={"files": ["src/main.py", "tests/test_main.py"]},
    )

def _tl(*events):
    tl = Timeline(since=_SINCE)
    tl.events = list(events)
    return tl

class TestTerminalRenderer(unittest.TestCase):
    def r(self): return TerminalRenderer(since=_SINCE, repo_path=".", color=False)
    def test_renders_content(self):
        out = self.r().render(_tl(_event()))
        self.assertIn("fix: bug", out)
        self.assertIn("alice", out)
        self.assertIn("deadbee", out)
    def test_empty_message(self): self.assertIn("No events", self.r().render(_tl()))
    def test_shows_files(self): self.assertIn("src/main.py", self.r().render(_tl(_event())))
    def test_truncates_many_files(self):
        e = Event(timestamp=datetime(2024,6,1,11,0,tzinfo=timezone.utc),
                  kind=EventKind.COMMIT, summary="big", author="bob", sha="abc",
                  meta={"files": [f"f{i}.py" for i in range(10)]})
        self.assertIn("more", self.r().render(_tl(e)))

class TestMarkdownRenderer(unittest.TestCase):
    def r(self): return MarkdownRenderer(since=_SINCE, repo_path=".")
    def test_renders_table(self):
        out = self.r().render(_tl(_event()))
        self.assertIn("| Time |", out)
        self.assertIn("fix: bug", out)
    def test_summary_section(self): self.assertIn("## TL;DR", self.r().render(_tl(_event())))
    def test_empty(self): self.assertIn("No events", self.r().render(_tl()))

if __name__ == "__main__": unittest.main()
