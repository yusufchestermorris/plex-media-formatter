"""
Helpers for resolving episode offsets from the output library.
"""
from __future__ import annotations

import re
from pathlib import Path

from plex_media_formatter.config import settings


_EPISODE_PATTERN = re.compile(r"S(?P<season>\d{2})E(?P<episode>\d{2,4})", re.IGNORECASE)


def get_season_output_dir(
    plex_library_root: Path,
    series_title: str,
    year: int,
    season: int,
) -> Path:
    return plex_library_root / f"{series_title} ({year})" / f"Season {season:02d}"


def detect_episode_offset(
    plex_library_root: Path,
    series_title: str,
    year: int,
    season: int,
) -> int | None:
    """
    Return the next available episode offset for an existing Plex season dir.

    Example:
    - existing highest file is S01E12 -> returns 12
    - no directory / no matches -> returns None

    The returned value is intended to be used as the slice offset for remote
    episode mapping, i.e. source_files[0] maps to episodes[offset].
    """
    season_dir = get_season_output_dir(plex_library_root, series_title, year, season)
    if not season_dir.exists() or not season_dir.is_dir():
        return None

    max_episode = None

    for path in season_dir.iterdir():
        if not path.is_file():
            continue

        match = _EPISODE_PATTERN.search(path.name)
        if not match:
            continue

        file_season = int(match.group("season"))
        file_episode = int(match.group("episode"))

        if file_season != season:
            continue

        if max_episode is None or file_episode > max_episode:
            max_episode = file_episode

    return max_episode


def resolve_episode_offset(
    series_title: str,
    year: int,
    season: int,
    user_offset: int | None = None,
) -> int:
    """
    Offset precedence:
    1. explicit user input
    2. inferred from existing output dir
    3. zero
    """
    if user_offset is not None:
        return user_offset

    detected = detect_episode_offset(
        plex_library_root=Path(settings.plex_library_root),
        series_title=series_title,
        year=year,
        season=season,
    )
    return detected if detected is not None else 0
