import datetime
from data_sources.musicbrainz_utils import get_artist_country
from artist_birth_death import get_artist_birth_death
from data_sources.musicbrainz_utils import get_publishing_metadata
from data_sources.discogs_utils import get_discogs_publishing_metadata

import json
import os

COPYRIGHT_RULES_PATH = os.path.join(os.path.dirname(__file__), 'copyright_rules.json')
with open(COPYRIGHT_RULES_PATH, 'r') as f:
    raw_rules = json.load(f)

COPYRIGHT_RULES = {entry['country']: entry for entry in raw_rules}



def resolve_country(artist: str, label: str = None) -> (str, bool):
    country = get_artist_country(artist)
    if country:
        return country, False
    return "EU", True  # default fallback to US


def generate_copyright_flags(
    artist: str,
    title: str,
    spotify_data: dict,
    rightsholders: dict,
    derivatives: dict,
    discogs_master: dict
):
    year = datetime.datetime.now().year
    flags = []

    label = rightsholders.get('label')
    country, country_missing = resolve_country(artist, label)

    if country_missing:
        flags.append("Country unknown — defaulted to EU")

    rule = COPYRIGHT_RULES.get(country)
    term = int(rule['term']) if rule else 70

    artist_meta = get_artist_birth_death(artist)
    birth_year = artist_meta.get('birth')
    death_year = artist_meta.get('death')

    if birth_year:
        expiry_year = (death_year if death_year else year) + term
        if expiry_year <= year:
            flags.append(f"Copyright expired under {country} law (expired in {expiry_year})")
        elif expiry_year - year <= 5:
            flags.append(f"Copyright expiring soon under {country} law (expires in {expiry_year})")
    else:
        flags.append("Artist birth year missing — unable to evaluate life+term rule")

   # Discogs publishing extraction
    discogs_pub_data = get_discogs_publishing_metadata(artist, title)
    discogs_publishers = discogs_pub_data.get('publishers', [])
    if discogs_publishers:
        print(f"Discogs publishers: {discogs_publishers}")

    # Publishing metadata check
    publishing = get_publishing_metadata(title, artist) or {}
    if not publishing.get('iswc'):
        flags.append("Missing ISWC code")
    if not publishing.get('pro'):
        flags.append("Missing Performing Rights Organization (PRO) information")

    combined_publishers = discogs_publishers + publishing.get('publishers', [])
    if not combined_publishers:
        flags.append("Missing publisher information")
    else:
        print(f"Combined publishers: {combined_publishers}")


    # Derivatives check
    total_derivatives = sum(len(v) for v in derivatives.values() if isinstance(v, list))
    if total_derivatives == 0:
        flags.append("No derivative works found — potential orphan work")

    # Conflicting writers: compare sources
    writers = rightsholders.get('writers', [])
    writers_by_source = {}
    for w in writers:
        source = w.get('source', 'unknown')
        writers_by_source.setdefault(source, set()).add(w['name'])

    discogs_writers = writers_by_source.get('discogs', set())
    mb_writers = writers_by_source.get('musicbrainz', set())

    if discogs_writers and mb_writers:
        conflicts = discogs_writers.symmetric_difference(mb_writers)
        if conflicts:
            flags.append(f"Conflicting writer data between Discogs and MusicBrainz: {', '.join(conflicts)}")

    return {
        "artist": artist,
        "title": title,
        "country": country,
        "flags": flags
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python copyright_flags.py \"Artist\" \"Title\"")
        sys.exit(1)

    artist, title = sys.argv[1], sys.argv[2]
    # Since this is standalone, you'd have to fetch all the data here to test directly
    print("This module is intended to be called from main.py with pre-fetched data.")
