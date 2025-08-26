import sys
import json
import os
from typing import List, Dict, Any
from itertools import combinations
from collections import Counter, defaultdict
from data_sources.spotify_utils import get_spotify_metadata
from data_sources.discogs_utils import get_discogs_metadata
from data_sources.musicbrainz_utils import get_musicbrainz_metadata
from resolvers.combined_derivatives_resolver import resolve_combined_derivatives
from copyright_flags import generate_insight_flags

DATABASE_FILE = "database.json"

# ===============================
# Role Normalization
# ===============================
def normalize_role(role: str) -> str:
    if not role:
        return None
    role = role.lower()
    replacements = {
        'lyrics': 'Lyricist',
        'composer': 'Composer',
        'written': 'Composer',
        'producer': 'Producer',
        'engineer': 'Engineer',
        'vocals': 'Vocalist',
        'guitar': 'Guitar'
    }
    for key, val in replacements.items():
        if key in role:
            return val
    return role.capitalize()

# ===============================
# Collect & Merge Metadata
# ===============================
def collect_song_data(artist: str, title: str) -> Dict[str, Any]:
    spotify_data = get_spotify_metadata(artist, title)
    discogs_data = get_discogs_metadata(artist, title)
    musicbrainz_data = get_musicbrainz_metadata(artist, title)
    derivatives = resolve_combined_derivatives(artist, title)

    contributors = merge_contributors(
        discogs_data.get("contributors", []),
        musicbrainz_data.get("contributors", [])
    )

    publishers = list(set(
        discogs_data.get("publishers", []) +
        musicbrainz_data.get("publishing", {}).get("publishers", [])
    ))

    flags = generate_insight_flags(artist, title, {}, discogs_data, musicbrainz_data)

    return {
        "artist": artist,
        "title": title,
        "album": spotify_data.get("album_name"),
        "release_year": spotify_data.get("release_year"),
        "label": spotify_data.get("label") or (discogs_data.get("labels")[0]["name"] if discogs_data.get("labels") else None),
        "spotify_popularity": spotify_data.get("track_popularity", 0),
        "artist_popularity": spotify_data.get("artist_popularity", 0),
        "genres": list(set(spotify_data.get("artist_genres", []) + discogs_data.get("album_styles", []))),
        "contributors": contributors,
        "publishers": publishers,
        "derivatives": derivatives,
        "flags": flags["flags"]
    }

# ===============================
# Merge Contributors
# ===============================
def merge_contributors(discogs_contributors: List[Dict[str, Any]], mb_contributors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged = {}

    def add(c, source):
        name = c.get("name")
        role = normalize_role(c.get("role", ""))
        if not name or not role:
            return
        if name not in merged:
            merged[name] = {"name": name, "roles": set(), "sources": set()}
        merged[name]["roles"].add(role)
        merged[name]["sources"].add(source)

    for c in discogs_contributors:
        add(c, "discogs")
    for c in mb_contributors:
        add(c, "musicbrainz")

    return [
        {
            "name": name,
            "roles": sorted(list(info["roles"])),
            "sources": sorted(list(info["sources"]))
        }
        for name, info in merged.items()
    ]

# ===============================
# Save Song to Database
# ===============================
def save_to_database(song_data: Dict[str, Any]):
    db = []
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as f:
            try:
                db = json.load(f)
            except json.JSONDecodeError:
                db = []
    artist_key = song_data["artist"].strip().lower()
    title_key = song_data["title"].strip().lower()
    for i, s in enumerate(db):
        if s.get("artist", "").strip().lower() == artist_key and s.get("title", "").strip().lower() == title_key:
            db[i] = song_data
            break
    else:
        db.append(song_data)
    with open(DATABASE_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ===============================
# Derived Insights Builder
# ===============================
def build_multi_song_insights(songs: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Summary
    summary = {
        "total_songs": len(songs),
        "unique_contributors": len({c["name"] for s in songs for c in s["contributors"]}),
        "unique_labels": len({s["label"] for s in songs if s["label"]})
    }

    # Shared maps
    contributors_map, labels_map, genres_map, publishers_map = {}, {}, {}, {}
    role_tally = Counter()
    derivative_count = 0

    for s in songs:
        for c in s["contributors"]:
            contributors_map.setdefault(c["name"], {"count": 0, "roles": set(), "songs": [], "co_contributors": set()})
            contributors_map[c["name"]]["count"] += 1
            contributors_map[c["name"]]["roles"].update(c["roles"])
            contributors_map[c["name"]]["songs"].append(s["title"])
            for r in c["roles"]:
                role_tally[r] += 1
        if s["label"]:
            labels_map.setdefault(s["label"], {"count": 0, "songs": []})
            labels_map[s["label"]]["count"] += 1
            labels_map[s["label"]]["songs"].append(s["title"])
        for g in s["genres"]:
            genres_map.setdefault(g, {"count": 0, "songs": []})
            genres_map[g]["count"] += 1
            genres_map[g]["songs"].append(s["title"])
        for p in s["publishers"]:
            publishers_map.setdefault(p, {"count": 0, "songs": []})
            publishers_map[p]["count"] += 1
            publishers_map[p]["songs"].append(s["title"])
        if s.get("derivatives", {}).get("secondhandsongs"):
            derivative_count += 1

    # Build co-contributor mapping
    for s in songs:
        song_contributors = [c["name"] for c in s["contributors"]]
        for c in song_contributors:
            contributors_map[c]["co_contributors"].update([x for x in song_contributors if x != c])

    shared_contributors = [
        {"name": k, "count": v["count"], "roles": list(v["roles"]), "songs": v["songs"]}
        for k, v in contributors_map.items() if v["count"] > 1
    ]
    shared_labels = [{"name": k, "count": v["count"], "songs": v["songs"]} for k, v in labels_map.items() if v["count"] > 1]
    shared_genres = [{"name": k, "count": v["count"], "songs": v["songs"]} for k, v in genres_map.items() if v["count"] > 1]
    shared_publishers = [{"name": k, "count": v["count"], "songs": v["songs"]} for k, v in publishers_map.items() if v["count"] > 1]

    # Popularity Buckets
    def bucket_popularity(value: int) -> str:
        if value is None:
            return "Unknown"
        if value <= 25:
            return "0-25"
        elif value <= 50:
            return "26-50"
        elif value <= 75:
            return "51-75"
        else:
            return "76-100"

    track_buckets, artist_buckets = {}, {}
    for s in songs:
        track_range = bucket_popularity(s.get("spotify_popularity", 0))
        artist_range = bucket_popularity(s.get("artist_popularity", 0))
        track_buckets.setdefault(track_range, []).append(f"{s['title']} ({s.get('spotify_popularity', 0)})")
        artist_buckets.setdefault(artist_range, []).append(f"{s['artist']} ({s.get('artist_popularity', 0)})")

    # Patterns: connectors = contributors linking other contributors
    # ✅ Build adjacency for all contributors (connections through shared songs)
    adjacency = defaultdict(set)
    for s in songs:
        names = [c["name"] for c in s["contributors"]]
        for a, b in combinations(names, 2):
            adjacency[a].add(b)
            adjacency[b].add(a)

    # ✅ Identify true linkers (contributors who connect others who are otherwise unconnected)
    connectors = []
    for contributor, data in contributors_map.items():
        co_contributors = list(data["co_contributors"])
        unique_links = []
        for a, b in combinations(co_contributors, 2):
            # If a and b are NOT connected directly (except via current contributor)
            if b not in adjacency[a]:
                unique_links.append((a, b))
        if unique_links:
            linked_names = sorted({name for pair in unique_links for name in pair})
            connectors.append({
                "name": contributor,
                "linked_contributors": linked_names,
                "songs": data["songs"]
            })


    # Clusters: simple (contributors sharing songs)
    # ✅ Build clusters: groups of contributors that appear together on 2+ songs
    combo_map = defaultdict(list)

    # Step 1: For each song, track contributor sets
    for s in songs:
        names = sorted([c["name"] for c in s["contributors"]])
        # For every combination of contributors of size 2 or more
        for size in range(2, len(names)+1):
            for combo in combinations(names, size):
                combo_map[combo].append(s["title"])

    # Step 2: Filter combos with at least 2 songs
    valid_combos = {combo: titles for combo, titles in combo_map.items() if len(titles) >= 2}

    # Step 3: Sort by size (largest first), then filter out subsets
    sorted_combos = sorted(valid_combos.items(), key=lambda x: (-len(x[0]), -len(x[1])))

    clusters = []
    for combo, titles in sorted_combos:
        # Skip if this combo is a subset of an already chosen cluster
        if any(set(combo).issubset(set(existing["names"])) for existing in clusters):
            continue
        clusters.append({
            "names": list(combo),
            "songs": list(set(titles))
        })

    # Top entities
    top_entities = {
        "contributor": max(contributors_map.items(), key=lambda x: x[1]["count"])[0] if contributors_map else None,
        "label": max(labels_map.items(), key=lambda x: x[1]["count"])[0] if labels_map else None,
        "genre": max(genres_map.items(), key=lambda x: x[1]["count"])[0] if genres_map else None
    }

    return {
        "summary": summary,
        "shared": {
            "contributors": shared_contributors,
            "labels": shared_labels,
            "genres": shared_genres,
            "publishers": shared_publishers
        },
        "patterns": {
            "clusters": clusters,
            "connectors": connectors
        },
        "popularity_distribution": {
            "track": track_buckets,
            "artist": artist_buckets
        },
        "top_entities": top_entities,
        "extra_summary": {
            "role_tally": dict(role_tally),
            "derivative_count": derivative_count
        }
    }

# ===============================
# Aggregate for Compare Tab
# ===============================
def aggregate_song_data(artists: List[str], titles: List[str]) -> Dict[str, Any]:
    results = []
    for artist, title in zip(artists, titles):
        song_data = collect_song_data(artist, title)
        save_to_database(song_data)
        results.append(song_data)

    insights = {}
    if len(results) > 1:
        insights = build_multi_song_insights(results)

    return {"songs": results, "derived_insights": insights}

# ===============================
# Load Database with Insights
# ===============================
def load_database_with_insights() -> Dict[str, Any]:
    if not os.path.exists(DATABASE_FILE):
        return {"songs": [], "derived_insights": {}}

    with open(DATABASE_FILE, "r") as f:
        try:
            db = json.load(f)
        except json.JSONDecodeError:
            db = []

    insights = {}
    if len(db) > 1:
        insights = build_multi_song_insights(db)

    return {"songs": db, "derived_insights": insights}



# ===============================
# CLI Runner
# ===============================
def main(artist1, title1, artist2=None, title2=None):
    return aggregate_song_data([artist1, artist2] if artist2 else [artist1],
                                [title1, title2] if title2 else [title1])

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) not in [2, 4]:
        print("Usage: python main.py \"Artist1\" \"Title1\" [\"Artist2\" \"Title2\"]")
        sys.exit(1)
    print(json.dumps(main(*args), indent=2))
