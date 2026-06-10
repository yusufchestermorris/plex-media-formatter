import re
import httpx
from plex_media_formatter.core.models import EpisodeInfo, SeriesInfo
from plex_media_formatter.api.base import ApiClient

_SEPARATOR_PATTERN = re.compile(r';\s+')
_SANITIZER_PATTERN = re.compile(r'^\b(?:SA|C|DI|DU|IN)\b(?!-)\s*:?\s*', flags=re.IGNORECASE)


def clean_title(raw: str) -> str:
    """
    Cleans TMDB metadata prefixes and redundant subtitle noise.
    """
    if not raw:
        return ""
        
    clean = _SANITIZER_PATTERN.sub('', raw)
    
    if ";" in clean:
        if _SEPARATOR_PATTERN.search(clean) or _SANITIZER_PATTERN.match(raw):
            clean = clean.split(";")[0]
            
    return clean.strip()


class TmdbClient(ApiClient):
    default_url = "https://api.themoviedb.org/3"

    def __init__(self, api_url: str = None, api_key: str = None, api_token: str = None) -> None:
        if api_key is None and api_token is None:
            raise ValueError("TMDb API key or token is required")
        
        url = api_url or self.default_url
        
        self.api_url = url.rstrip("/")
        self._headers = {}
        self._params = {}
        
        if api_key is not None:
            self._params = {"api_key": api_key}
        if api_token is not None:
            self._headers = {"Authorization": f"Bearer {api_token}"}
        
    async def fetch_series_info(self, title: str, **kwargs) -> SeriesInfo:
        url = f"{self.api_url}/search/tv"
        params = self._params.copy()
        params["query"] = title
        
        async with httpx.AsyncClient(headers=self._headers) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
            
            if not results:
                raise ValueError(f"No results found for title: {title}")
            
            series = results[0]
            year = series.get("first_air_date")
            year = int(year[:4]) if year else 0
            
            return SeriesInfo(
                series_id=series["id"],
                title=series["name"],
                year=year
            )

    async def fetch_episodes(self, series_id: int, season: int, clean: bool = False, **kwargs) -> list[EpisodeInfo]:
        url = f"{self.api_url}/tv/{series_id}/season/{season}"
        params = self._params.copy()

        async with httpx.AsyncClient(headers=self._headers) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            episodes = response.json().get("episodes", [])
            if not episodes:
                raise ValueError(
                    f"No episodes found for series ID {series_id} season {season}"
                )
            
            return [
                EpisodeInfo(
                    season=season, 
                    episode=episode["episode_number"], 
                    title=clean_title(episode["name"]) if clean else episode["name"]
                )
                for episode in episodes
            ]
