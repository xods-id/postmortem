"""CLI entry point for postmortem."""

import sys
import click

from postmortem import __version__
from postmortem.pipeline import build_timeline
from postmortem.renderers.terminal import TerminalRenderer
from postmortem.renderers.markdown import MarkdownRenderer
from postmortem.utils.time import parse_since


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--since", "-s", default="2h", metavar="DURATION", show_default=True,
              help="How far back to look. e.g. 30m, 2h, 1d")
@click.option("--repo", "-r", default=".", metavar="PATH", show_default=True,
              help="Path to the git repository.")
@click.option("--output", "-o", type=click.Choice(["terminal", "markdown"], case_sensitive=False),
              default="terminal", show_default=True, help="Output format.")
@click.option("--out-file", "-f", metavar="FILE", default=None,
              help="Write output to a file instead of stdout.")
@click.option("--no-color", is_flag=True, default=False,
              help="Disable colored output.")
@click.option("--sentry-token", envvar="SENTRY_TOKEN", default=None, metavar="TOKEN",
              help="Sentry auth token (or set SENTRY_TOKEN env var).")
@click.option("--sentry-org", envvar="SENTRY_ORG", default=None, metavar="SLUG",
              help="Sentry organisation slug (or set SENTRY_ORG env var).")
@click.option("--sentry-project", envvar="SENTRY_PROJECT", default=None, metavar="SLUG",
              help="Sentry project slug (optional, searches all projects if omitted).")
@click.version_option(__version__, "-v", "--version", prog_name="postmortem")
def cli(since, repo, output, out_file, no_color, sentry_token, sentry_org, sentry_project):
    """
    \b
    postmortem — instant incident timelines from your repo.

    Stitches together git commits, file hotspots, and Sentry errors
    into a human-readable incident timeline.

    \b
    Examples:
      postmortem --since 2h
      postmortem --since 1d --output markdown --out-file report.md
      postmortem --since 4h --sentry-org my-org --sentry-project api
    """
    try:
        since_dt = parse_since(since)
    except ValueError as exc:
        click.echo(f"[error] Invalid --since value: {exc}", err=True)
        sys.exit(1)

    try:
        timeline = build_timeline(
            repo_path=repo,
            since=since_dt,
            sentry_token=sentry_token,
            sentry_org=sentry_org,
            sentry_project=sentry_project,
        )
    except Exception as exc:
        click.echo(f"[error] {exc}", err=True)
        sys.exit(1)

    if output == "markdown":
        renderer = MarkdownRenderer(since=since_dt, repo_path=repo)
    else:
        renderer = TerminalRenderer(since=since_dt, repo_path=repo, color=not no_color)

    rendered = renderer.render(timeline)

    if out_file:
        with open(out_file, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        click.echo(f"Report saved to {out_file}")
    else:
        click.echo(rendered)


def main() -> None:
    cli()
