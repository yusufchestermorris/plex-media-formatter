from __future__ import annotations

from pathlib import Path

import pytest

from plex_media_formatter.core.offset import (
    detect_episode_offset,
    get_season_output_dir,
    resolve_episode_offset,
)


def test_get_season_output_dir_builds_expected_path(tmp_path: Path) -> None:
    result = get_season_output_dir(
        plex_library_root=tmp_path,
        series_title="Cowboy Bebop",
        year=1998,
        season=1,
    )

    assert result == tmp_path / "Cowboy Bebop (1998)" / "Season 01"


def test_detect_episode_offset_returns_none_when_season_dir_missing(tmp_path: Path) -> None:
    result = detect_episode_offset(
        plex_library_root=tmp_path,
        series_title="Cowboy Bebop",
        year=1998,
        season=1,
    )

    assert result is None


def test_detect_episode_offset_returns_none_when_no_matching_files(tmp_path: Path) -> None:
    season_dir = tmp_path / "Cowboy Bebop (1998)" / "Season 01"
    season_dir.mkdir(parents=True)

    (season_dir / "notes.txt").write_text("hello")
    (season_dir / "poster.jpg").write_bytes(b"fake")
    (season_dir / "Cowboy Bebop (1998) - trailer.mkv").write_bytes(b"fake")

    result = detect_episode_offset(
        plex_library_root=tmp_path,
        series_title="Cowboy Bebop",
        year=1998,
        season=1,
    )

    assert result is None


def test_detect_episode_offset_returns_highest_episode_for_matching_season(tmp_path: Path) -> None:
    season_dir = tmp_path / "Cowboy Bebop (1998)" / "Season 01"
    season_dir.mkdir(parents=True)

    (season_dir / "Cowboy Bebop (1998) - S01E01 - Asteroid Blues.mkv").write_bytes(b"fake")
    (season_dir / "Cowboy Bebop (1998) - S01E02 - Stray Dog Strut.mkv").write_bytes(b"fake")
    (season_dir / "Cowboy Bebop (1998) - S01E10 - Ganymede Elegy.mkv").write_bytes(b"fake")

    result = detect_episode_offset(
        plex_library_root=tmp_path,
        series_title="Cowboy Bebop",
        year=1998,
        season=1,
    )

    assert result == 10


def test_detect_episode_offset_ignores_files_for_other_seasons(tmp_path: Path) -> None:
    season_dir = tmp_path / "Cowboy Bebop (1998)" / "Season 01"
    season_dir.mkdir(parents=True)

    (season_dir / "Cowboy Bebop (1998) - S02E99 - Wrong Season.mkv").write_bytes(b"fake")
    (season_dir / "Cowboy Bebop (1998) - S01E03 - Honky Tonk Women.mkv").write_bytes(b"fake")

    result = detect_episode_offset(
        plex_library_root=tmp_path,
        series_title="Cowboy Bebop",
        year=1998,
        season=1,
    )

    assert result == 3


def test_detect_episode_offset_handles_mixed_extensions(tmp_path: Path) -> None:
    season_dir = tmp_path / "Cowboy Bebop (1998)" / "Season 01"
    season_dir.mkdir(parents=True)

    (season_dir / "Cowboy Bebop (1998) - S01E04 - Gateway Shuffle.mp4").write_bytes(b"fake")
    (season_dir / "Cowboy Bebop (1998) - S01E07 - Heavy Metal Queen.mkv").write_bytes(b"fake")
    (season_dir / "Cowboy Bebop (1998) - S01E05 - Ballad of Fallen Angels.avi").write_bytes(b"fake")

    result = detect_episode_offset(
        plex_library_root=tmp_path,
        series_title="Cowboy Bebop",
        year=1998,
        season=1,
    )

    assert result == 7


def test_resolve_episode_offset_prefers_explicit_user_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from plex_media_formatter.config import settings

    monkeypatch.setattr(settings, "plex_library_root", str(tmp_path))

    season_dir = tmp_path / "Cowboy Bebop (1998)" / "Season 01"
    season_dir.mkdir(parents=True)
    (season_dir / "Cowboy Bebop (1998) - S01E12 - Jupiter Jazz.mkv").write_bytes(b"fake")

    result = resolve_episode_offset(
        series_title="Cowboy Bebop",
        year=1998,
        season=1,
        user_offset=4,
    )

    assert result == 4


def test_resolve_episode_offset_uses_detected_value_when_user_offset_is_none(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from plex_media_formatter.config import settings

    monkeypatch.setattr(settings, "plex_library_root", str(tmp_path))

    season_dir = tmp_path / "Cowboy Bebop (1998)" / "Season 01"
    season_dir.mkdir(parents=True)
    (season_dir / "Cowboy Bebop (1998) - S01E12 - Jupiter Jazz.mkv").write_bytes(b"fake")

    result = resolve_episode_offset(
        series_title="Cowboy Bebop",
        year=1998,
        season=1,
        user_offset=None,
    )

    assert result == 12


def test_resolve_episode_offset_defaults_to_zero_when_no_user_or_detected_value(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from plex_media_formatter.config import settings

    monkeypatch.setattr(settings, "plex_library_root", str(tmp_path))

    result = resolve_episode_offset(
        series_title="Cowboy Bebop",
        year=1998,
        season=1,
        user_offset=None,
    )

    assert result == 0


@pytest.mark.parametrize(
    ("filenames", "expected"),
    [
        (["Show (2024) - S01E01 - One.mkv"], 1),
        (["Show (2024) - S01E09 - Nine.mkv", "Show (2024) - S01E10 - Ten.mkv"], 10),
        (["Show (2024) - S01E001 - One.mkv", "Show (2024) - S01E012 - Twelve.mkv"], 12),
    ],
)
def test_detect_episode_offset_parametrized_cases(
    tmp_path: Path,
    filenames: list[str],
    expected: int,
) -> None:
    season_dir = tmp_path / "Show (2024)" / "Season 01"
    season_dir.mkdir(parents=True)

    for name in filenames:
        (season_dir / name).write_bytes(b"fake")

    result = detect_episode_offset(
        plex_library_root=tmp_path,
        series_title="Show",
        year=2024,
        season=1,
    )

    assert result == expected


if __name__ == "__main__":
    pytest.main([__file__])
