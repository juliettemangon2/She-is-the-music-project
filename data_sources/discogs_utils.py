from __future__ import annotations
import os
import requests
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_USER_TOKEN")
BASE_URL = "https://api.discogs.com"

@dataclass(slots=True, frozen=True)
class Credit:
    name: str
    role: str
    source: str = "discogs"

def _discogs_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Discogs token={DISCOGS_TOKEN}",
        "User-Agent": "SITMApp/0.1"
    })
    return session

def get_discogs_credits(artist: str, song_title: str) -> List[Credit]:
    session = _discogs_session()
    params = {"q": f"{artist} {song_title}", "type": "release", "per_page": 1}
    resp = session.get(f"{BASE_URL}/database/search", params=params, timeout=10)
    if not resp.ok:
        return []
    results = resp.json().get("results", [])
    if not results:
        return []

    release_id = results[0].get("id")
    release_resp = session.get(f"{BASE_URL}/releases/{release_id}", timeout=10)
    if not release_resp.ok:
        return []
    release = release_resp.json()

    credits = []
    seen = set()

    # First, attempt to collect track-level credits
    for track in release.get("tracklist", []):
        if song_title.lower() in track.get("title", "").lower() and track.get("extraartists"):
            for artist_entry in track["extraartists"]:
                key = (artist_entry.get("name", "").strip().lower(), artist_entry.get("role", "").strip().lower())
                if key not in seen:
                    seen.add(key)
                    credits.append(Credit(
                        name=artist_entry.get("name", "").strip(),
                        role=artist_entry.get("role", "").strip()
                    ))

    # If no track-specific credits, fallback to release-level credits
    if not credits:
        for artist_entry in release.get("extraartists", []):
            key = (artist_entry.get("name", "").strip().lower(), artist_entry.get("role", "").strip().lower())
            if key not in seen:
                seen.add(key)
                credits.append(Credit(
                    name=artist_entry.get("name", "").strip(),
                    role=artist_entry.get("role", "").strip()
                ))

    return credits


def get_discogs_label(artist: str, title: str) -> Optional[str]:
    session = _discogs_session()
    params = {"q": f"{artist} {title}", "type": "release", "per_page": 1}
    resp = session.get(f"{BASE_URL}/database/search", params=params, timeout=10)
    if not resp.ok:
        return None
    results = resp.json().get("results", [])
    if not results:
        return None
    labels = results[0].get("label")
    return labels[0] if labels else None

def get_discogs_label_country(label_name: str) -> Optional[str]:
    """
    Attempts to find the country of a label by searching Discogs.

    Args:
        label_name: Name of the record label.

    Returns:
        Country string if found, else None.
    """
    if not label_name:
        return None

    session = _discogs_session()
    params = {"q": label_name, "type": "label", "per_page": 1}
    resp = session.get(f"{BASE_URL}/database/search", params=params, timeout=10)

    if not resp.ok:
        return None

    results = resp.json().get("results", [])
    if not results:
        return None

    return results[0].get("country")

def get_discogs_master_and_versions(artist: str, title: str) -> dict:
    """
    Given an artist and title, fetch the Discogs master release and its versions.

    Returns:
        {
            "master_title": str,
            "master_artist": str,
            "master_uri": str,
            "versions": List[Dict[str, str]]
        }
    """
    session = _discogs_session()
    search_params = {
        "q": f"{artist} {title}",
        "type": "release",
        "per_page": 1
    }
    search_resp = session.get(f"{BASE_URL}/database/search", params=search_params, timeout=10)
    if not search_resp.ok:
        return {}

    results = search_resp.json().get("results", [])
    if not results:
        return {}

    release = results[0]
    master_id = release.get("master_id")
    if not master_id:
        return {}

    # Get master release details
    master_resp = session.get(f"{BASE_URL}/masters/{master_id}", timeout=10)
    if not master_resp.ok:
        return {}

    master_data = master_resp.json()
    master_title = master_data.get("title")
    master_artist = master_data.get("artist")
    master_uri = f"https://www.discogs.com/master/{master_id}"

    # Get versions of the master release
    versions_resp = session.get(f"{BASE_URL}/masters/{master_id}/versions", timeout=10)
    if not versions_resp.ok:
        return {}

    versions_data = versions_resp.json()
    versions = []
    for version in versions_data.get("versions", []):
        versions.append({
            "title": version.get("title"),
            "artist": version.get("artist"),
            "uri": f"https://www.discogs.com/release/{version.get('id')}"
        })

    return {
        "master_title": master_title,
        "master_artist": master_artist,
        "master_uri": master_uri,
        "versions": versions
    }

def get_discogs_publishing_metadata(artist: str, song_title: str) -> dict:
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
    publishers = set()
    copyrights = []
    phonographic_rights = []

    # 1. Publishing credits usually reside in "companies"
    for company in release.get("companies", []):
        role = company.get("entity_type_name", "").lower()
        name = company.get("name", "")
        if "published by" in role:
            publishers.add(name)

    # 2. Copyright info
    for cr in release.get("extraartists", []):
        role = cr.get("role", "").lower()
        name = cr.get("name", "")
        if "copyright" in role:
            copyrights.append(f"{role.capitalize()}: {name}")
        elif "phonographic copyright" in role:
            phonographic_rights.append(f"{role.capitalize()}: {name}")

    # 3. Also, some releases store copyright in 'notes'
    notes = release.get('notes', '')

    return {
        "publishers": list(publishers),
        "copyrights": copyrights,
        "phonographic_rights": phonographic_rights,
        "notes": notes
    }


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 3:
        print("Usage: python discogs_utils.py \"Artist Name\" \"Song Title\"")
        sys.exit(1)

    artist, title = sys.argv[1], sys.argv[2]
    publishing_metadata = get_discogs_publishing_metadata(artist, title)
    print(json.dumps(publishing_metadata, indent=2))
