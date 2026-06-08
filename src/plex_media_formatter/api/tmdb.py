import httpx
from plex_media_formatter.core.models import EpisodeInfo, SeriesInfo
from plex_media_formatter.api.base import ApiClient


class TmdbClient(ApiClient):
    default_url = "https://api.themoviedb.org/3"

    def __init__(self, api_url: str = None, api_key: str = None) -> None:
        if api_key is None:
            raise ValueError("TMDb API key is required")
        
        self.api_url = api_url.rstrip("/") or self.default_url
        self._headers = {"Authorization": f"Bearer {api_key}"}

    async def fetch_series_info(self, title: str) -> SeriesInfo:
        url = f"{self.api_url}/search/tv"
        
        async with httpx.AsyncClient(headers=self._headers) as client:
            response = await client.get(url, params={"query": title})
            response.raise_for_status()
            series = response.json()["results"][0]
            return SeriesInfo(
                series_id=series["id"],
                title=series["name"],
                year=int(
                    series["first_air_date"][:4]
                ),
            )

    async def fetch_episodes(self, series_id: int, season: int) -> list[EpisodeInfo]:
        url = f"{self.api_url}/tv/{series_id}/season/{season}"
        
        async with httpx.AsyncClient(headers=self._headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return [
                EpisodeInfo(
                    season=season, 
                    episode=episode["episode_number"], 
                    title=episode["name"]
                )
                for episode in response.json()["episodes"]
            ]
