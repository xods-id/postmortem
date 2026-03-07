# Contributing to postmortem

Thank you for your interest in contributing! This guide covers everything you need to know.

## Development setup

```bash
# Clone the repo
git clone https://github.com/phlx0/postmortem
cd postmortem

# Run the install script in dev mode (editable install)
bash install.sh

# Or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Your changes to the `postmortem/` directory take effect immediately — no reinstall needed.

## Running tests

```bash
pytest                        # all tests
pytest tests/unit/            # unit tests only
pytest tests/integration/     # integration tests only
pytest --cov=postmortem       # with coverage
```

## Code style

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
ruff check postmortem tests   # lint
ruff format postmortem tests  # format
```

## Architecture overview

```
postmortem/
├── cli.py           # Click entry point — thin, delegates everything
├── pipeline.py      # Orchestrates collectors → Timeline
├── models.py        # Pure data classes: Event, Timeline, EventKind
├── collectors/      # One file per data source
│   ├── __init__.py  # BaseCollector ABC
│   └── git.py       # Git log, tags
├── renderers/       # One file per output format
│   ├── __init__.py  # BaseRenderer ABC
│   ├── terminal.py  # Colourised terminal output
│   └── markdown.py  # GitHub-flavoured Markdown
└── utils/
    └── time.py      # Duration parsing
```

### Adding a new collector

1. Create `postmortem/collectors/myservice.py`
2. Subclass `BaseCollector` and implement `collect() -> list[Event]`
3. Register it in `pipeline.py`
4. Add tests in `tests/unit/` and optionally `tests/integration/`

### Adding a new renderer

1. Create `postmortem/renderers/myformat.py`
2. Subclass `BaseRenderer` and implement `render(timeline) -> str`
3. Add it as a `--output` choice in `cli.py`

## Pull request checklist

- [ ] Tests pass: `pytest`
- [ ] Linter clean: `ruff check .`
- [ ] New functionality has tests
- [ ] CHANGELOG.md updated under `[Unreleased]`

## Commit style

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add GitHub Actions collector
fix: handle repos with no commits
docs: improve README install section
chore: bump click to 8.2
```
