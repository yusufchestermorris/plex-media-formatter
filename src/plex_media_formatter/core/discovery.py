"""
Scans a source directory for sequential MKV rip files.
"""
import re
from pathlib import Path

from plex_media_formatter.core.models import SourceFile

_FILE_PATTERN = re.compile(r".*_t(\d+)\.[a-z0-9]+$", re.IGNORECASE)


def scan_source(source_dir: Path) -> list[SourceFile]:
    """
    Discover all .mkv files matching the MakeMKV naming convention.
    """
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        raise NotADirectoryError(
            f"Source path is not a directory: {source_dir}"
        )

    candidates: list[tuple[int, Path]] = []
    
    # Loop through source dir
    for path in source_dir.iterdir():
        if path.is_dir():
            continue
            
        match = _FILE_PATTERN.search(path.name)
        if not match:
            continue
        
        # Extract disc index and add to candidates list
        candidates.append((int(match.group(1)), path))

    # Sort candidates by disc index
    candidates.sort(key=lambda item: item[0])

    # Align episode idx with global 
    return [
        SourceFile(
            path=path, 
            stem=path.stem, 
            index=idx
        )
        for idx, (_, path) in enumerate(candidates)
    ]
