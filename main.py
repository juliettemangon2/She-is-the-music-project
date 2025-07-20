import sys
import json

from data_sources.spotify_utils import get_spotify_metadata
from data_sources.rightsholders_utils import get_rightsholders
from resolvers.combined_derivatives_resolver import resolve_combined_derivatives
from copyright_flags import generate_copyright_flags
from data_sources.musicbrainz_utils import get_artist_country
from data_sources.discogs_utils import get_discogs_master_and_versions, get_discogs_publishing_metadata


def main(artist: str, title: str):
    print(f"Fetching Spotify metadata for {artist} - {title}")
    spotify_data = get_spotify_metadata(artist, title)
    release_year = spotify_data.get("release_year")
    print(f"Spotify data retrieved: {spotify_data}")

    print("Fetching rightsholders...")
    rightsholders = get_rightsholders(artist, title)
    print(f"Rightsholders: {rightsholders}")

    print("Fetching publishing metadata from Discogs...")
    publishing_info = get_discogs_publishing_metadata(artist, title)
    print(f"Publishing info: {publishing_info}")

    print("Resolving derivatives...")
    derivatives = resolve_combined_derivatives(artist, title)
    print(f"Derivatives found: {len(derivatives)}")

    print("Fetching Discogs master & versions...")
    discogs_master = get_discogs_master_and_versions(artist, title)
    print(f"Discogs master data: {discogs_master['master_title']} with {len(discogs_master['versions'])} versions")

    print("Generating copyright flags...")
    flags = generate_copyright_flags(
        artist=artist,
        title=title,
        spotify_data=spotify_data,
        rightsholders=rightsholders,
        derivatives=derivatives,
        discogs_master=discogs_master
    )
    print(f"Flags: {flags}")

    result = {
        "artist": artist,
        "title": title,
        "release_year": release_year,
        "label": rightsholders.get("label"),
        "rightsholders": {
            "writers": rightsholders.get("writers", []),
            "producers": rightsholders.get("producers", []),
            "engineers": rightsholders.get("engineers", [])
        },
        "publishing": publishing_info,
        "derivatives": derivatives,
        "discogs_master": discogs_master,
        "copyright_flags": flags
    }

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py \"Artist Name\" \"Song Title\"")
        sys.exit(1)

    artist = sys.argv[1]
    title = sys.argv[2]

    main(artist, title)
