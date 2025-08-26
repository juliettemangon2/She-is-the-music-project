from __future__ import annotations
from typing import List, Dict, Any
from data_sources.discogs_utils import get_discogs_credits, get_discogs_label
from data_sources.musicbrainz_utils import get_contributors
from data_sources.spotify_utils import get_spotify_metadata


def get_rightsholders(artist: str, title: str) -> Dict[str, Any]:
    spotify_meta = get_spotify_metadata(artist, title)
    label = spotify_meta.get('label') or get_discogs_label(artist, title)

    discogs_data = get_discogs_credits(artist, title)
    discogs_credits = discogs_data.get('credits', [])
    mb_contributors = get_contributors(title, artist)
    spotify_credits = spotify_meta.get('credits', [])

    contributors = []
    writers, producers, engineers = [], [], []
    seen = set()

    def add_contributor(name: str, role: str, source: str):
        key = (name.lower(), role.lower(), source.lower())
        if key not in seen:
            seen.add(key)
            contributors.append({
                "name": name,
                "role": role,
                "source": source
            })
            if 'writer' in role.lower() or 'songwriter' in role.lower() or 'composer' in role.lower() or 'lyricist' in role.lower():
                writers.append({"name": name, "role": role, "source": source})
            elif 'producer' in role.lower():
                producers.append({"name": name, "role": role, "source": source})
            elif 'engineer' in role.lower():
                engineers.append({"name": name, "role": role, "source": source})

    for credit in discogs_credits:
        add_contributor(credit['name'], credit['role'], 'discogs')

    for mb_credit in mb_contributors:
        add_contributor(mb_credit['name'], mb_credit['role'], mb_credit['source'])

    for spotify_credit in spotify_credits:
        add_contributor(spotify_credit['name'], spotify_credit['role'], spotify_credit['source'])

    return {
        "writers": writers,
        "producers": producers,
        "engineers": engineers,
        "contributors": contributors,
        "label": label
    }

if __name__ == "__main__":
    import sys, json

    if len(sys.argv) != 3:
        print("Usage: python rightsholders_utils.py \"Artist Name\" \"Song Title\"")
        sys.exit(1)

    artist, title = sys.argv[1], sys.argv[2]
    rights = get_rightsholders(artist, title)
    print(json.dumps(rights, indent=2))
