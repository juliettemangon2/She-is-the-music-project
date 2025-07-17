# resolvers/derivative_mapper.py

from __future__ import annotations
import uuid
import re
from typing import Any, Dict, List
from data_sources.musicbrainz_utils import get_derivative_works

# A simple dataclass to represent a normalized derivative work
from dataclasses import dataclass, asdict

@dataclass(slots=True, frozen=True)
class Derivative:
    id: str
    title: str
    artist: str
    mbid: str
    relation_type: str
    source_url: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _clean_text(s: str) -> str:
    """
    Basic normalization: strip extra whitespace, collapse spaces,
    remove leading/trailing punctuation.
    """
    s = s.strip()
    # collapse multiple spaces
    s = re.sub(r'\s+', ' ', s)
    # remove unbalanced leading/trailing punctuation
    s = re.sub(r'^[\W_]+|[\W_]+$', '', s)
    return s


def map_derivatives(
    title: str,
    artist: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetches raw derivatives via MusicBrainz and normalizes entries.

    Args:
        title: Original track title.
        artist: Original track artist.

    Returns:
        Dict with keys 'samples', 'covers', 'remixes', 'interpolations',
        each mapping to a list of normalized derivative dicts.
    """
    raw = get_derivative_works(title=title, artist=artist)

    mapped: Dict[str, List[Dict[str, Any]]] = {
        "samples": [],
        "covers": [],
        "remixes": [],
        "interpolations": []
    }

    for category, entries in raw.items():
        for entry in entries:
            # Clean up title and artist fields
            clean_title = _clean_text(entry.get("title", "")) or "Unknown Title"
            clean_artist = _clean_text(entry.get("artist", "")) or "Unknown Artist"

            mbid = entry.get("mbid") or str(uuid.uuid4())
            rel_type = entry.get("relation_type", "").lower()

            # Assign our own unique node ID for graph purposes
            node_id = f"deriv-{uuid.uuid4().hex}"

            # Build the final Derivative object
            deriv = Derivative(
                id=node_id,
                title=clean_title,
                artist=clean_artist,
                mbid=mbid,
                relation_type=rel_type,
                source_url=entry.get("source_url", "")
            )

            mapped[category].append(deriv.to_dict())

    return mapped


# Example standalone test
if __name__ == "__main__":
    import json, sys

    if len(sys.argv) != 3:
        print("Usage: python -m resolvers.derivative_mapper \"Song Title\" \"Artist Name\"")
        sys.exit(1)

    song_title, artist_name = sys.argv[1], sys.argv[2]
    out = map_derivatives(song_title, artist_name)
    print(json.dumps(out, indent=2))
