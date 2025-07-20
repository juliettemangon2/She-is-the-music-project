# resolvers/shs_derivatives.py

import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

SHS_API_KEY = os.getenv("SHS_API_KEY")
SHS_BASE_URL = "https://api.secondhandsongs.com"

HEADERS = {
    "Accept": "application/json"
}
if SHS_API_KEY:
    HEADERS["X-API-Key"] = SHS_API_KEY


def search_work(title: str, artist: str):
    params = {"title": title, "format": "json"}
    resp = requests.get(f"{SHS_BASE_URL}/search/work", headers=HEADERS, params=params, timeout=10, verify=False)
    if not resp.ok:
        return None
    data = resp.json()
    results = data.get("resultPage", [])

    for work in results:
        work_uri = work.get("uri")
        if work_uri:
            details = fetch_work_details(work_uri)
            original = details.get("original", {})
            performer = original.get("performer", {}).get("name", "").lower()
            if artist.lower() in performer:
                return details
    return None


def fetch_work_details(work_uri: str):
    resp = requests.get(work_uri, headers=HEADERS, timeout=10, verify=False)
    return resp.json() if resp.ok else {}


def search_performances(title: str, artist: str):
    params = {"title": title, "performer": artist, "format": "json"}
    resp = requests.get(f"{SHS_BASE_URL}/search/performance", headers=HEADERS, params=params, timeout=10, verify=False)
    if resp.ok:
        data = resp.json()
        return data.get("resultPage", [])
    return []


def get_all_derivatives_from_shs(artist: str, title: str):
    derivatives = []
    seen_uris = set()

    work_details = search_work(title, artist)
    if work_details:
        for category in ['versions', 'derivedWorks']:
            for item in work_details.get(category, []):
                uri = item.get('uri')
                artist_name = item.get("performer", {}).get("name", "Unknown")
                if uri and uri not in seen_uris and artist_name != "Unknown":
                    seen_uris.add(uri)
                    derivatives.append({
                        "title": item.get("title"),
                        "artist": artist_name,
                        "relation_type": category,
                        "uri": uri
                    })

    performances = search_performances(title, artist)
    for perf in performances:
        uri = perf.get("uri")
        artist_name = perf.get("performer", {}).get("name", "Unknown")
        if uri and uri not in seen_uris and artist_name != "Unknown":
            seen_uris.add(uri)
            derivatives.append({
                "title": perf.get("title"),
                "artist": artist_name,
                "relation_type": "performance",
                "uri": uri
            })

    return derivatives
