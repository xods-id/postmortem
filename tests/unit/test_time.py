"""Unit tests for postmortem.utils.time."""
import unittest
from datetime import UTC, datetime

import pytest

from postmortem.utils.time import parse_since


class TestParseSince(unittest.TestCase):
    def _approx(self, dt, seconds, tol=5):
        return abs((datetime.now(tz=UTC) - dt).total_seconds() - seconds) < tol

    def test_minutes(self):
        assert self._approx(parse_since("30m"), 1800)

    def test_hours(self):
        assert self._approx(parse_since("2h"), 7200)

    def test_days(self):
        assert self._approx(parse_since("1d"), 86400)

    def test_weeks(self):
        assert self._approx(parse_since("1w"), 604800)

    def test_uppercase(self):
        assert self._approx(parse_since("30M"), 1800)

    def test_invalid(self):
        with pytest.raises(ValueError, match=".*"):
            parse_since("2hours")

    def test_no_unit(self):
        with pytest.raises(ValueError, match=".*"):
            parse_since("120")

    def test_empty(self):
        with pytest.raises(ValueError, match=".*"):
            parse_since("")

    def test_tz_aware(self):
        assert parse_since("1h").tzinfo is not None


if __name__ == "__main__":
    unittest.main()
