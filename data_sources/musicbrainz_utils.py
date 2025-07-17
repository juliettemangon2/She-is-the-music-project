import time
import logging
import requests
from typing import List, Dict, Any, Optional
from requests.adapters import HTTPAdapter, Retry

MB_API_BASE = "https://musicbrainz.org/ws/2"
USER_AGENT = "SITMApp/0.1"
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
            "Accept": "application/json"
        })
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)

        _session = session
    return _session

def _musicbrainz_get(endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    time.sleep(REQUEST_DELAY)
    resp = _get_session().get(f"{MB_API_BASE}/{endpoint}", params=params, timeout=10)
    if resp.ok:
        return resp.json()
    logger.warning(f"MusicBrainz GET failed: {resp.status_code} {resp.text}")
    return None

def _search_recording_mbid(title: str, artist: str) -> Optional[str]:
    query = f'recording:\"{title}\" AND artist:\"{artist}\"'
    params = {"query": query, "limit": 1, "fmt": "json"}
    data = _musicbrainz_get("recording", params)
    if data and data.get("recordings"):
        return data["recordings"][0]["id"]
    return None

def get_contributors(title: str, artist: str) -> List[Dict[str, Any]]:
    mbid = _search_recording_mbid(title, artist)
    if not mbid:
        return []

    params = {"inc": "artist-credits+work-rels+recording-rels", "fmt": "json"}
    data = _musicbrainz_get(f"recording/{mbid}", params)
    if not data:
        return []

    contributors = []
    # First gather recording level relations
    for rel in data.get("relations", []):
        if rel.get("type") in ["composer", "lyricist"] and "artist" in rel:
            contributors.append({
                "name": rel["artist"]["name"],
                "role": rel["type"],
                "source": "musicbrainz"
            })

    # Then gather work-level contributors
    for work_rel in data.get("relations", []):
        if work_rel.get("work"):
            work_id = work_rel["work"].get("id")
            if work_id:
                work_data = _musicbrainz_get(f"work/{work_id}", {"inc": "artist-rels", "fmt": "json"})
                if work_data:
                    for artist_rel in work_data.get("relations", []):
                        if artist_rel.get("type") in ["composer", "lyricist"] and "artist" in artist_rel:
                            contributors.append({
                                "name": artist_rel["artist"]["name"],
                                "role": artist_rel["type"],
                                "source": "musicbrainz"
                            })

    return contributors
