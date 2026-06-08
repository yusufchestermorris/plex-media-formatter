from __future__ import annotations

from pathlib import Path

import pytest

from plex_media_formatter.core.execute import execute_operations
from plex_media_formatter.core.models import (
    Execution,
    ExecutionState,
    FileOperation,
    Manifest,
    OperationType,
)


def _operation(tmp_path: Path, name: str = "title_t00.mkv") -> FileOperation:
    src = tmp_path / name
    src.write_bytes(b"fake")
    dst = tmp_path / "dest" / "Show (2024) - S01E01 - Ep.mkv"
    return FileOperation(
        source_path=src,
        destination_path=dst,
        series_title="Show",
        year=2024,
        season=1,
        episode=1,
        episode_title="Ep",
        execution=Execution(type=OperationType.MOVE),
    )


def test_execute_moves_file_and_updates_state(tmp_path: Path) -> None:
    op = _operation(tmp_path)
    manifest = Manifest(series_title="Show", year=2024, api_source="tmdb", operations=[op])

    execute_operations(manifest)

    assert op.destination_path.exists()
    assert not op.source_path.exists()
    assert op.execution.state == ExecutionState.COMPLETED


def test_execute_records_failure_when_task_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    op = _operation(tmp_path)
    manifest = Manifest(series_title="Show", year=2024, api_source="tmdb", operations=[op])

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("plex_media_formatter.core.execute._move_file", boom)
    monkeypatch.setitem(
        __import__("plex_media_formatter.core.execute", fromlist=["_TASK_REGISTRY"])._TASK_REGISTRY,
        OperationType.MOVE,
        (
            __import__("plex_media_formatter.core.execute", fromlist=["_SRC"])._SRC,
            __import__("plex_media_formatter.core.execute", fromlist=["_DST"])._DST,
            boom,
        ),
    )

    with pytest.raises(RuntimeError, match="failed"):
        execute_operations(manifest)

    assert op.execution.state == ExecutionState.FAILED
    assert op.execution.error is not None


if __name__ == "__main__":
    pytest.main([__file__])
