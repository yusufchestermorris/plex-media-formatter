import httpx
import asyncio
from plex_media_formatter.core.models import EpisodeInfo, SeriesInfo
from plex_media_formatter.api.base import ApiClient


class JikanClient(ApiClient):
    default_url = "https://api.jikan.moe/v4"
    
    def __init__(self, api_url: str = None, api_key: str = None, api_token: str = None) -> None:
        url = api_url or self.default_url
        self.api_url = url.rstrip("/")
        
         # Interface consistency placeholders
        self.api_key = None
        self.api_token = None

    async def fetch_series_info(self, title: str, **kwargs) -> SeriesInfo:
        url = f"{self.api_url}/anime"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"q": title, "limit": 1})
            response.raise_for_status()
            
            results = response.json().get("data", [])
            if not results:
                raise ValueError(f"No results found for title: {title}")
            
            series = results[0]
            year = series.get("year")
            year = int(year) if year else 0
            
            return SeriesInfo(
                series_id=series["mal_id"],
                title=series.get("title_english") or series["title"],
                year=year
            )

    async def fetch_episodes(self, series_id: int, season: int, **kwargs) -> list[EpisodeInfo]:
        """
        Jikan lacks discrete season endpoints; episodes are fetched from
        pagination. Season number is used only for the output path.
        """
        url = f"{self.api_url}/anime/{series_id}/episodes"
        
        all_episodes: list[EpisodeInfo] = []
        page = 1
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(url, params={"page": page},)
                if response.status_code == 429:
                    await asyncio.sleep(2)
                    continue
                
                response.raise_for_status()
                payload = response.json()
                episodes = payload.get("data", [])
                
                if not episodes and page == 1:
                    raise ValueError(
                        f"No episodes found for series ID {series_id} season {season}"
                    )
                
                for idx, episode in enumerate(episodes, start=1):
                    episode_number = episode.get("mal_id") or ((page -1) * 100 + idx)
                    title = episode.get("title") or f"Episode {episode_number}"
                    
                    all_episodes.append(
                        EpisodeInfo(
                            season=season,
                            episode=episode_number,
                            title=title,
                    ))
                
                pagination = payload.get("pagination", {})
                has_next_page = pagination.get("has_next_page", False)    
                if not has_next_page:
                    break
                
                await asyncio.sleep(1)  # be nice to the API
                page += 1
                
        return episodes
