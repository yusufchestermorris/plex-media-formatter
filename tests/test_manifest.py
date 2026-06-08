from __future__ import annotations

from __future__ import annotations

from pathlib import Path

import pytest

from plex_media_formatter.core.manifest import read_manifest, write_manifest
from plex_media_formatter.core.models import Execution, ExecutionState, FileOperation, Manifest, OperationType


def _manifest(tmp_path: Path) -> Manifest:
    src = tmp_path / "title_t00.mkv"
    dst = tmp_path / "dest" / "Show (2024) - S01E01 - Ep.mkv"
    op = FileOperation(
        source_path=src,
        destination_path=dst,
        series_title="Show",
        year=2024,
        season=1,
        episode=1,
        episode_title="Ep",
        execution=Execution(type=OperationType.MOVE),
    )
    return Manifest(series_title="Show", year=2024, api_source="tmdb", operations=[op])


def test_round_trip(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    path = tmp_path / "manifest.json"
    write_manifest(manifest, path)

    loaded = read_manifest(path)
    assert loaded.series_title == "Show"
    assert loaded.api_source == "tmdb"
    assert loaded.total_operations == 1


def test_computed_fields_reflect_operation_state(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    manifest.operations[0].execution.state = ExecutionState.COMPLETED

    assert manifest.completed_operations == 1
    assert manifest.pending_operations == 0
    assert manifest.failed_operations == 0


def test_atomic_write_creates_file(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    path = tmp_path / "sub" / "manifest.json"
    write_manifest(manifest, path)
    assert path.exists()


if __name__ == "__main__":
    pytest.main([__file__])
