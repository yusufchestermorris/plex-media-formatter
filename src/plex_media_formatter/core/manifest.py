"""
Manifest I/O layer.
Writes atomically (write-to-temp + os.replace) so a crash mid-write
never leaves a corrupt state file.
"""
import os
import tempfile
from pathlib import Path

from plex_media_formatter.core.models import Manifest


def write_manifest(manifest: Manifest, path: Path) -> None:
    """Atomic write: temp file → fsync → os.replace."""
    data = manifest.model_dump_json(indent=2)
    _dir = path.parent
    _dir.mkdir(parents=True, exist_ok=True)

    fd, tmp = tempfile.mkstemp(dir=_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
            
        os.replace(tmp, path)
        
    except Exception:
        os.unlink(tmp)
        raise


def read_manifest(path: Path) -> Manifest:
    if not path.exists():
        raise FileNotFoundError(f"No manifest found at {path}")
    
    return Manifest.model_validate_json(path.read_text())
