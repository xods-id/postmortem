"""Unit tests for postmortem.utils.time."""
import unittest
from datetime import datetime, timezone
from postmortem.utils.time import parse_since

class TestParseSince(unittest.TestCase):
    def _approx(self, dt, seconds, tol=5):
        return abs((datetime.now(tz=timezone.utc) - dt).total_seconds() - seconds) < tol

    def test_minutes(self): self.assertTrue(self._approx(parse_since("30m"), 1800))
    def test_hours(self): self.assertTrue(self._approx(parse_since("2h"), 7200))
    def test_days(self): self.assertTrue(self._approx(parse_since("1d"), 86400))
    def test_weeks(self): self.assertTrue(self._approx(parse_since("1w"), 604800))
    def test_uppercase(self): self.assertTrue(self._approx(parse_since("30M"), 1800))
    def test_invalid(self):
        with self.assertRaises(ValueError): parse_since("2hours")
    def test_no_unit(self):
        with self.assertRaises(ValueError): parse_since("120")
    def test_empty(self):
        with self.assertRaises(ValueError): parse_since("")
    def test_tz_aware(self): self.assertIsNotNone(parse_since("1h").tzinfo)

if __name__ == "__main__": unittest.main()
