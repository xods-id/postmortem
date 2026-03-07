<div align="center">

# 🔍 postmortem

**When production breaks, stop guessing. Start knowing.**

[![CI](https://img.shields.io/github/actions/workflow/status/phlx0/postmortem/ci.yml?style=flat-square&label=CI)](https://github.com/phlx0/postmortem/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

_Stitches together git history, file hotspots, and Sentry errors  
into a shareable incident report — in seconds._

```bash
postmortem --since 2h --output markdown --out-file incident.md
```

</div>

---

## Why postmortem?

Production is down. You need to know what changed and when — fast.

That means opening GitHub, scanning commits, cross-referencing deploy times, and asking teammates "did anyone push anything?" — all while the clock is ticking.

postmortem does it in one command.

```
────────────────────────────────────────────────────────────────────────
  🔍  postmortem  ·  my-api
  Since 2h  ·  19:58 UTC
────────────────────────────────────────────────────────────────────────

  🔥  File Hotspots

  ■■■  payments.py     changed 4x  risk 94%
       coupled: db.py  utils.py
  ■■  db.py            changed 3x  risk 71%

  ── Sat 07 Mar 2026 ──

  17:58  ⚠  [ERROR] NullPointerException in PaymentService.charge()  ← Sentry
             payments-api  ·  142 occurrences

  18:21  ●  fix: patch null pointer in payment handler  [3a7f2b1]  ← alice
             ↳ src/payments/handler.py
             ↳ tests/test_payments.py

  19:08  ⇄  Merge branch 'feature/stripe-v3' into main  [9c1e4fd]  ← bob
             ↳ src/stripe/client.py  ↳ src/stripe/webhooks.py  ↳ … +4

────────────────────────────────────────────────────────────────────────
  6 events  ·  2 authors  ·  1 Sentry error  ·  top hotspot: payments.py
```

---

## Installation

postmortem installs into an isolated virtualenv at `~/.postmortem` and adds itself to your `$PATH` automatically. Open a new terminal and you're ready.

**Linux / macOS**

```bash
curl -sSL https://raw.githubusercontent.com/phlx0/postmortem/main/install.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/phlx0/postmortem/main/install.ps1 | iex
```

**From source** (edits apply instantly — no reinstall needed)

```bash
git clone https://github.com/phlx0/postmortem
cd postmortem
bash install.sh       # or: .\install.ps1 on Windows
```

**Requires:** Python 3.11+, git

```bash
postmortem --version   # verify install
bash install.sh --uninstall   # remove cleanly
```

---

## Commands

### Basic usage

```bash
postmortem                                    # last 2 hours, current repo
postmortem --since 30m                        # last 30 minutes
postmortem --since 1d                         # last day
postmortem --since 4h --repo /path/to/repo    # different repo
```

### Generate a shareable report

```bash
postmortem --since 2h --output markdown --out-file incident.md
```

Paste directly into a GitHub issue or Slack. The report includes a TL;DR table, file hotspot rankings, Sentry errors, and the full commit timeline with collapsible file diffs.

### Sentry integration

```bash
export SENTRY_TOKEN=sntrys_...
export SENTRY_ORG=my-org
export SENTRY_PROJECT=api         # optional — searches all projects if omitted

postmortem --since 2h
```

Or pass inline:

```bash
postmortem --since 2h --sentry-org my-org --sentry-token sntrys_...
```

### All flags

| Flag               | Default           | Description                                   |
| ------------------ | ----------------- | --------------------------------------------- |
| `--since`, `-s`    | `2h`              | How far back to look: `30m`, `2h`, `1d`, `1w` |
| `--repo`, `-r`     | `.`               | Path to a git repository                      |
| `--output`, `-o`   | `terminal`        | Output format: `terminal` or `markdown`       |
| `--out-file`, `-f` | stdout            | Write output to a file                        |
| `--no-color`       | false             | Disable ANSI colours                          |
| `--sentry-token`   | `$SENTRY_TOKEN`   | Sentry auth token                             |
| `--sentry-org`     | `$SENTRY_ORG`     | Sentry organisation slug                      |
| `--sentry-project` | `$SENTRY_PROJECT` | Sentry project slug                           |
| `--version`, `-v`  |                   | Show version and exit                         |

---

## What's in the report

### 🔥 File hotspots

Pure git analysis — no config needed. Ranks every file touched during the window by:

- **Change frequency** — how many times it was modified
- **Recency** — changes in the last 25% of the window score higher
- **Coupling** — files that always change together are a hidden coordination risk

The coupling column is often the most useful: if `payments.py` and `db.py` consistently appear in the same commits but aren't directly imported by each other, that's a hidden dependency worth knowing about.

### 🔴 Sentry errors

Surfaces issues whose _last seen_ time falls inside the incident window. Requires a read-scope auth token — see [Sentry setup](#sentry-integration) above.

### 📋 Git timeline

Commits, merges, and tags in chronological order, each with author, SHA, and the list of files changed. Merges are labelled separately so you can spot integration points at a glance.

---

## Project structure

```
postmortem/
├── cli.py              Click entry point — stays thin
├── pipeline.py         Wires collectors → Timeline
├── models.py           Event, Timeline, HotspotFile — pure data
├── collectors/
│   ├── __init__.py     BaseCollector ABC
│   ├── git.py          Commits, merges, tags
│   ├── hotspot.py      File frequency + coupling analysis
│   └── sentry.py       Sentry Issues API
├── renderers/
│   ├── __init__.py     BaseRenderer ABC
│   ├── terminal.py     ANSI terminal output
│   └── markdown.py     GitHub-flavoured incident report
└── utils/
    └── time.py         "2h" → datetime
```

### Adding a collector

```python
# postmortem/collectors/datadog.py
from postmortem.collectors import BaseCollector
from postmortem.models import Event, EventKind

class DatadogCollector(BaseCollector):
    def collect(self) -> list[Event]:
        # hit the Datadog API, return Events
        ...
```

Register it in `pipeline.py`. That's it.

### Planned collectors

- [ ] GitHub Actions — CI run pass/fail per commit
- [ ] Datadog / Grafana — annotation and alert events
- [ ] PagerDuty — on-call alerts in the window
- [ ] Heroku / Railway — deploy events

PRs welcome.

---

## Development

```bash
git clone https://github.com/phlx0/postmortem
cd postmortem
bash install.sh          # editable install — changes apply immediately

pytest                   # run all tests
ruff check postmortem    # lint
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

<div align="center">

Made with ☕ · [MIT License](LICENSE)

</div>
