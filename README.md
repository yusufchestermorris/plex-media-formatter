# Plex Media Formatter

Plex Media Formatter is a manifest-driven Python CLI for turning raw optical media rips into Plex-compliant TV library structures.

It is designed for workflows where tools such as MakeMKV produce sequential files like `title_t00.mkv`, `title_t01.mkv`, and `title_t02.mkv`, and those files need to be renamed and moved into a clean Plex season layout.

## Features

- Scans a source directory for sequential ripped media files.
- Fetches series and episode metadata from a configured API client.
- Resolves episode offsets automatically from the existing Plex output directory, with optional user override.
- Computes the full file operation plan before executing any filesystem changes.
- Writes a manifest file so the run can be reviewed and reverted.
- Supports dry-run mode for safe verification.
- Supports revert mode to undo a previous format operation.

## Project layout

```text
src/plex_media_formatter/
├── api/        # Metadata clients and API selection
├── cli/        # Typer command-line application
├── config/     # Pydantic settings
└── core/       # Scanning, offsets, mapping, manifest, execution
```

## Installation

This project is designed to work well with `uv`.

```bash
uv sync
```

Then run the CLI with:

```bash
uv run plex-fmt --help
```

## Usage

### Format files

```bash
uv run plex-fmt format \
  --source /path/to/raw_rips \
  --title "Cowboy Bebop" \
  --season 1
```

### Dry run

```bash
uv run plex-fmt format \
  --source /path/to/raw_rips \
  --title "Cowboy Bebop" \
  --season 1 \
  --dry-run
```

### Override detected offset

```bash
uv run plex-fmt format \
  --source /path/to/raw_rips \
  --title "Cowboy Bebop" \
  --season 1 \
  --offset 12
```

### Revert a previous run

```bash
uv run plex-fmt revert
```

Or with an explicit manifest path:

```bash
uv run plex-fmt revert /path/to/manifest.json
```

## Configuration

Configuration is loaded from environment variables or a `.env` file.

Common settings include:

- `API_CLIENT` — metadata provider, for example `tmdb` or `jikan`
- `API_URL` — optional override for the API base URL
- `API_KEY` — required when using `tmdb`
- `PLEX_LIBRARY_ROOT` — root Plex library path for output scanning and offset detection
- `MANIFEST_PATH` — path to the manifest file written during format runs

Example `.env`:

```env
API_CLIENT=jikan
PLEX_LIBRARY_ROOT=/mnt/plex/media
MANIFEST_PATH=/mnt/plex/media/manifest.json
```

## Safety model

The formatter is designed around a safety-first workflow:

1. Scan source files.
2. Fetch remote metadata.
3. Resolve the effective episode offset.
4. Compute the full file operation map.
5. Write the manifest.
6. Execute the file operations.

This separation between planning and side effects makes the tool easier to inspect, test, and revert.

## Development

Run tests with:

```bash
uv run pytest
```

Run the CLI locally with:

```bash
uv run plex-fmt --help
```