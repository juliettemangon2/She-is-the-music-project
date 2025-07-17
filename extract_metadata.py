from __future__ import annotations
import os
from dataclasses import asdict, dataclass
from typing import Any, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter, Retry
from dotenv import load_dotenv
from data_sources.spotify_utils import get_spotify_client

load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_USER_TOKEN")
if not DISCOGS_TOKEN:
    raise RuntimeError("DISCOGS_USER_TOKEN is missing – set it in your .env file")

# ---------- HTTP session with retry/backoff for Discogs ---------------------

def _discogs_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Discogs token={DISCOGS_TOKEN}",
        "User-Agent": "SITMApp/0.1"
    })
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

# Shared Spotify client
_spotify = get_spotify_client()

@dataclass(slots=True, frozen=True)
class TrackMetadata:
    title: str
    artists: str
    album: str
    release_year: int
    track_id: str
    isrc: Optional[str]
    popularity: Optional[int]
    available_markets: List[str]

    def asdict(self) -> dict[str, Any]:
        return asdict(self)

# ---------- Discogs tag fetchers --------------------------------------------

def _discogs_release_id(query: str, session: requests.Session) -> Optional[int]:
    url = "https://api.discogs.com/database/search"
    resp = session.get(url, params={"q": query, "type": "release", "per_page": 1}, timeout=10)
    if not resp.ok:
        return None
    results = resp.json().get("results", [])
    if not results:
        return None
    return results[0].get("id")


def _iter_tags(release_id: int, session: requests.Session) -> List[str]:
    url = f"https://api.discogs.com/releases/{release_id}"
    resp = session.get(url, timeout=10)
    if not resp.ok:
        return []
    data = resp.json()
    tags = []
    for tag in data.get("styles", []) + data.get("genres", []):
        clean = tag.lower().strip()
        if clean:
            tags.append(clean)
    return tags


def _get_discogs_tags(song_title: str, artist_name: str) -> List[str]:
    session = _discogs_session()
    q = f"{artist_name} {song_title}"
    rid = _discogs_release_id(q, session)
    if rid is None:
        return []
    tags = _iter_tags(rid, session)
    return sorted(set(tags))

# ---------- Spotify track selector ------------------------------------------

def _pick_best_track(
    song_title: str,
    artist_name: str,
    market: Optional[str] = None,
    prefer_isrc: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    q = f'track:"{song_title}" artist:"{artist_name}"'
    result = _spotify.search(q=q, type="track", limit=10, market=market)
    items = result.get("tracks", {}).get("items", [])
    if not items:
        return None
    if prefer_isrc:
        for item in items:
            if item.get("external_ids", {}).get("isrc") == prefer_isrc.upper():
                return item
    # fallback: highest popularity
    items.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    return items[0]

# ---------- Public API ------------------------------------------------------

def get_song_metadata(
    song_title: str,
    artist_name: str,
    *,
    market: Optional[str] = None,
    prefer_isrc: Optional[str] = None,
) -> Tuple[Optional[TrackMetadata], List[str], Optional[dict[str, Any]]]:
    """
    Fetch track metadata from Spotify and genre/style tags from Discogs.

    Returns:
      - TrackMetadata or None if not found
      - List of tags (lowercase)
      - Raw Spotify track JSON
    """
    track = _pick_best_track(song_title, artist_name, market, prefer_isrc)
    if not track:
        return None, [], None

    markets = track.get("available_markets", [])
    metadata = TrackMetadata(
        title=track.get("name", ""),
        artists=", ".join(a.get("name", "") for a in track.get("artists", [])),
        album=track.get("album", {}).get("name", ""),
        release_year=int(track.get("album", {}).get("release_date", "0000").split("-")[0]),
        track_id=track.get("id", ""),
        isrc=track.get("external_ids", {}).get("isrc"),
        popularity=track.get("popularity"),
        available_markets=markets,
    )
    tags = _get_discogs_tags(song_title, artist_name)
    return metadata, tags, track

# ---------- CLI -------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    import sys, json
    if len(sys.argv) < 3:
        print("Usage: python extract_metadata.py \"Song Title\" \"Artist Name\"")
        sys.exit(1)
    md, tags, raw = get_song_metadata(sys.argv[1], sys.argv[2])
    print(json.dumps({"metadata": md.asdict() if md else None, "tags": tags}, indent=2))