from __future__ import annotations

import pytest

from plex_media_formatter.api.tmdb import clean_title 


def test_clean_tmdb_title_formats(title_cleaning_case: tuple[str | None, str]) -> None:
    """Verifies that TMDB metadata prefixes and trailing subtitles are scrubbed cleanly."""
    raw_title, expected_output = title_cleaning_case
    assert clean_title(raw_title) == expected_output


def test_clean_tmdb_title_word_boundary_safety() -> None:
    """Ensures words starting with prefix letters aren't aggressively clipped."""
    assert clean_title("C-Control") == "C-Control"
    assert clean_title("SAO: Sword Art Online") == "SAO: Sword Art Online"


if __name__ == "__main__":
    pytest.main([__file__])
