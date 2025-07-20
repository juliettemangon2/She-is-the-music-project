# resolvers/combined_derivatives_resolver.py

from data_sources.musicbrainz_utils import get_derivative_works as musicbrainz_derivatives
from resolvers.shs_derivatives import get_all_derivatives_from_shs
from data_sources.discogs_utils import get_discogs_master_and_versions
import requests
import time

def enrich_discogs_versions_with_artist(versions):
    enriched_versions = []
    for version in versions:
        if version.get("artist") is None:
            release_id = version['uri'].split("/")[-1]
            try:
                release_data = requests.get(f"https://api.discogs.com/releases/{release_id}", timeout=10)
                if release_data.ok:
                    release_json = release_data.json()
                    artists = release_json.get("artists", [])
                    artist_name = " & ".join([a.get("name") for a in artists if "name" in a]) if artists else None
                    version["artist"] = artist_name
            except Exception as e:
                print(f"Error fetching artist for version {version['uri']}: {e}")
            time.sleep(1)  # avoid hitting rate limits
        enriched_versions.append(version)
    return enriched_versions


def resolve_combined_derivatives(artist: str, title: str):
    combined = {
        "musicbrainz": [],
        "secondhandsongs": [],
        "discogs_master": None,
    }

    print(f"Fetching MusicBrainz derivatives for {artist} - {title}")
    mb_results = musicbrainz_derivatives(title, artist)
    combined["musicbrainz"] = mb_results
    print(f"MusicBrainz derivatives: {len(mb_results)}")

    print("Fetching SecondHandSongs derivatives...")
    shs_results = get_all_derivatives_from_shs(artist, title)
    combined["secondhandsongs"] = shs_results
    print(f"SecondHandSongs derivatives: {len(shs_results)}")

    print("Fetching Discogs master + versions...")
    discogs_master_data = get_discogs_master_and_versions(artist, title)
    if discogs_master_data and discogs_master_data.get("versions"):
        discogs_master_data["versions"] = enrich_discogs_versions_with_artist(discogs_master_data["versions"])
    combined["discogs_master"] = discogs_master_data

    return combined


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 3:
        print("Usage: python combined_derivatives_resolver.py \"Artist Name\" \"Song Title\"")
        sys.exit(1)

    artist = sys.argv[1]
    title = sys.argv[2]

    results = resolve_combined_derivatives(artist, title)
    print(json.dumps(results, indent=2))
