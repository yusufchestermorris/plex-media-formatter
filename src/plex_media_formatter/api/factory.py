from plex_media_formatter.config import settings
from plex_media_formatter.api.base import ApiClient
from plex_media_formatter.api.jikan import JikanClient
from plex_media_formatter.api.tmdb import TmdbClient


def get_api_client(name: str = None) -> ApiClient:
    mapping = {
        "tmdb": TmdbClient,
        "jikan": JikanClient,
    }
    name = name if name is not None else settings.api_client

    
    client_cls = mapping.get(name, None)
    if client_cls is None:
        raise ValueError(
            f"Invalid API client name: {name}"
        )
        
    return client_cls(
        api_url=settings.api_url,
        api_key=settings.api_key,
        api_token=settings.api_token,
    )   
    