import os
import requests
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise RuntimeError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env")

TOKEN_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"

def _get_spotify_token() -> str:
    """Get Spotify access token via Client Credentials flow."""
    response = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=10
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_spotify_metadata(artist: str, title: str) -> dict:
    """
    Fetch Spotify metadata for a given artist and title.

    Returns:
        Dictionary containing Spotify metadata, including album label and release year.
    """
    token = _get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}

    query = f'track:"{title}" artist:"{artist}"'
    params = {
        "q": query,
        "type": "track",
        "limit": 1
    }

    response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10)
    if not response.ok:
        return {}

    data = response.json()
    items = data.get("tracks", {}).get("items", [])
    if not items:
        return {}

    track = items[0]
    album_info = track.get("album", {})
    release_date = album_info.get("release_date", "")
    release_year = None
    if release_date:
        try:
            release_year = int(release_date.split("-")[0])
        except ValueError:
            release_year = None

    track["release_year"] = release_year
    return track

if __name__ == "__main__":
    import sys, json

    if len(sys.argv) != 3:
        print("Usage: python spotify_utils.py \"Artist\" \"Song Title\"")
        sys.exit(1)

    artist, title = sys.argv[1], sys.argv[2]
    metadata = get_spotify_metadata(artist, title)
    print(json.dumps(metadata, indent=2))
