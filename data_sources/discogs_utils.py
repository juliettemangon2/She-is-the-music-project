import os
import requests
from dataclasses import dataclass, asdict
from typing import List
from dotenv import load_dotenv

load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_USER_TOKEN")
BASE_URL = "https://api.discogs.com"

@dataclass(slots=True, frozen=True)
class Credit:
    name: str
    role: str
    source: str = "discogs"
    scope: str = "album"  # default to album-level unless marked track

def _discogs_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Discogs token={DISCOGS_TOKEN}",
        "User-Agent": "SITMApp/0.1"
    })
    return session

def get_discogs_metadata(artist: str, song_title: str) -> dict:
    """
    Fetch Discogs metadata for a track including contributors (with scope), album info, legal info, and identifiers.
    """
    session = _discogs_session()
    params = {"q": f"{artist} {song_title}", "type": "release", "per_page": 1}
    resp = session.get(f"{BASE_URL}/database/search", params=params, timeout=10)
    if not resp.ok:
        return {}

    results = resp.json().get("results", [])
    if not results:
        return {}

    release_id = results[0].get("id")
    release_resp = session.get(f"{BASE_URL}/releases/{release_id}", timeout=10)
    if not release_resp.ok:
        return {}

    release = release_resp.json()
    contributors = []
    seen = set()

    # Track-level contributors
    for track in release.get("tracklist", []):
        if song_title.lower() in track.get("title", "").lower() and track.get("extraartists"):
            for artist_entry in track["extraartists"]:
                key = (artist_entry.get("name", "").strip().lower(), artist_entry.get("role", "").strip().lower())
                if key not in seen:
                    seen.add(key)
                    contributors.append(Credit(
                        name=artist_entry.get("name", "").strip(),
                        role=artist_entry.get("role", "").strip(),
                        scope="track"
                    ))

    # Fallback: release-level contributors
    if not contributors:
        for artist_entry in release.get("extraartists", []):
            key = (artist_entry.get("name", "").strip().lower(), artist_entry.get("role", "").strip().lower())
            if key not in seen:
                seen.add(key)
                contributors.append(Credit(
                    name=artist_entry.get("name", "").strip(),
                    role=artist_entry.get("role", "").strip(),
                    scope="album"
                ))

    # Album-level info
    album_genres = release.get("genres", [])
    album_styles = release.get("styles", [])
    album_formats = [fmt.get("name") for fmt in release.get("formats", []) if "name" in fmt]

    # Release info
    release_country = release.get("country")
    release_year = release.get("year")
    if not release_year and release.get("released"):
        release_year = int(release["released"].split("-")[0])

    # Labels
    labels = [{"name": lbl.get("name"), "catno": lbl.get("catno")} for lbl in release.get("labels", [])]

    # Companies
    companies = [{"name": comp.get("name"), "role": comp.get("entity_type_name")} for comp in release.get("companies", [])]

    # Identifiers
    identifiers = [{"type": ident.get("type"), "value": ident.get("value")} for ident in release.get("identifiers", [])]

    # Legal info
    publishers = {comp.get("name") for comp in release.get("companies", []) if "published by" in comp.get("entity_type_name", "").lower()}

    # Fix: Parse companies for © and ℗ roles
    copyrights = [comp["name"] for comp in release.get("companies", []) if "copyright" in comp.get("entity_type_name", "").lower()]
    phonographic_rights = [comp["name"] for comp in release.get("companies", []) if "phonographic" in comp.get("entity_type_name", "").lower()]

    notes = release.get("notes", "")

    return {
        "contributors": [asdict(c) for c in contributors],
        "album_genres": album_genres,
        "album_styles": album_styles,
        "album_formats": album_formats,
        "release_country": release_country,
        "release_year": release_year,
        "labels": labels,
        "companies": companies,
        "identifiers": identifiers,
        "publishers": list(publishers),
        "copyrights": copyrights,
        "phonographic_rights": phonographic_rights,
        "notes": notes
    }

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) != 3:
        print("Usage: python discogs_utils.py \"Artist\" \"Song Title\"")
        sys.exit(1)

    artist, title = sys.argv[1], sys.argv[2]
    metadata = get_discogs_metadata(artist, title)
    print(json.dumps(metadata, indent=2))
