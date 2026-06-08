"""
Schema definitions for core data structures.
"""
from enum import StrEnum
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, computed_field


PLEX_FILENAME = (
    "{series_title} ({year}) - "
    "S{season:02d}E{episode:02d} - "
    "{episode_title}{extension}"
)


class ExecutionState(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class OperationType(StrEnum):
    MOVE = "move"
    REVERT = "revert"


class SeriesInfo(BaseModel):
    series_id: int
    title: str
    year: int


class EpisodeInfo(BaseModel):
    season: int
    episode: int
    title: str


class SourceFile(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    stem: str
    index: int


class Execution(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    type: OperationType
    state: ExecutionState = Field(ExecutionState.PENDING)
    error: Exception | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @field_serializer("error")
    def serialise_error(self, error: Exception | None) -> dict[str, str] | None:
        if error is None:
            return None
        return {
            "type": type(error).__name__,
            "message": str(error),
        }

    def start(self) -> None:
        self.state = ExecutionState.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        self.state = ExecutionState.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, exc: Exception) -> None:
        self.state = ExecutionState.FAILED
        self.error = exc
        self.completed_at = datetime.now(timezone.utc)

    @computed_field
    @property
    def elapsed_seconds(self) -> float | None:
        if self.started_at is None:
            return None
        
        end = self.completed_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()


class FileOperation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_path: Path
    destination_path: Path
    series_title: str
    year: int
    season: int
    episode: int
    episode_title: str
    index_offset: int = 0

    execution: Execution = Field(
        default_factory=lambda: Execution(type=OperationType.MOVE)
    )

    @property
    def plex_filename(self) -> str:
        extension = self.source_path.suffix
        title = self.episode_title.replace("/", "-").replace(":", " -")
        return PLEX_FILENAME.format(
            series_title=self.series_title,
            year=self.year,
            season=self.season,
            episode=self.episode,
            episode_title=title,
            extension=extension,
        )


class Manifest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    series_title: str
    year: int
    api_source: str
    operations: list[FileOperation]
    executed: bool = False

    @computed_field
    @property
    def total_operations(self) -> int:
        return len(self.operations)

    @computed_field
    @property
    def pending_operations(self) -> int:
        return sum(1 for op in self.operations if op.execution.state == ExecutionState.PENDING)

    @computed_field
    @property
    def in_progress_operations(self) -> int:
        return sum(1 for op in self.operations if op.execution.state == ExecutionState.IN_PROGRESS)

    @computed_field
    @property
    def completed_operations(self) -> int:
        return sum(1 for op in self.operations if op.execution.state == ExecutionState.COMPLETED)

    @computed_field
    @property
    def failed_operations(self) -> int:
        return sum(1 for op in self.operations if op.execution.state == ExecutionState.FAILED)

    @computed_field
    @property
    def progress_pct(self) -> float:
        if self.total_operations == 0:
            return 0.0
        
        resolved = self.completed_operations + self.failed_operations
        return round((resolved / self.total_operations) * 100, 1)

    @computed_field
    @property
    def has_failures(self) -> bool:
        return self.failed_operations > 0

    @computed_field
    @property
    def elapsed_seconds(self) -> float | None:
        started = [
            op.execution.started_at
            for op in self.operations
            if op.execution.started_at is not None
        ]
        if not started:
            return None
        
        end_times = [
            op.execution.completed_at
            for op in self.operations
            if op.execution.completed_at is not None
        ]
        end = max(end_times) if len(end_times) == len(self.operations) else datetime.now(timezone.utc)
        return (end - min(started)).total_seconds()

    def status_summary(self) -> dict[str, Any]:
        return {
            "series": f"{self.series_title} ({self.year})",
            "api_source": self.api_source,
            "total": self.total_operations,
            "pending": self.pending_operations,
            "in_progress": self.in_progress_operations,
            "completed": self.completed_operations,
            "failed": self.failed_operations,
            "progress_pct": self.progress_pct,
            "elapsed_s": self.elapsed_seconds,
            "has_failures": self.has_failures,
        }
