import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_USER_TOKEN")

MB_API_BASE = "https://musicbrainz.org/ws/2"
WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
DISCOGS_API = "https://api.discogs.com/database/search"

HEADERS = {"User-Agent": "SITMApp/0.1"}

def get_musicbrainz_artist(artist_name):
    params = {"query": artist_name, "fmt": "json", "limit": 1}
    resp = requests.get(f"{MB_API_BASE}/artist", params=params, headers=HEADERS, timeout=10)
    if resp.ok and resp.json().get('artists'):
        artist = resp.json()['artists'][0]
        return {
            "id": artist.get("id"),
            "birth": artist.get("life-span", {}).get("begin"),
            "death": artist.get("life-span", {}).get("end"),
            "relations": artist.get("relations", [])
        }
    return None

def get_wikidata_birth_death(wikidata_id):
    resp = requests.get(WIKIDATA_API.format(wikidata_id), timeout=10)
    if not resp.ok:
        return None, None
    data = resp.json()
    entity = data.get('entities', {}).get(wikidata_id, {}).get('claims', {})
    birth = extract_wikidata_date(entity, 'P569')  # Birth date
    death = extract_wikidata_date(entity, 'P570')  # Death date
    return birth, death

def extract_wikidata_date(claims, property_code):
    if property_code in claims:
        time_str = claims[property_code][0]['mainsnak']['datavalue']['value']['time']
        return time_str.lstrip('+').split('T')[0]
    return None

def get_discogs_birth_death(artist_name):
    params = {"q": artist_name, "type": "artist", "per_page": 1, "token": DISCOGS_TOKEN}
    resp = requests.get(DISCOGS_API, params=params, timeout=10)
    if resp.ok and resp.json().get('results'):
        artist = resp.json()['results'][0]
        return artist.get('year', None), artist.get('death_year', None)
    return None, None

def get_artist_birth_death(artist_name):
    # 1. MusicBrainz
    mb_artist = get_musicbrainz_artist(artist_name)
    birth = mb_artist['birth'] if mb_artist and mb_artist['birth'] else None
    death = mb_artist['death'] if mb_artist and mb_artist['death'] else None

    # 2. Wikidata via MusicBrainz relation
    if mb_artist and not (birth and death):
        for rel in mb_artist.get('relations', []):
            if rel.get('type') == 'wikidata':
                wikidata_id = rel.get('url', {}).get('resource', '').split('/')[-1]
                wikidata_birth, wikidata_death = get_wikidata_birth_death(wikidata_id)
                birth = birth or wikidata_birth
                death = death or wikidata_death
                break

    # 3. Discogs fallback
    if not birth and not death:
        birth, death = get_discogs_birth_death(artist_name)

    return {"artist": artist_name, "birth": birth, "death": death}

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) != 2:
        print("Usage: python artist_birth_death.py \"Artist Name\"")
        sys.exit(1)

    artist_name = sys.argv[1]
    data = get_artist_birth_death(artist_name)
    print(json.dumps(data, indent=2))
