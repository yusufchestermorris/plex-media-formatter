"""Helpers for storing and resolving the latest manifest pointer."""
from __future__ import annotations

from pathlib import Path


def write_latest_manifest_pointer(pointer_path: Path, manifest_path: Path) -> None:
    """
    Persist the absolute path to the most recently written manifest.

    The pointer file is a convenience index only. The manifest JSON remains the
    canonical execution record.
    """
    pointer_path = Path(pointer_path)
    manifest_path = Path(manifest_path).resolve()

    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    pointer_path.write_text(f"{manifest_path}\n", encoding="utf-8")


def read_latest_manifest_pointer(pointer_path: Path) -> Path:
    """
    Read the latest manifest pointer and return the resolved manifest path.

    Raises:
        FileNotFoundError: if the pointer file does not exist
        ValueError: if the pointer file is empty
        FileNotFoundError: if the pointed manifest path does not exist
    """
    pointer_path = Path(pointer_path)

    if not pointer_path.exists():
        raise FileNotFoundError(
            f"No latest manifest pointer found at: {pointer_path}"
        )

    raw = pointer_path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError(
            f"Latest manifest pointer file is empty: {pointer_path}"
        )

    manifest_path = Path(raw)
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Latest manifest pointer exists, but manifest was not found: {manifest_path}"
        )

    return manifest_path


def resolve_manifest_path(
    manifest_path: Path | None,
    latest_manifest_path: Path,
) -> Path:
    """
    Resolve the manifest path for commands such as `revert`.

    Precedence:
    1. Explicit manifest path argument
    2. Latest manifest pointer file
    """
    if manifest_path is not None:
        return Path(manifest_path)

    return read_latest_manifest_pointer(latest_manifest_path)