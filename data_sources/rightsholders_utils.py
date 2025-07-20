from __future__ import annotations
from typing import List, Dict, Any
from data_sources.discogs_utils import get_discogs_credits, get_discogs_label
from data_sources.musicbrainz_utils import get_contributors
from data_sources.spotify_utils import get_spotify_metadata


def get_rightsholders(artist: str, title: str) -> Dict[str, Any]:
    spotify_meta = get_spotify_metadata(artist, title)
    # get_spotify_metadata returns label at the top level, not nested under
    # an "album" key. Pull it directly if present.
    label = spotify_meta.get('label') if spotify_meta else None

    discogs_credits = get_discogs_credits(artist, title)
    discogs_label = get_discogs_label(artist, title)
    if not label:
        label = discogs_label

    mb_contributors = get_contributors(title, artist)

    writers = []
    producers = []
    engineers = []
    seen = set()

    def add_contributor(name: str, role: str, source: str, target_list: list):
        key = (name.lower(), role.lower())
        if key not in seen:
            seen.add(key)
            target_list.append({
                "name": name,
                "role": role,
                "source": source
            })


    for credit in discogs_credits:
        role = (credit.role or '').lower()
        name = credit.name
        source = credit.source

        # Normalize role by removing bracketed info for clean comparison
        base_role = role.split('[')[0].strip()

        if 'producer' in base_role:
            print(f"Adding producer: {name} ({credit.role})")
            add_contributor(name, credit.role, source, producers)
        elif 'engineer' in base_role:
            print(f"Adding engineer: {name} ({credit.role})")
            add_contributor(name, credit.role, source, engineers)
        elif any(term in base_role for term in ['writer', 'songwriter', 'composer', 'lyricist', 'lyrics by']):
            print(f"Adding writer: {name} ({credit.role})")
            add_contributor(name, credit.role, source, writers)

    for mb_credit in mb_contributors:
        role = mb_credit['role'].lower()
        if role in ['composer', 'lyricist', 'writer']:
            add_contributor(mb_credit['name'], mb_credit['role'], mb_credit['source'], writers)
        elif role == 'producer':
            add_contributor(mb_credit['name'], mb_credit['role'], mb_credit['source'], producers)
        elif role == 'engineer':
            add_contributor(mb_credit['name'], mb_credit['role'], mb_credit['source'], engineers)

    return {
        "writers": writers,
        "producers": producers,
        "engineers": engineers,
        "label": label
    }


if __name__ == "__main__":
    import sys, json

    if len(sys.argv) != 3:
        print("Usage: python rightsholders_utils.py \"Song Title\" \"Artist Name\"")
        sys.exit(1)

    title, artist = sys.argv[1], sys.argv[2]
    rights = get_rightsholders(artist, title)
    print(json.dumps(rights, indent=2))
