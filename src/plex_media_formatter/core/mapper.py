"""
Mapper functions to compute file operations from discovered source files and episode metadata.
"""
import re
from pathlib import Path

from plex_media_formatter.config import Settings, settings
from plex_media_formatter.core.models import (
    FileOperation, 
    EpisodeInfo, 
    SeriesInfo, 
    SourceFile,
    PLEX_FILENAME
)

_SANITISE_PATTERN = re.compile(r'[\\/*?:"<>|]')


def _normalise_title(s: str) -> str:
    """Remove characters that are invalid in Windows filenames and trim whitespace."""
    cleaned = _SANITISE_PATTERN.sub("", s)
    return cleaned.replace("  ", " ").strip()


def _dest_path(
    root: Path,
    series: SeriesInfo,
    season: int,
    episode: EpisodeInfo,
    extension: str,
) -> Path:
    """Construct the destination path for a given episode, applying Plex naming conventions."""
    # Clean titles
    series_title = _normalise_title(series.title)
    episode_title = _normalise_title(episode.title)
    
    # Build plex subfolders
    series_dir = f"{series_title} ({series.year})"
    season_dir = f"Season {season:02d}"
    
    filename = PLEX_FILENAME.format(
        series_title=series_title,
        year=series.year,
        season=season,
        episode=episode.episode,
        episode_title=episode_title,
        extension=extension
    )
    return root / series_dir / season_dir / filename


def compute_file_operation_map(
    source_files: list[SourceFile],
    episodes: list[EpisodeInfo],
    series_info: SeriesInfo,
    season: int,
    episode_offset: int = 0,
    settings: Settings = settings
) -> list[FileOperation]:
    """
    Given a list of discovered source files and corresponding episode metadata, 
    compute the mapping of source to destination paths with proper Plex naming.
    """
    dest_root = Path(settings.plex_library_root)
    start = episode_offset
    end = episode_offset + len(source_files)
    
    if start < 0 or start >= len(episodes):
        raise ValueError(
            f"Episode offset ({episode_offset}) is out of bounds for the "
            f"available episode metadata array (Total episodes: {len(episodes)})."
        )
    
    episode_slice = episodes[start:end]
    if len(episode_slice) != len(source_files):
        raise ValueError(
            f"Source file count ({len(source_files)}) does not match "
            f"available episodes after offset ({len(episode_slice)}). "
            "Adjust episode_offset in your config."
        )

    return [
        FileOperation(
            source_path=src.path,
            destination_path=_dest_path(
                root=dest_root, 
                series=series_info, 
                season=season, 
                episode=ep, 
                extension=src.path.suffix
            ),
            series_title=series_info.title,
            year=series_info.year,
            season=season,
            episode=ep.episode,
            episode_title=ep.title,
            index_offset=episode_offset,
        )
        for src, ep in zip(source_files, episode_slice)
    ]
