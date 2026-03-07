"""Unit tests for postmortem.models."""
import unittest
from datetime import datetime, timezone, timedelta
from postmortem.models import Event, EventKind, Timeline

def _ts(offset_min=0):
    return datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc) - timedelta(minutes=offset_min)

def _event(offset=0, kind=EventKind.COMMIT, author="alice"):
    return Event(timestamp=_ts(offset), kind=kind, summary="test", author=author, sha="abc1234def5678")

class TestEvent(unittest.TestCase):
    def test_short_sha(self): self.assertEqual(_event().short_sha, "abc1234")
    def test_short_sha_empty(self):
        e = Event(timestamp=datetime.now(tz=timezone.utc), kind=EventKind.COMMIT, summary="x")
        self.assertEqual(e.short_sha, "")
    def test_ordering(self): self.assertLess(_event(10), _event(5))

class TestTimeline(unittest.TestCase):
    def _tl(self, *events):
        tl = Timeline(since=_ts(60))
        tl.events = list(events)
        return tl

    def test_sorted_events(self):
        tl = self._tl(_event(5), _event(10), _event(1))
        ts = [e.timestamp for e in tl.sorted_events()]
        self.assertEqual(ts, sorted(ts))

    def test_filter_by_kind(self):
        tl = self._tl(_event(5), _event(4, kind=EventKind.MERGE), _event(3, kind=EventKind.TAG))
        self.assertEqual(len(tl.filter_by_kind(EventKind.COMMIT, EventKind.MERGE)), 2)

    def test_authors_deduped(self):
        tl = self._tl(_event(5, author="alice"), _event(4, author="bob"), _event(3, author="alice"))
        self.assertEqual(tl.authors, ["alice", "bob"])

    def test_is_empty(self):
        tl = self._tl()
        self.assertTrue(tl.is_empty)
        tl.events.append(_event())
        self.assertFalse(tl.is_empty)

if __name__ == "__main__": unittest.main()
