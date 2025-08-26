import json

def generate_insight_flags(
    artist: str,
    title: str,
    rightsholders: dict,
    discogs_data: dict,
    musicbrainz_data: dict
) -> dict:
    """
    Generate insight-driven flags about data consistency and completeness.
    
    Args:
        artist: Primary artist name.
        title: Track title.
        rightsholders: Combined contributor data (if already aggregated).
        discogs_data: Raw Discogs metadata.
        musicbrainz_data: Raw MusicBrainz metadata.

    Returns:
        {
            "artist": str,
            "title": str,
            "flags": [ { "type": str, "message": str, "details": dict (optional) } ]
        }
    """
    flags = []

    # 1. Conflicting contributor info
    discogs_writers = set()
    mb_writers = set()

    # Extract writers from Discogs
    for c in discogs_data.get("contributors", []):
        if "songwriter" in c.get("role", "").lower() or "lyrics" in c.get("role", "").lower():
            discogs_writers.add(c.get("name"))

    # Extract writers from MusicBrainz
    for c in musicbrainz_data.get("contributors", []):
        if c.get("role") in ["Composer", "Lyricist", "Writer"]:
            mb_writers.add(c.get("name"))

    if discogs_writers and mb_writers:
        if discogs_writers != mb_writers:
            conflict_details = {
                "discogs": list(discogs_writers),
                "musicbrainz": list(mb_writers)
            }
            flags.append({
                "type": "conflicting_info",
                "message": "Contributor information differs between Discogs and MusicBrainz",
                "details": conflict_details
            })

    # 2. Missing publisher info
    discogs_publishers = discogs_data.get("publishers", [])
    mb_publishers = musicbrainz_data.get("publishing", {}).get("publishers", [])
    if not discogs_publishers and not mb_publishers:
        flags.append({
            "type": "missing_publisher",
            "message": "Publisher information missing"
        })

    return {
        "artist": artist,
        "title": title,
        "flags": flags
    }


# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python insight_flags.py \"Artist\" \"Title\"")
        sys.exit(1)

    artist = sys.argv[1]
    title = sys.argv[2]
    print("This script is meant to be called with pre-fetched data in main.py")
