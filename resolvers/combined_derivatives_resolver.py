# resolvers/combined_derivatives_resolver.py

from resolvers.shs_derivatives import get_all_derivatives_from_shs
from data_sources.discogs_utils import get_discogs_metadata
import requests
import time

def enrich_discogs_versions_with_artist(versions):
    """Ensure each Discogs version has an artist name (fallback to release lookup if missing)."""
    enriched_versions = []
    for version in versions:
        if not version.get("artist"):
            release_id = version['uri'].split("/")[-1]
            try:
                resp = requests.get(f"https://api.discogs.com/releases/{release_id}", timeout=10)
                if resp.ok:
                    release_json = resp.json()
                    artists = release_json.get("artists", [])
                    artist_name = " & ".join([a.get("name") for a in artists if "name" in a]) if artists else None
                    version["artist"] = artist_name
            except Exception as e:
                print(f"Error fetching artist for version {version['uri']}: {e}")
            time.sleep(1)  # avoid hitting rate limits
        enriched_versions.append(version)
    return enriched_versions

def resolve_combined_derivatives(artist: str, title: str) -> dict:
    """
    Combine derivative-related data from SecondHandSongs and Discogs.
    
    Returns:
        {
            "secondhandsongs": [ {title, artist, relation_type, uri}, ... ],
            "discogs_master": {
                "master_title": str,
                "master_artist": str,
                "master_uri": str,
                "versions": [ {title, artist, uri}, ... ]
            }
        }
    """
    combined = {
        "secondhandsongs": [],
        "discogs_master": None
    }

    # SecondHandSongs derivatives (covers, adaptations, performances)
    shs_results = get_all_derivatives_from_shs(artist, title)
    combined["secondhandsongs"] = shs_results

    # Discogs master + versions
    discogs_master_data = get_discogs_metadata(artist, title)
    if discogs_master_data and discogs_master_data.get("versions"):
        discogs_master_data["versions"] = enrich_discogs_versions_with_artist(discogs_master_data["versions"])
    combined["discogs_master"] = discogs_master_data

    return combined

# Example CLI for testing
if __name__ == "__main__":
    import sys, json
    if len(sys.argv) != 3:
        print("Usage: python combined_derivatives_resolver.py \"Artist Name\" \"Song Title\"")
        sys.exit(1)

    artist = sys.argv[1]
    title = sys.argv[2]

    results = resolve_combined_derivatives(artist, title)
    print(json.dumps(results, indent=2))
