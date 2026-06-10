from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_source(tmp_path: Path) -> Path:
    for i in range(5):
        (tmp_path / f"title_t{i:02d}.mkv").write_bytes(b"fake mkv")
    return tmp_path


@pytest.fixture
def series_info():
    from plex_media_formatter.core.models import SeriesInfo
    return SeriesInfo(series_id=123, title="Cowboy Bebop", year=1998)


@pytest.fixture
def episodes():
    from plex_media_formatter.core.models import EpisodeInfo
    return [
        EpisodeInfo(season=1, episode=i + 1, title=f"Session {i + 1}")
        for i in range(10)
    ]


@pytest.fixture(params=[
    # --- Ghost in the Shell S.A.C. Edge Cases ---
    ("SA The Fortunate Ones; MISSING HEARTS", "The Fortunate Ones"),
    ("C The Man Who Lurks in the Darkness of the Net; CHAT! CHAT! CHAT!", "The Man Who Lurks in the Darkness of the Net"),
    ("SA A Perfect Day for a Jungle Cruise; JUNGLE CRUISE", "A Perfect Day for a Jungle Cruise"),
    ("SA Automated Capitalism; ¥€$", "Automated Capitalism"),
    ("DI: Re-view; RE-VIEW", "Re-view"),
    
    # --- SciADV Visual Novel Franchise Edge Cases (Must preserve internal semicolon) ---
    ("Steins;Gate", "Steins;Gate"),
    ("Robotics;Notes", "Robotics;Notes"),
    ("Occultic;Nine", "Occultic;Nine"),
    
    # --- False-Positive Prefix Boundary Edge Cases ---
    ("Captain America", "Captain America"),      # Starts with 'C' but is a single word
    ("Inside Out", "Inside Out"),                # Starts with 'IN' but is a single word
    ("Digital Monster", "Digital Monster"),      # Starts with 'DI' but is a single word
    
    # --- General Boundary Edge Cases ---
    ("Normal Title Without Special Tokens", "Normal Title Without Special Tokens"),
    ("", ""),
    (None, ""),
])
def title_cleaning_case(request) -> tuple[str | None, str]:
    """Provides a tuple of (raw_tmdb_title, expected_cleaned_title)."""
    return request.param
