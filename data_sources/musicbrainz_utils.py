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
    params = {"query": query, "limit": 5, "fmt": "json"}
    data = _musicbrainz_get("recording", params)
    if not data or "recordings" not in data or not data["recordings"]:
        return None
    return data["recordings"][0].get("id")

def _normalize_role(role: str) -> str:
    return role.replace("-", " ").title()

def _get_artist_details(artist_id: str) -> Dict[str, Any]:
    """Fetch artist details (ISNI, IPI, disambiguation)."""
    params = {"inc": "isni-codes+ipi-codes", "fmt": "json"}
    data = _musicbrainz_get(f"artist/{artist_id}", params)
    if not data:
        return {}
    return {
        "isni": data.get("isni-codes", []),
        "ipi": data.get("ipi-codes", []),
        "disambiguation": data.get("disambiguation")
    }

def _get_recording_contributors(mbid: str) -> List[Dict[str, Any]]:
    """Get recording-level contributors with expanded roles."""
    params = {"inc": "artist-credits+work-rels+recording-rels+artist-rels", "fmt": "json"}
    data = _musicbrainz_get(f"recording/{mbid}", params)
    if not data:
        return []

    contributors = []
    for rel in data.get("relations", []):
        rel_type = rel.get("type")
        if rel_type in ["composer", "lyricist", "writer", "arranger", "producer", "engineer"]:
            artist_info = rel.get("artist", {})
            artist_id = artist_info.get("id")
            name = artist_info.get("name")
            if not name:
                continue
            artist_details = _get_artist_details(artist_id) if artist_id else {}

            contributors.append({
                "name": name,
                "role": _normalize_role(rel_type),
                "scope": "recording",
                "isni": artist_details.get("isni"),
                "ipi": artist_details.get("ipi"),
                "disambiguation": artist_details.get("disambiguation"),
                "source": "musicbrainz"
            })
    return contributors

def _get_work_metadata(title: str, artist: str) -> Dict[str, Any]:
    """Fetch publishing data and work-level contributors."""
    query = f'work:"{title}" AND artist:"{artist}"'
    params = {"query": query, "limit": 1, "fmt": "json"}
    search_data = _musicbrainz_get("work", params)
    if not search_data or not search_data.get("works"):
        return {}

    work = search_data["works"][0]
    work_id = work.get("id")
    if not work_id:
        return {}

    # Fetch full work details
    params = {"inc": "artist-rels+aliases+work-rels", "fmt": "json"}
    work_data = _musicbrainz_get(f"work/{work_id}", params)
    if not work_data:
        return {}

    iswc = work_data.get("iswc")
    aliases = [alias.get("name") for alias in work_data.get("aliases", []) if alias.get("name")]

    # Writers (with details)
    contributors = []
    for rel in work_data.get("relations", []):
        if rel.get("type") in ["composer", "lyricist", "writer"]:
            artist_info = rel.get("artist", {})
            artist_id = artist_info.get("id")
            name = artist_info.get("name")
            if not name:
                continue
            artist_details = _get_artist_details(artist_id) if artist_id else {}

            contributors.append({
                "name": name,
                "role": _normalize_role(rel.get("type")),
                "scope": "work",
                "isni": artist_details.get("isni"),
                "ipi": artist_details.get("ipi"),
                "disambiguation": artist_details.get("disambiguation"),
                "source": "musicbrainz"
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
        "aliases": aliases,
        "contributors": contributors,
        "related_works": related_works
    }

def get_musicbrainz_metadata(artist: str, title: str) -> Dict[str, Any]:
    """Main function to aggregate MusicBrainz metadata for a song."""
    mbid = _search_recording_mbid(title, artist)
    if not mbid:
        return {}

    recording_contributors = _get_recording_contributors(mbid)
    work_metadata = _get_work_metadata(title, artist)

    contributors = recording_contributors + work_metadata.get("contributors", [])

    return {
        "contributors": contributors,
        "publishing": {
            "iswc": work_metadata.get("iswc"),
            "aliases": work_metadata.get("aliases"),
            "related_works": work_metadata.get("related_works")
        }
    }

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) != 3:
        print("Usage: python musicbrainz_utils.py \"Artist Name\" \"Song Title\"")
        sys.exit(1)

    artist = sys.argv[1]
    title = sys.argv[2]

    metadata = get_musicbrainz_metadata(artist, title)
    print(json.dumps(metadata, indent=2))
