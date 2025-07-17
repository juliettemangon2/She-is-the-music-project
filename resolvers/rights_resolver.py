from __future__ import annotations
from typing import Any, Dict, List, Optional
from copyright_utils import estimate_copyright_status
from data_sources.rightsholders_utils import get_rightsholders


def resolve_rights(
    spotify_track: Dict[str, Any],
    release_year: int,
    author_death_year: Optional[int],
    rightsholders: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Resolves the full rights profile for a song.

    Args:
        spotify_track: Raw Spotify track JSON.
        release_year: Year the song was first published.
        author_death_year: Last author's death year, if known.
        rightsholders: Optional list of rightsholder dicts with:
            - name: str
            - role: str (e.g., songwriter, publisher)
            - affiliation: str (e.g., ASCAP, BMI)
            - territory: str (e.g., US, UK)

    Returns:
        A dictionary containing:
            - copyright_summary
            - publishers
            - songwriters
            - rightsholders (as provided)
    """
    copyright_summary = estimate_copyright_status(
        spotify_track=spotify_track,
        release_year=release_year,
        author_death_year=author_death_year
    )

    publishers: List[Dict[str, Any]] = []
    songwriters: List[Dict[str, Any]] = []

    if rightsholders:
        for rh in rightsholders:
            role = rh.get("role", "").lower()
            if "publisher" in role:
                publishers.append(rh)
            elif "writer" in role or "songwriter" in role or "composer" in role:
                songwriters.append(rh)

    return {
        "copyright_summary": copyright_summary,
        "publishers": publishers,
        "songwriters": songwriters,
        "rightsholders": rightsholders or []
    }

if __name__ == "__main__":
    import json

    mock_track = {
        "name": "Test Song",
        "available_markets": ["US", "GB"],
        "restrictions": None
    }

    resolved = resolve_rights(
        spotify_track=mock_track,
        release_year=2000,
        author_death_year=None,
        rightsholders=[]
    )

    print(json.dumps(resolved, indent=2))
