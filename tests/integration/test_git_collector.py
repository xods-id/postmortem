"""Integration tests against a real (temporary) git repository."""
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from postmortem.pipeline import build_timeline

def make_git_repo():
    tmp = Path(tempfile.mkdtemp())
    env = {**os.environ, "GIT_AUTHOR_DATE": "2024-06-01T12:00:00Z", "GIT_COMMITTER_DATE": "2024-06-01T12:00:00Z"}
    def run(*args): subprocess.run(list(args), cwd=tmp, capture_output=True, check=True, env=env)
    subprocess.run(["git", "init", str(tmp)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(tmp), "config", "user.email", "test@test.com"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(tmp), "config", "user.name", "Test User"], capture_output=True, check=True)
    (tmp / "hello.py").write_text("print('hello')\n")
    subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(tmp), "commit", "-m", "feat: initial commit"], capture_output=True, check=True, env=env)
    (tmp / "world.py").write_text("print('world')\n")
    subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(tmp), "commit", "-m", "fix: add world module"], capture_output=True, check=True, env=env)
    return tmp

REPO = make_git_repo()
SINCE_OLD = datetime(2024, 1, 1, tzinfo=timezone.utc)

class TestGitIntegration(unittest.TestCase):
    def test_collects_commits(self):
        tl = build_timeline(str(REPO), SINCE_OLD)
        summaries = [e.summary for e in tl.events]
        self.assertTrue(any("initial commit" in s for s in summaries))
        self.assertTrue(any("world module" in s for s in summaries))

    def test_events_have_author(self):
        tl = build_timeline(str(REPO), SINCE_OLD)
        for e in tl.events: self.assertEqual(e.author, "Test User")

    def test_events_have_sha(self):
        tl = build_timeline(str(REPO), SINCE_OLD)
        for e in tl.events: self.assertEqual(len(e.sha), 40)

    def test_since_filters_old_commits(self):
        tl = build_timeline(str(REPO), datetime.now(tz=timezone.utc))
        self.assertTrue(tl.is_empty)

    def test_invalid_repo_raises(self):
        import tempfile
        with self.assertRaises(RuntimeError):
            build_timeline(tempfile.mkdtemp(), datetime.now(tz=timezone.utc))

if __name__ == "__main__": unittest.main()
