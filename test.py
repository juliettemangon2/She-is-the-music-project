import os
import requests
from dotenv import load_dotenv

load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_USER_TOKEN")
if not DISCOGS_TOKEN:
    raise RuntimeError("DISCOGS_USER_TOKEN is missing – set it in your .env file")

HEADERS = {
    "Authorization": f"Discogs token={DISCOGS_TOKEN}",
    "User-Agent": "SITMApp/0.1"
}

def get_all_discogs_contributors(artist: str, title: str):
    # Step 1: Search for the release
    search_url = "https://api.discogs.com/database/search"
    params = {
        "q": f"{artist} {title}",
        "type": "release",
        "per_page": 1
    }
    resp = requests.get(search_url, headers=HEADERS, params=params, timeout=10)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return []

    release_id = results[0].get("id")
    release_url = f"https://api.discogs.com/releases/{release_id}"
    release_resp = requests.get(release_url, headers=HEADERS, timeout=10)
    release_resp.raise_for_status()
    release = release_resp.json()

    contributors = []

    # Step 2: Gather release-level extraartists
    for person in release.get("extraartists", []):
        contributors.append({
            "name": person.get("name", "").strip(),
            "role": person.get("role", "").strip(),
            "source": "discogs_release"
        })

    # Step 3: Gather track-level extraartists
    for track in release.get("tracklist", []):
        if track.get("extraartists"):
            for person in track["extraartists"]:
                contributors.append({
                    "name": person.get("name", "").strip(),
                    "role": person.get("role", "").strip(),
                    "track": track.get("title", "").strip(),
                    "source": "discogs_track"
                })

    return contributors

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 3:
        print("Usage: python script.py \"Artist Name\" \"Song Title\"")
        sys.exit(1)

    artist = sys.argv[1]
    title = sys.argv[2]
    contributors = get_all_discogs_contributors(artist, title)
    print(json.dumps(contributors, indent=2))
