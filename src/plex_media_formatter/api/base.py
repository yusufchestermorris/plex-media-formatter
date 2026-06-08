"""
Abstract API client - any concrete engine must satisfy this Protocol.
Decouples the execution engine from the upstream data source.
"""
from typing import Protocol, runtime_checkable

from plex_media_formatter.core.models import EpisodeInfo, SeriesInfo


@runtime_checkable
class ApiClient(Protocol):
    async def fetch_series_info(self, title: str) -> SeriesInfo: ...
    async def fetch_episodes(self, series_id: int, season: int) -> list[EpisodeInfo]: ...
