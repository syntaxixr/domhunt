"""domhunt CLI entry point."""

from __future__ import annotations

import asyncio
import re
import sys

import click
from rich.console import Console
from rich.table import Table

from domhunt import __version__
from domhunt.checker import CheckResult, Status, check_many
from domhunt.tlds import resolve_tlds

console = Console()

# Domain labels per RFC 1035 §2.3.1, simplified: letters, digits, hyphen,
# 1-63 chars, no leading/trailing hyphen.
_NAME_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")


def _validate_name(name: str) -> str:
    name = name.strip().lower()
    if not _NAME_RE.match(name):
        raise click.BadParameter(
            f"'{name}' is not a valid domain label "
            "(use 1-63 letters/digits/hyphens, no leading/trailing hyphen)"
        )
    return name


def _render(name: str, results: list[CheckResult]) -> None:
    table = Table(
        title=f"domhunt: '{name}'",
        title_style="bold",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Domain", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Detail", style="dim")

    available_count = 0
    for r in results:
        if r.status is Status.AVAILABLE:
            status_str = "[green][+] available[/green]"
            available_count += 1
        elif r.status is Status.TAKEN:
            status_str = "[red][-] taken[/red]"
        else:
            status_str = "[yellow][?] unknown[/yellow]"
        table.add_row(r.domain, status_str, r.detail)

    console.print(table)
    console.print(
        f"\n[bold green]{available_count}[/bold green] available "
        f"of [bold]{len(results)}[/bold] checked."
    )


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="domhunt")
@click.argument("name")
@click.option(
    "--tlds",
    "tlds_spec",
    default=None,
    help="Comma-separated TLDs (e.g. com,io,dev), or 'all' for the extended list. "
    "Default: a curated developer-focused list.",
)
@click.option(
    "--concurrency",
    "-c",
    default=10,
    show_default=True,
    type=click.IntRange(1, 50),
    help="Max parallel RDAP queries.",
)
@click.option(
    "--available-only",
    "-a",
    is_flag=True,
    default=False,
    help="Only show domains that are available.",
)
def main(name: str, tlds_spec: str | None, concurrency: int, available_only: bool) -> None:
    """Check if NAME is available across a curated list of TLDs.

    \b
    Examples:
        domhunt myproject
        domhunt acme --tlds com,io,dev
        domhunt newco --tlds all --available-only
    """
    name = _validate_name(name)
    tlds = resolve_tlds(tlds_spec)

    with console.status(f"Querying {len(tlds)} TLDs..."):
        results = asyncio.run(check_many(name, tlds, concurrency=concurrency))

    if available_only:
        results = [r for r in results if r.status is Status.AVAILABLE]

    if not results:
        console.print("[yellow]No available domains found.[/yellow]")
        sys.exit(1)

    _render(name, results)


if __name__ == "__main__":
    main()
