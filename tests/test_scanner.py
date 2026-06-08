from __future__ import annotations

from pathlib import Path

import pytest

from plex_media_formatter.core.discovery import scan_source


def test_scan_returns_sorted_files(tmp_source: Path) -> None:
    files = scan_source(tmp_source)
    assert len(files) == 5
    assert [f.index for f in files] == list(range(5))
    assert [f.path.name for f in files] == [f"title_t{i:02d}.mkv" for i in range(5)]


def test_scan_ignores_non_matching_files(tmp_path: Path) -> None:
    (tmp_path / "random.mkv").write_bytes(b"x")
    (tmp_path / "title_t03.mkv").write_bytes(b"x")
    files = scan_source(tmp_path)
    assert len(files) == 1
    assert files[0].path.name == "title_t03.mkv"


def test_scan_raises_on_missing_dir(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        scan_source(tmp_path / "missing")


if __name__ == "__main__":
    pytest.main([__file__])
