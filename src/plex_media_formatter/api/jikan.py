import httpx
import asyncio
from plex_media_formatter.core.models import EpisodeInfo, SeriesInfo
from plex_media_formatter.api.base import ApiClient


class JikanClient(ApiClient):
    default_url = "https://api.jikan.moe/v4"
    
    def __init__(self, api_url: str = None, api_key: str = None) -> None:
        self.api_url = api_url.rstrip("/") or self.default_url
        self.api_key = None # interface consistency

    async def fetch_series_info(self, title: str) -> SeriesInfo:
        url = f"{self.api_url}/anime"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"q": title, "limit": 1})
            response.raise_for_status()
            series = response.json()["data"][0]
            return SeriesInfo(
                series_id=series["mal_id"],
                title=series.get("title_english") or series["title"],
                year=(
                    int(series["year"]) 
                    if series["year"] 
                    else 0  
                ),
            )

    async def fetch_episodes(self, series_id: int, season: int) -> list[EpisodeInfo]:
        """
        Jikan lacks discrete season endpoints; episodes are fetched from
        pagination. Season number is used only for the output path.
        """
        url = f"{self.api_url}/anime/{series_id}/episodes"
        
        episodes: list[EpisodeInfo] = []
        page = 1
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(url, params={"page": page},)
                response.raise_for_status()
                
                body = response.json()
                for episode in body["data"]:
                    episodes.append(EpisodeInfo(
                        season=season,
                        episode=episode["mal_id"],
                        title=episode["title"] or f"Episode {episode['mal_id']}",
                    ))
                    
                if not body["pagination"]["has_next_page"]:
                    break
                
                await asyncio.sleep(1)  # be nice to the API
                page += 1
                
        return episodes
