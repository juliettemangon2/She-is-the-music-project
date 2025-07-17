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
    for track in release.get("tracklist", []):
        if song_title.lower() in track.get("title", "").lower() and track.get("extraartists"):
            for artist_entry in track["extraartists"]:
                credits.append(Credit(
                    name=artist_entry.get("name", "").strip(),
                    role=artist_entry.get("role", "").strip()
                ))

    for artist_entry in release.get("extraartists", []):
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
