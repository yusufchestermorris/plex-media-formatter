import shutil
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from plex_media_formatter.core.models import FileOperation, Manifest, OperationType, ExecutionState


def _move_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))


def _revert_file(source: Path, destination: Path) -> None:
    """
    For revert, caller passes (destination_path, source_path) so the
    signature stays (source, destination) throughout - no special casing.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))


def _prune_empty_dirs(dirs: set[Path]) -> None:
    for d in sorted(dirs, key=lambda p: len(p.parts), reverse=True):
        try:
            if d.exists() and not any(d.iterdir()):
                d.rmdir()
        except OSError:
            pass


PathSelector = Callable[[FileOperation], Path]

_SRC: PathSelector = lambda op: op.source_path
_DST: PathSelector = lambda op: op.destination_path

TaskFn = Callable[[Path, Path], None]

_TASK_REGISTRY: dict[OperationType, tuple[PathSelector, PathSelector, TaskFn]] = {
    OperationType.MOVE:   (_SRC, _DST, _move_file),
    OperationType.REVERT: (_DST, _SRC, _revert_file),  # paths intentionally swapped
}


def execute_operations(
    manifest: Manifest,
    max_workers: int = 4,
    callback: Callable[[FileOperation], None] | None = None,
) -> None:
    """
    Dispatch each FileOperations in the manifest.
    """
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        operation_futures: list[tuple[FileOperation, Future[None]]] = []

        for op in manifest.operations:
            src_sel, dst_sel, task_fn = _TASK_REGISTRY[op.execution.type]
            op.execution.start()
            future = pool.submit(task_fn, src_sel(op), dst_sel(op))
            operation_futures.append((op, future))

        for op, future in operation_futures:
            try:
                future.result()
                op.execution.complete()
                
            except Exception as exc:
                op.execution.fail(exc)
                
            finally:
                if callback:
                    callback(op)

    if any(
        op.execution.type == OperationType.REVERT 
        for op in manifest.operations
    ):
        completed_dests = {
            op.destination_path
            for op in manifest.operations
            if op.execution.state == ExecutionState.COMPLETED
        }
        _prune_empty_dirs({p.parent for p in completed_dests})

    failed = [
        op 
        for op in manifest.operations 
        if op.execution.state == ExecutionState.FAILED
    ]
    if failed:
        lines = [
            f"  [{op.episode}] {op.plex_filename}: {op.execution.error}" 
            for op in failed
        ]
        raise RuntimeError(
            f"{len(failed)} operation(s) failed:\n" + "\n".join(lines)
        )
    