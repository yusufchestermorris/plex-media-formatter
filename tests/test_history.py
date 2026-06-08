from __future__ import annotations

from pathlib import Path

import pytest

from plex_media_formatter.core.history import (
    read_latest_manifest_pointer,
    resolve_manifest_path,
    write_latest_manifest_pointer,
)


def test_write_latest_manifest_pointer_creates_parent_and_writes_absolute_path(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifests" / "format_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text('{"ok": true}', encoding="utf-8")

    pointer_path = tmp_path / "state" / "latest_manifest.txt"
    write_latest_manifest_pointer(pointer_path, manifest_path)

    assert pointer_path.exists()
    assert pointer_path.read_text(encoding="utf-8").strip() == str(manifest_path.resolve())


def test_read_latest_manifest_pointer_returns_manifest_path(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifests" / "format_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text('{"ok": true}', encoding="utf-8")

    pointer_path = tmp_path / "latest_manifest.txt"
    pointer_path.write_text(f"{manifest_path.resolve()}\n", encoding="utf-8")

    result = read_latest_manifest_pointer(pointer_path)

    assert result == manifest_path.resolve()


def test_read_latest_manifest_pointer_raises_when_pointer_missing(tmp_path: Path) -> None:
    pointer_path = tmp_path / "missing_latest_manifest.txt"

    with pytest.raises(FileNotFoundError, match="No latest manifest pointer found"):
        read_latest_manifest_pointer(pointer_path)


def test_read_latest_manifest_pointer_raises_when_pointer_empty(tmp_path: Path) -> None:
    pointer_path = tmp_path / "latest_manifest.txt"
    pointer_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="pointer file is empty"):
        read_latest_manifest_pointer(pointer_path)


def test_read_latest_manifest_pointer_raises_when_manifest_missing(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifests" / "format_manifest.json"
    pointer_path = tmp_path / "latest_manifest.txt"
    pointer_path.write_text(str(manifest_path.resolve()), encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="manifest was not found"):
        read_latest_manifest_pointer(pointer_path)


def test_resolve_manifest_path_prefers_explicit_manifest_path(tmp_path: Path) -> None:
    explicit_manifest = tmp_path / "explicit_manifest.json"
    explicit_manifest.write_text('{"ok": true}', encoding="utf-8")

    pointer_path = tmp_path / "latest_manifest.txt"

    result = resolve_manifest_path(
        manifest_path=explicit_manifest,
        latest_manifest_path=pointer_path,
    )

    assert result == explicit_manifest


def test_resolve_manifest_path_falls_back_to_latest_pointer(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifests" / "format_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text('{"ok": true}', encoding="utf-8")

    pointer_path = tmp_path / "latest_manifest.txt"
    write_latest_manifest_pointer(pointer_path, manifest_path)

    result = resolve_manifest_path(
        manifest_path=None,
        latest_manifest_path=pointer_path,
    )

    assert result == manifest_path.resolve()


if __name__ == "__main__":
    pytest.main([__file__])
