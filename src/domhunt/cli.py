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
from domhunt.suggester import variations
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


def _fmt_price(p: float | None) -> str:
    return f"${p:g}/yr" if p is not None else "-"


def _render(title: str, results: list[CheckResult]) -> int:
    """Render a single results table. Returns the number of available rows."""
    table = Table(title=title, title_style="bold", show_header=True, header_style="bold")
    table.add_column("Domain", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Price", no_wrap=True, style="dim")
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
        table.add_row(r.domain, status_str, _fmt_price(r.price_usd), r.detail)

    console.print(table)
    return available_count


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
@click.option(
    "--no-suggest",
    is_flag=True,
    default=False,
    help="Skip the suggester even when nothing is available for the original name.",
)
def main(
    name: str,
    tlds_spec: str | None,
    concurrency: int,
    available_only: bool,
    no_suggest: bool,
) -> None:
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

    visible = [r for r in results if r.status is Status.AVAILABLE] if available_only else results

    if visible:
        _render(f"domhunt: '{name}'", visible)
    else:
        console.print("[yellow]No domains to show.[/yellow]")

    total_available = sum(1 for r in results if r.status is Status.AVAILABLE)
    console.print(
        f"\n[bold green]{total_available}[/bold green] available "
        f"of [bold]{len(results)}[/bold] checked."
    )

    if total_available == 0 and not no_suggest:
        _run_suggester(name, tlds, concurrency)

    if total_available == 0 and not visible:
        sys.exit(1)


async def _gather_suggestions(
    candidates: list[str], tlds: list[str], concurrency: int
) -> list[CheckResult]:
    chunks = await asyncio.gather(
        *(check_many(c, tlds, concurrency=concurrency) for c in candidates)
    )
    return [r for chunk in chunks for r in chunk]


def _run_suggester(name: str, tlds: list[str], concurrency: int) -> None:
    candidates = variations(name, limit=12)
    if not candidates:
        return

    console.print("\n[bold]Searching variations...[/bold]")
    with console.status(f"Querying {len(candidates) * len(tlds)} candidate domains..."):
        all_results = asyncio.run(_gather_suggestions(candidates, tlds, concurrency))

    # Only surface candidates that are actually available — otherwise the
    # suggester table is huge and useless.
    visible = [r for r in all_results if r.status is Status.AVAILABLE]

    if visible:
        _render("Try one of these instead", visible)
    else:
        console.print(
            "[yellow]Even the variations are all taken. Try a longer or more unusual name.[/yellow]"
        )


if __name__ == "__main__":
    main()
