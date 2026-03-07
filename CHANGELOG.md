# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-07

### Added

- Initial release
- **Git collector** — commits, merges, and tags with per-commit file-level detail
- **File hotspot collector** — ranks files by change frequency, recency, and
  co-change coupling. Zero config, pure git analysis. Surfaces the likely blast
  radius of an incident.
- **Sentry collector** — fetches issues whose _last seen_ time falls inside the
  incident window. Requires `SENTRY_TOKEN` and `SENTRY_ORG` env vars (or CLI
  flags). Silently skipped if not configured.
- `--since` flag supporting `m`, `h`, `d`, `w` durations (e.g. `30m`, `2h`, `1d`)
- `--output terminal|markdown` flag
- `--out-file` flag to write reports to disk
- `--no-color` flag for CI/pipe-friendly output
- `--sentry-token`, `--sentry-org`, `--sentry-project` flags (also readable
  from `SENTRY_TOKEN`, `SENTRY_ORG`, `SENTRY_PROJECT` env vars)
- Terminal renderer with ANSI colours, icons, hotspot panel, and inline Sentry events
- Markdown renderer producing a structured incident report with TL;DR table,
  file hotspot rankings, Sentry errors section, and collapsible file diffs —
  designed to paste directly into a GitHub issue or Slack
- `HotspotFile` model with `path`, `change_count`, `coupled_files`, `risk_score`
- `Timeline.hotspots` field populated by the hotspot collector
- `EventKind` values: `commit`, `merge`, `tag`, `sentry`, `hotspot`
- `postmortem/__main__.py` so `python -m postmortem` works as a fallback
- Linux/macOS installer (`install.sh`) — isolated virtualenv at `~/.postmortem`,
  automatic PATH setup via `~/.local/bin`, editable dev mode, `--uninstall` flag
- Windows PowerShell installer (`install.ps1`) — isolated virtualenv, user PATH
  management via registry, editable dev mode, `-Uninstall` flag
- Full test suite: 23 unit tests + 5 integration tests against a real git repo
- GitHub Actions CI — lint, Python 3.11/3.12/3.13 matrix, Linux and Windows
  install smoke tests
- GitHub Actions release workflow — PyPI publish + GitHub Releases on tag push
- Bug report, feature request, and new collector issue templates
- Pull request template with contributor checklist
- `CONTRIBUTING.md` with architecture overview, collector/renderer guides,
  and commit style conventions
- `SECURITY.md` with vulnerability reporting policy and Sentry token guidance

[Unreleased]: https://github.com/phlx0/postmortem/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/phlx0/postmortem/releases/tag/v0.1.0
