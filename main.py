from data_sources.rightsholders_utils import get_rightsholders
from data_sources.spotify_utils import get_spotify_metadata
from resolvers.derivative_mapper import map_derivatives
from copyright_utils import estimate_copyright_status
from risk_assessor import assess_risks

def get_song_metadata(artist: str, title: str) -> dict:
    # Step 1: Spotify metadata (for label + release year)
    spotify_meta = get_spotify_metadata(artist, title)
    release_year = spotify_meta.get("release_year") if spotify_meta else None

    # Step 2: Rightsholders
    rightsholders = get_rightsholders(artist, title)

    # Step 3: Derivatives
    derivatives = map_derivatives(title, artist)

    # Step 4: Copyright Status
    copyright_status = estimate_copyright_status(
        spotify_track=spotify_meta,
        release_year=release_year or 2020  # fallback if unknown
    )

    # Step 5: Risk assessment
    risk_flags = assess_risks(rightsholders, derivatives)

    return {
        "artist": artist,
        "title": title,
        "spotify_metadata": spotify_meta,
        "release_year": release_year,
        "rightsholders": rightsholders,
        "derivatives": derivatives,
        "copyright_status": copyright_status,
        "risk_flags": risk_flags
    }

if __name__ == "__main__":
    import sys, json

    if len(sys.argv) != 3:
        print("Usage: python main.py \"Artist Name\" \"Song Title\"")
        sys.exit(1)

    artist = sys.argv[1]
    title = sys.argv[2]

    metadata = get_song_metadata(artist, title)
    print(json.dumps(metadata, indent=2))
