"""Typer CLI - format and revert sub-commands."""
import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn, 
    Progress, 
    SpinnerColumn, 
    TaskID, 
    TextColumn
)
from rich.table import Table

from plex_media_formatter.config import settings
from plex_media_formatter.api import get_api_client
from plex_media_formatter.core.models import (
    ExecutionState,
    FileOperation,
    Manifest,
    OperationType,
)
from plex_media_formatter.core import (
    scan_source,
    resolve_episode_offset,
    compute_file_operation_map,
    execute_operations,
    read_manifest,
    write_manifest,
    write_latest_manifest_pointer,
    resolve_manifest_path,
)

app = typer.Typer(
    name="plex-fmt",
    help="Manifest-driven CLI for formatting raw media files into Plex-compliant libraries.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


@app.command(
    help=(
        "Scan a source directory, fetch remote series metadata, compute the "
        "Plex file operation plan, write a manifest, and optionally execute it."
    ),
    short_help="Format raw media files into a Plex-ready structure.",
)
def format(  # noqa: A001
    source: Path = typer.Option(
        ...,
        "--source",
        "-s",
        help="Directory containing raw ripped media files such as title_t00.mkv.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    title: str = typer.Option(
        ...,
        "--title",
        "-t",
        help="Series title to search for in the configured metadata API.",
    ),
    season: int = typer.Option(
        1,
        "--season",
        min=1,
        help="Season number to map the source files against.",
    ),
    episode_offset: int | None = typer.Option(
        None,
        "--offset",
        min=0,
        help=(
            "Starting episode offset. If omitted, the tool will try to detect "
            "the next offset from the existing Plex output directory."
        ),
    ),
    clean_titles: bool = typer.Option(
        False,
        "--clean-titles",
        "-c",
        help=(
            "Scrub metadata prefixes (like SA, C, DI) and extra localization subtitles "
            "from TMDB episode names before renaming."
        ),
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the operation plan without creating directories, moving files, or writing a manifest.",
    ),
) -> None:
    """Scan → fetch remote → compute matrix → write manifest → execute."""

    # Scan source dir for media files
    console.rule("[bold cyan]Scanning source")
    source_files = scan_source(source)
    console.print(f"  Found [bold]{len(source_files)}[/] rip(s) in [dim]{source}[/]")
    if not source_files:
        raise typer.Exit(1)

    # Fetch data from API
    console.rule(f"[bold cyan]Fetching series metadata ({settings.api_client.upper()})")
    client = get_api_client()

    with console.status("Querying API…"):
        series_info = asyncio.run(client.fetch_series_info(title))
        episodes = asyncio.run(client.fetch_episodes(series_info.series_id, season, clean=clean_titles))

    # Detect global episode offset
    resolved_offset = resolve_episode_offset(
        series_title=series_info.title,
        year=series_info.year,
        season=season,
        user_offset=episode_offset,
    )
    
    offset_source = "user" if episode_offset is not None else "auto/default"
    console.print(
        f"  Episode offset: [bold]{resolved_offset}[/bold] [dim]({offset_source})[/dim]"
    )
    
    # Compute file operations matrix
    console.rule("[bold cyan]Computing file operations")
    operations = compute_file_operation_map(
        source_files, episodes, series_info, season, resolved_offset
    )
    _print_operations_table(operations)

    if dry_run:
        console.rule("[bold yellow]DRY RUN - no filesystem changes made")
        raise typer.Exit(0)

    # Write manifest to disk
    manifest = Manifest(
        series_title=series_info.title,
        year=series_info.year,
        api_source=settings.api_client,
        operations=operations,
    )
    manifest_path = Path(settings.manifest_path)
    write_manifest(manifest, manifest_path)
    write_latest_manifest_pointer(Path(settings.latest_manifest_path), manifest_path)
    console.print(f"  Manifest → [dim]{manifest_path}[/]")

    # Execute operations
    console.rule("[bold cyan]Executing")
    _run_with_progress(manifest, action_label="Moving", state_colour="cyan")
    _print_summary(manifest)


@app.command(
    help=(
        "Revert a previous formatting run by reading a manifest and moving files "
        "back to their original locations. If no manifest path is provided, the "
        "latest manifest pointer is used."
    ),
    short_help="Undo a previous format operation.",
)
def revert(
    manifest_path: Optional[Path] = typer.Argument(
        None,
        help=(
            "Optional path to a manifest file. If omitted, the command uses "
            "LATEST_MANIFEST_PATH."
        ),
        resolve_path=True,
    ),
) -> None:
    """Reverse-parse the state manifest and restore all files."""
    # Load manifest from disk
    path = resolve_manifest_path(
        manifest_path=manifest_path,
        latest_manifest_path=Path(settings.latest_manifest_path),
    )
    manifest = read_manifest(path)

    # Flip every operation to REVERT
    for op in manifest.operations:
        op.execution.type = OperationType.REVERT

    # Execute operations
    console.rule("[bold red]Reverting")
    _run_with_progress(manifest, action_label="Reverting", state_colour="red")
    _print_summary(manifest)


def _run_with_progress(
    manifest: Manifest,
    action_label: str,
    state_colour: str,
) -> None:
    """
    Run execute_operations with a live Rich progress bar.
    Wraps the single-argument callback signature expected by execute_operations.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task_id: TaskID = progress.add_task(
            f"{action_label}…", total=manifest.total_operations
        )

        def _callback(op: FileOperation) -> None:
            colour = state_colour if op.execution.state == ExecutionState.COMPLETED else "red"
            label = op.plex_filename if state_colour == "cyan" else op.source_path.name
            progress.update(
                task_id,
                advance=1,
                description=f"[{colour}]{label}",
            )

        try:
            execute_operations(manifest, callback=_callback)
        except RuntimeError:
            pass


def _print_summary(manifest: Manifest) -> None:
    """Render a Rich panel from manifest.status_summary() after execution."""
    summary = manifest.status_summary()
    elapsed = f"{summary['elapsed_s']:.1f}s" if summary["elapsed_s"] is not None else "—"

    lines = [
        f"[bold]Series:[/]        {summary['series']}",
        f"[bold]API source:[/]    {summary['api_source']}",
        f"[bold]Total:[/]         {summary['total']}",
        f"[bold]Completed:[/]     [green]{summary['completed']}[/]",
        f"[bold]Failed:[/]        [{'red' if summary['has_failures'] else 'dim'}]{summary['failed']}[/]",
        f"[bold]Progress:[/]      {summary['progress_pct']}%",
        f"[bold]Elapsed:[/]       {elapsed}",
    ]

    border = "red" if summary["has_failures"] else "green"
    title = "✗ Completed with failures" if summary["has_failures"] else "✓ Complete"
    console.print(Panel("\n".join(lines), title=title, border_style=border))

    if summary["has_failures"]:
        _print_failed_operations(manifest)
        raise typer.Exit(1)


def _print_failed_operations(manifest: Manifest) -> None:
    """Print a table of failed operations with their error messages."""
    failed = [op for op in manifest.operations if op.execution.state == ExecutionState.FAILED]
    if not failed:
        return

    table = Table(header_style="bold red", title="Failed Operations")
    table.add_column("Ep", style="dim", width=4)
    table.add_column("File", style="cyan")
    table.add_column("Error", style="red")

    for op in failed:
        error_msg = str(op.execution.error) if op.execution.error else "Unknown"
        table.add_row(str(op.episode), op.source_path.name, error_msg)

    console.print(table)


def _print_operations_table(operations: list[FileOperation]) -> None:
    table = Table(header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Source", style="cyan")
    table.add_column("→ Destination", style="green")
    for op in operations:
        table.add_row(str(op.episode), op.source_path.name, str(op.destination_path))
        
    console.print(table)
