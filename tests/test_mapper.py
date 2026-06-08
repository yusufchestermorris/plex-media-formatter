from __future__ import annotations

from pathlib import Path

import pytest

from plex_media_formatter.config import settings
from plex_media_formatter.core.mapper import compute_file_operation_map
from plex_media_formatter.core.models import EpisodeInfo, SeriesInfo, SourceFile


def _make_source_files(tmp_path: Path, n: int = 5) -> list[SourceFile]:
    out = []
    for i in range(n):
        p = tmp_path / f"title_t{i:02d}.mkv"
        p.write_bytes(b"fake")
        out.append(SourceFile(path=p, stem=p.stem, index=i))
        
    return out


def test_operation_count_matches_source_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "plex_library_root", str(tmp_path / "plex"))
    series = SeriesInfo(series_id=1, title="Cowboy Bebop", year=1998)
    episodes = [EpisodeInfo(season=1, episode=i + 1, title=f"Session {i + 1}") for i in range(10)]
    source_files = _make_source_files(tmp_path, 5)

    ops = compute_file_operation_map(source_files, episodes, series, season=1)
    assert len(ops) == 5


def test_plex_filename_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "plex_library_root", str(tmp_path / "plex"))
    series = SeriesInfo(series_id=1, title="Cowboy Bebop", year=1998)
    episodes = [EpisodeInfo(season=1, episode=1, title="Session 1")]
    source_files = _make_source_files(tmp_path, 1)

    ops = compute_file_operation_map(source_files, episodes, series, season=1)
    assert "S01E01" in ops[0].plex_filename
    assert ops[0].plex_filename.endswith(".mkv")


def test_episode_offset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "plex_library_root", str(tmp_path / "plex"))
    series = SeriesInfo(series_id=1, title="Show", year=2024)
    episodes = [EpisodeInfo(season=1, episode=i + 1, title=f"Ep {i + 1}") for i in range(10)]
    source_files = _make_source_files(tmp_path, 3)

    ops = compute_file_operation_map(source_files, episodes, series, season=1, episode_offset=3)
    assert [o.episode for o in ops] == [4, 5, 6]


def test_raises_on_length_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "plex_library_root", str(tmp_path / "plex"))
    series = SeriesInfo(series_id=1, title="Show", year=2024)
    episodes = [EpisodeInfo(season=1, episode=1, title="Ep 1")]
    source_files = _make_source_files(tmp_path, 2)

    with pytest.raises(ValueError, match="does not match"):
        compute_file_operation_map(source_files, episodes, series, season=1)


if __name__ == "__main__":
    pytest.main([__file__])
