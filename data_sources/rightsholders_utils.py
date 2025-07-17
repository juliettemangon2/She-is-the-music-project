from __future__ import annotations
from typing import List, Dict, Any
from data_sources.discogs_utils import get_discogs_credits, get_discogs_label
from data_sources.musicbrainz_utils import get_contributors
from data_sources.spotify_utils import get_spotify_metadata


def get_rightsholders(artist: str, title: str) -> Dict[str, Any]:
    """
    Aggregates rightsholder information from Discogs, MusicBrainz, and Spotify.

    Returns:
        Dictionary with:
            - writers: List of dicts
            - producers: List of dicts
            - engineers: List of dicts
            - label: str or None
    """
    # Spotify Metadata for label
    spotify_meta = get_spotify_metadata(artist, title)
    label = spotify_meta.get('album', {}).get('label') if spotify_meta else None

    # Discogs Credits and Label
    discogs_credits = get_discogs_credits(artist, title)
    discogs_label = get_discogs_label(artist, title)
    if not label:
        label = discogs_label

    # MusicBrainz Contributors (writers)
    mb_contributors = get_contributors(title, artist)

    writers = []
    producers = []
    engineers = []
    seen = set()

    # Process Discogs Credits
    for credit in discogs_credits:
        name = credit.name
        role = credit.role.lower()
        key = (name.lower(), role)
        if key in seen:
            continue
        seen.add(key)

        entry = {"name": name, "role": credit.role, "source": credit.source}

        if 'producer' in role:
            producers.append(entry)
        elif 'engineer' in role:
            engineers.append(entry)
        elif 'writer' in role or 'songwriter' in role or 'composer' in role:
            writers.append(entry)

    # Process MusicBrainz contributors as writers
    for mb_credit in mb_contributors:
        name = mb_credit['name']
        role = mb_credit['role'].lower()
        key = (name.lower(), role)
        if key in seen:
            continue
        seen.add(key)

        writers.append({
            "name": name,
            "role": mb_credit['role'],
            "source": mb_credit.get('source', 'musicbrainz')
        })

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
