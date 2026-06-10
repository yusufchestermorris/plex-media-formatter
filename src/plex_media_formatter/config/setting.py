"""
Configuration settings:
loads from environment / .env. 

allows swap between api clients:
- TMDB
- Jikan
"""
from typing import Literal

from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_API_CLIENT = {"tmdb", "jikan"}


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    api_client: Literal["tmdb", "jikan"] = Field("jikan", alias="API_CLIENT")
    api_url: str | None = Field(None, alias="API_URL")
    api_key: str | None = Field(None, alias="API_KEY")
    api_token: str | None = Field(None, alias="API_TOKEN")

    plex_library_root: str = Field("/mnt/plex/media", alias="PLEX_LIBRARY_ROOT")
    
    manifest_path: str | None = Field(None, alias="MANIFEST_PATH")
    latest_manifest_path: str | None = Field(None, alias="LATEST_MANIFEST_PATH")

    @model_validator(mode="after")
    def check_token_required(self):
        if self.api_client not in _API_CLIENT:
            raise ValueError(f"Invalid API client. Must be one of {_API_CLIENT}")
        
        if self.api_client == "tmdb" and not (self.api_key or self.api_token):
            raise ValueError("API_KEY is required when API_CLIENT is 'tmdb'")
        
        return self
    
    @model_validator(mode="after")
    def set_default_api_url(self):
        if not self.api_url:
            if self.api_client == "tmdb":
                self.api_url = "https://api.themoviedb.org/3"
                
            elif self.api_client == "jikan":
                self.api_url = "https://api.jikan.moe/v4"
                
        return self
    
    @model_validator(mode="after")
    def set_default_manifest_path(self):
        if not self.manifest_path:
            self.manifest_path = str(Path(self.plex_library_root) / "manifest.json")
        if not self.latest_manifest_path:
            self.latest_manifest_path = str(Path(self.plex_library_root) / "latest_manifest.json")
                
        return self
        
settings = Settings()
