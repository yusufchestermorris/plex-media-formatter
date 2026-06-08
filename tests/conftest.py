from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_source(tmp_path: Path) -> Path:
    for i in range(5):
        (tmp_path / f"title_t{i:02d}.mkv").write_bytes(b"fake mkv")
    return tmp_path


@pytest.fixture
def series_info():
    from plex_media_formatter.core.models import SeriesInfo
    return SeriesInfo(series_id=123, title="Cowboy Bebop", year=1998)


@pytest.fixture
def episodes():
    from plex_media_formatter.core.models import EpisodeInfo
    return [
        EpisodeInfo(season=1, episode=i + 1, title=f"Session {i + 1}")
        for i in range(10)
    ]
