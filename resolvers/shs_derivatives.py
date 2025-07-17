import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

SHS_API_KEY = os.getenv("SHS_API_KEY")
SHS_BASE_URL = "https://api.secondhandsongs.com"

HEADERS = {
    "Accept": "application/json"
}
if SHS_API_KEY:
    HEADERS["X-API-Key"] = SHS_API_KEY


def search_work(title: str, artist: str) -> Any:
    params = {
        "title": title,
        "credits": artist,
        "format": "json"
    }
    resp = requests.get(f"{SHS_BASE_URL}/search/work", headers=HEADERS, params=params, timeout=10, verify=False)
    if not resp.ok:
        print(f"Failed to search work: {resp.status_code} {resp.text}")
        return None

    data = resp.json()
    works = data.get("results", [])
    return works[0] if works else None


def fetch_work_details(work_uri: str) -> Any:
    url = f"{SHS_BASE_URL}{work_uri}"
    resp = requests.get(url, headers=HEADERS, timeout=10, verify=False)
    if not resp.ok:
        print(f"Failed to fetch work details: {resp.status_code} {resp.text}")
        return None

    return resp.json()


def get_shs_work_full_data(artist: str, title: str) -> Dict[str, Any]:
    work = search_work(title, artist)
    if not work:
        return {}

    work_details = fetch_work_details(work["uri"])
    if not work_details:
        return {}

    return {
        "title": work_details.get("title"),
        "entityType": work_details.get("entityType"),
        "language": work_details.get("language"),
        "credits": work_details.get("credits"),
        "originalCredits": work_details.get("originalCredits"),
        "original": work_details.get("original"),
        "basedOn": work_details.get("basedOn"),
        "derivedWorks": work_details.get("derivedWorks"),
        "versions": work_details.get("versions")
    }


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 3:
        print("Usage: python shs_derivatives.py \"Artist Name\" \"Song Title\"")
        sys.exit(1)

    artist = sys.argv[1]
    title = sys.argv[2]

    print(f"Fetching full work data for: {title} by {artist}\n")
    work_data = get_shs_work_full_data(artist, title)
    print(json.dumps(work_data, indent=2))