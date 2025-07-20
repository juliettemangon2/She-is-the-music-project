# data_sources/musicbrainz_utils.py

import time
import requests
from typing import List, Dict, Any, Optional
from requests.adapters import HTTPAdapter, Retry
import logging

MB_API_BASE = "https://musicbrainz.org/ws/2"
USER_AGENT = "SITMApp/0.1 ( juliette.mangon@gmail.com )"
REQUEST_DELAY = 1.0

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

_session: Optional[requests.Session] = None

def _get_session() -> requests.Session:
    global _session
    if _session is None:
        session = requests.Session()
        session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        })
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        _session = session
    return _session


def _musicbrainz_get(endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    time.sleep(REQUEST_DELAY)
    url = f"{MB_API_BASE}/{endpoint}"
    resp = _get_session().get(url, params=params, timeout=10)
    if not resp.ok:
        logger.warning(f"MusicBrainz request failed: {resp.status_code} {resp.text}")
        return None
    return resp.json()


def _search_recording_mbid(title: str, artist: str) -> Optional[str]:
    query = f'recording:"{title}" AND artist:"{artist}"'
    params = {
        "query": query,
        "limit": 5,
        "fmt": "json"
    }
    data = _musicbrainz_get("recording", params)
    if not data or "recordings" not in data:
        return None
    recordings = data["recordings"]
    if not recordings:
        return None
    return recordings[0].get("id")


def _get_recording_relationships(mbid: str) -> List[Dict[str, Any]]:
    params = {
        "inc": "artist-credits+aliases+works+work-rels+recording-rels",
        "fmt": "json"
    }
    data = _musicbrainz_get(f"recording/{mbid}", params)
    if not data:
        return []
    return data.get("relations", [])


def get_derivative_works(title: str, artist: str) -> List[Dict[str, Any]]:
    mbid = _search_recording_mbid(title, artist)
    if not mbid:
        return []

    relations = _get_recording_relationships(mbid)
    derivatives = []

    for rel in relations:
        rtype = rel.get("type", "").lower()
        if any(k in rtype for k in ["sample", "cover", "remix", "interpol"]):
            entry: Dict[str, Any] = {}
            target = rel.get("recording") or rel.get("work")
            if not target:
                continue
            entry["mbid"] = target.get("id")
            entry["title"] = target.get("title")
            artists = target.get("artist-credit", [])
            entry["artist"] = " & ".join(a.get("name") for a in artists if "name" in a) if artists else ""
            entry["relation_type"] = rel.get("type")
            entry["source_url"] = f"https://musicbrainz.org/{'recording' if 'recording' in rel else 'work'}/{entry['mbid']}"
            derivatives.append(entry)

    return derivatives

def get_contributors(title: str, artist: str):
    mbid = _search_recording_mbid(title, artist)
    if not mbid:
        return []

    params = {
        "inc": "artist-credits+work-rels+recording-rels",
        "fmt": "json"
    }
    data = _musicbrainz_get(f"recording/{mbid}", params)
    if not data:
        return []

    contributors = []

    # Extract composers, lyricists, writers, producers, engineers
    for rel in data.get("relations", []):
        rel_type = rel.get('type')
        artist_name = rel.get('artist', {}).get('name')
        if not artist_name:
            continue

        if rel_type in ['composer', 'lyricist', 'writer']:
            contributors.append({
                "name": artist_name,
                "role": rel_type.capitalize(),
                "source": "musicbrainz"
            })
        elif rel_type == 'producer':
            contributors.append({
                "name": artist_name,
                "role": "Producer",
                "source": "musicbrainz"
            })
        elif rel_type == 'engineer':
            contributors.append({
                "name": artist_name,
                "role": "Engineer",
                "source": "musicbrainz"
            })

    return contributors

def get_publishing_metadata(title: str, artist: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves ISWC, writers with roles, aliases, and related works for the given song.
    """
    query = f'work:"{title}" AND artist:"{artist}"'
    params = {"query": query, "limit": 1, "fmt": "json"}
    search_data = _musicbrainz_get("work", params)
    
    if not search_data or not search_data.get("works"):
        return None

    work = search_data["works"][0]
    work_id = work.get("id")
    if not work_id:
        return None

    # Fetch full work details
    params = {"inc": "artist-rels+aliases+work-rels", "fmt": "json"}
    work_data = _musicbrainz_get(f"work/{work_id}", params)
    if not work_data:
        return None

    iswc = work_data.get("iswc")
    aliases = [alias.get("name") for alias in work_data.get("aliases", []) if alias.get("name")]

    # Writers (from artist relationships)
    writers = []
    for rel in work_data.get("relations", []):
        if rel.get("type") in ["composer", "lyricist", "writer"]:
            writers.append({
                "name": rel.get("artist", {}).get("name"),
                "role": rel.get("type").capitalize()
            })

    # Related works
    related_works = []
    for rel in work_data.get("relations", []):
        if rel.get("work"):
            related_works.append({
                "title": rel["work"].get("title"),
                "relation_type": rel.get("type"),
                "work_id": rel["work"].get("id")
            })

    return {
        "iswc": iswc,
        "writers": writers,
        "aliases": aliases,
        "related_works": related_works
    }
def get_artist_country(artist_name: str) -> Optional[str]:
    """
    Attempts to retrieve the country of origin for a given artist from MusicBrainz.
    """
    params = {
        "query": f'artist:"{artist_name}"',
        "fmt": "json",
        "limit": 1
    }
    data = _musicbrainz_get("artist", params)
    if not data or "artists" not in data or not data["artists"]:
        return None

    return data["artists"][0].get("country")
