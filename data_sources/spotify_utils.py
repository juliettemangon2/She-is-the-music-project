import os
import requests
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

TOKEN_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"
ARTIST_URL = "https://api.spotify.com/v1/artists"
ALBUM_URL = "https://api.spotify.com/v1/albums"

def _get_spotify_token() -> str:
    """Retrieve Spotify API token using Client Credentials Flow."""
    response = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=10
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_spotify_metadata(artist: str, title: str) -> dict:
    """Fetch metadata for a given track and artist from Spotify."""
    token = _get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Search for the track
    query = f'track:"{title}" artist:"{artist}"'
    params = {"q": query, "type": "track", "limit": 1}
    response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10)
    if not response.ok:
        return {}

    data = response.json()
    items = data.get("tracks", {}).get("items", [])
    if not items:
        return {}

    track = items[0]
    album = track.get("album", {})
    album_id = album.get("id")

    # Step 2: Fetch full album details for label & copyrights
    album_label = None
    copyrights_raw = []
    if album_id:
        album_resp = requests.get(f"{ALBUM_URL}/{album_id}", headers=headers, timeout=10)
        if album_resp.ok:
            album_data = album_resp.json()
            album_label = album_data.get("label")
            copyrights_raw = album_data.get("copyrights", [])

    # Extract release date details
    release_date = album.get("release_date", "")
    release_precision = album.get("release_date_precision", "")
    release_year = int(release_date.split("-")[0]) if release_date else None

    # Step 3: Fetch artist details
    artist_data = {}
    if track.get("artists"):
        artist_id = track["artists"][0]["id"]
        artist_resp = requests.get(f"{ARTIST_URL}/{artist_id}", headers=headers, timeout=10)
        if artist_resp.ok:
            artist_info = artist_resp.json()
            artist_data = {
                "name": artist_info.get("name"),
                "followers": artist_info.get("followers", {}).get("total"),
                "popularity": artist_info.get("popularity"),
                "genres": artist_info.get("genres", [])
            }

    # Step 4: Additional track info
    isrc = track.get("external_ids", {}).get("isrc")
    track_popularity = track.get("popularity")

    # Step 5: Structure copyrights
    copyright_composition = [c["text"] for c in copyrights_raw if c.get("type") == "C"]
    copyright_sound_recording = [c["text"] for c in copyrights_raw if c.get("type") == "P"]

    # Final combined metadata
    return {
        "spotify_id": track.get("id"),
        "name": track.get("name"),
        "isrc": isrc,
        "track_popularity": track_popularity,
        "artist": artist_data.get("name", artist),
        "artist_followers": artist_data.get("followers"),
        "artist_popularity": artist_data.get("popularity"),
        "artist_genres": artist_data.get("genres"),
        "album_name": album.get("name"),
        "label": album_label,
        "release_date": release_date,
        "release_date_precision": release_precision,
        "release_year": release_year,
        "copyrights": copyrights_raw,  # original array
        "copyright_composition": copyright_composition,
        "copyright_sound_recording": copyright_sound_recording
    }

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) != 3:
        print("Usage: python spotify_utils.py \"Artist\" \"Song Title\"")
        sys.exit(1)

    artist, title = sys.argv[1], sys.argv[2]
    metadata = get_spotify_metadata(artist, title)
    print(json.dumps(metadata, indent=2))
