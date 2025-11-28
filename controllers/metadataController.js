// controllers/metadataController.js
import mongoose from "mongoose";

import { getSpotifyMetadata } from "../services/spotify.js";
import { getDiscogsMetadata } from "../services/discogs.js";
import { getMusicBrainzMetadata } from "../services/musicbrainz.js";
import { resolveCombinedDerivatives } from "../resolvers/combined.js";
import { generateInsightFlags } from "../resolvers/flags.js";
import { normalizeRole } from "../utils/normalizeRole.js";

import Artist from "../models/Artist.js";
import Song from "../models/Song.js";

// =====================================
// Merge Contributors (Discogs + MB)
// =====================================
function mergeContributors(discogsContrib, mbContrib) {
  const merged = new Map();

  const add = (c, source) => {
    const name = c?.name;
    const role = normalizeRole(c?.role || "");

    if (!name || !role) return;

    if (!merged.has(name)) {
      merged.set(name, {
        name,
        roles: new Set(),
        sources: new Set()
      });
    }

    merged.get(name).roles.add(role);
    merged.get(name).sources.add(source);
  };

  (discogsContrib || []).forEach(c => add(c, "discogs"));
  (mbContrib || []).forEach(c => add(c, "musicbrainz"));

  return Array.from(merged.values()).map(m => ({
    name: m.name,
    roles: [...m.roles],
    sources: [...m.sources]
  }));
}

// =====================================
// Collect Song Data (1 result)
// Equivalent to Python collect_song_data()
// =====================================
export async function collectSong(artist, title) {
  const spotify = await getSpotifyMetadata(artist, title);
  const discogs = await getDiscogsMetadata(artist, title);
  const musicbrainz = await getMusicBrainzMetadata(artist, title);
  const derivatives = await resolveCombinedDerivatives(artist, title);

  const contributors = mergeContributors(
    discogs.contributors || [],
    musicbrainz.contributors || []
  );

  const publishers = [
    ...(discogs.publishers || []),
    ...(musicbrainz.publishing?.publishers || [])
  ];

  const flags = generateInsightFlags(
    artist,
    title,
    {},
    discogs,
    musicbrainz
  );

  return {
    artist,
    title,
    album: spotify.album_name || null,
    release_year: spotify.release_year || null,
    label:
      spotify.label ||
      discogs.labels?.[0]?.name ||
      null,
    spotify_popularity: spotify.track_popularity || 0,
    artist_popularity: spotify.artist_popularity || 0,
    genres: Array.from(
      new Set([
        ...(spotify.artist_genres || []),
        ...(discogs.album_styles || [])
      ])
    ),
    contributors,      // [{ name, roles[], sources[] }]
    publishers,        // [string]
    derivatives,       // SHS + Discogs master
    flags: flags.flags || []
  };
}

// =====================================
// Helper: upsert Artist by name
// =====================================
async function upsertArtistByName(name) {
  if (!name) return null;

  let artist = await Artist.findOne({ name });

  if (!artist) {
    artist = new Artist({
      name,
      externalIds: {}
    });
    await artist.save();
  }

  return artist;
}

// =====================================
// Save Song + Contributors to Mongo
// Replaces save_to_database()
// =====================================
export async function saveSongToMongo(songData) {
  // DEBUG #1: Check which DB you're actually writing to
  console.log("Using database:", mongoose.connection.db.databaseName);

  // 1. Ensure primary artist exists
  const primaryArtist = await upsertArtistByName(songData.artist);

  // 2. Build contributors array with artistId + role
  const contributorDocs = [];

  for (const c of songData.contributors || []) {
    const contributorArtist = await upsertArtistByName(c.name);
    if (!contributorArtist) continue;

    const roles = (c.roles && c.roles.length > 0) ? c.roles : ["Unknown"];

    for (const role of roles) {
      contributorDocs.push({
        artistId: contributorArtist._id,
        role
      });
    }
  }

  // DEBUG #2: Are we generating valid contributor objects?
  console.log("Contributor docs:", contributorDocs);

  // 3. Build sources array (embedded documents)
  const now = new Date();
  const sources = [
    { name: "spotify", id: null, fetchedAt: now },
    { name: "discogs", id: null, fetchedAt: now },
    { name: "musicbrainz", id: null, fetchedAt: now }
  ];

  // 4. Upsert Song
  const existing = await Song.findOne({
    title: songData.title,
    primaryArtist: primaryArtist._id
  });

  if (existing) {
    existing.genres = songData.genres || [];
    existing.labels = songData.label ? [songData.label] : [];
    existing.contributors = contributorDocs;
    existing.sources = sources;

    // DEBUG #3: Does updating work?
    try {
      await existing.save();
      console.log("WRITE OK (existing song)");
    } catch (e) {
      console.error("WRITE FAILED (existing):", e);
    }

    return existing;
  }

  const newSong = new Song({
    title: songData.title,
    primaryArtist: primaryArtist._id,
    genres: songData.genres || [],
    labels: songData.label ? [songData.label] : [],
    contributors: contributorDocs,
    sources
  });

  // DEBUG #3: Does creating work?
  try {
    await newSong.save();
    console.log("WRITE OK (new song)");
  } catch (e) {
    console.error("WRITE FAILED (new):", e);
  }

  return newSong;
}

// =====================================
// Multi-Song Insights (translation of main.py)
// =====================================
export function buildMultiSongInsights(songs) {
  const summary = {
    total_songs: songs.length,
    unique_contributors: new Set(
      songs.flatMap(s => s.contributors.map(c => c.name))
    ).size,
    unique_labels: new Set(
      songs.map(s => s.label).filter(Boolean)
    ).size
  };

  const contributorsMap = {};
  const labelsMap = {};
  const genresMap = {};
  const publishersMap = {};
  const roleTally = {};
  let derivativeCount = 0;

  for (const s of songs) {
    // Contributors
    for (const c of s.contributors || []) {
      if (!contributorsMap[c.name]) {
        contributorsMap[c.name] = {
          count: 0,
          roles: new Set(),
          songs: [],
          co_contributors: new Set()
        };
      }
      contributorsMap[c.name].count++;
      (c.roles || []).forEach(r => {
        contributorsMap[c.name].roles.add(r);
        roleTally[r] = (roleTally[r] || 0) + 1;
      });
      contributorsMap[c.name].songs.push(s.title);
    }

    // Labels
    if (s.label) {
      if (!labelsMap[s.label]) labelsMap[s.label] = { count: 0, songs: [] };
      labelsMap[s.label].count++;
      labelsMap[s.label].songs.push(s.title);
    }

    // Genres
    (s.genres || []).forEach(g => {
      if (!genresMap[g]) genresMap[g] = { count: 0, songs: [] };
      genresMap[g].count++;
      genresMap[g].songs.push(s.title);
    });

    // Publishers
    (s.publishers || []).forEach(p => {
      if (!publishersMap[p]) publishersMap[p] = { count: 0, songs: [] };
      publishersMap[p].count++;
      publishersMap[p].songs.push(s.title);
    });

    if (s.derivatives?.secondhandsongs?.length) {
      derivativeCount++;
    }
  }

  // Co-contributors graph
  for (const s of songs) {
    const names = (s.contributors || []).map(c => c.name);
    for (const c of names) {
      names
        .filter(n => n !== c)
        .forEach(n => contributorsMap[c].co_contributors.add(n));
    }
  }

  const sharedContributors = Object.entries(contributorsMap)
    .filter(([_, v]) => v.count > 1)
    .map(([name, v]) => ({
      name,
      count: v.count,
      roles: [...v.roles],
      songs: v.songs
    }));

  const sharedLabels = Object.entries(labelsMap)
    .filter(([_, v]) => v.count > 1)
    .map(([name, v]) => ({ name, count: v.count, songs: v.songs }));

  const sharedGenres = Object.entries(genresMap)
    .filter(([_, v]) => v.count > 1)
    .map(([name, v]) => ({ name, count: v.count, songs: v.songs }));

  const sharedPublishers = Object.entries(publishersMap)
    .filter(([_, v]) => v.count > 1)
    .map(([name, v]) => ({ name, count: v.count, songs: v.songs }));

  const bucket = v => {
    if (v == null) return "Unknown";
    if (v <= 25) return "0-25";
    if (v <= 50) return "26-50";
    if (v <= 75) return "51-75";
    return "76-100";
  };

  const trackBuckets = {};
  const artistBuckets = {};

  for (const s of songs) {
    const tb = bucket(s.spotify_popularity);
    const ab = bucket(s.artist_popularity);
    trackBuckets[tb] = [...(trackBuckets[tb] || []), `${s.title} (${s.spotify_popularity})`];
    artistBuckets[ab] = [...(artistBuckets[ab] || []), `${s.artist} (${s.artist_popularity})`];
  }

  return {
    summary,
    shared: {
      contributors: sharedContributors,
      labels: sharedLabels,
      genres: sharedGenres,
      publishers: sharedPublishers
    },
    popularity_distribution: {
      track: trackBuckets,
      artist: artistBuckets
    },
    extra_summary: {
      role_tally: roleTally,
      derivative_count: derivativeCount
    }
  };
}

// =====================================
// Public functions used by routes/api.js
// =====================================

// OPTION B: fetch-one now ALSO saves to MongoDB
export async function fetchOneSong(artist, title) {
  const songData = await collectSong(artist, title);
  await saveSongToMongo(songData);
  return songData; // return rich metadata to the frontend
}

// OPTION B: fetch-multiple ALSO saves to MongoDB
export async function fetchMultipleSongs(artists, titles) {
  const results = [];

  for (let i = 0; i < artists.length; i++) {
    const data = await collectSong(artists[i], titles[i]);
    await saveSongToMongo(data);
    results.push(data);
  }

  const insights =
    results.length > 1 ? buildMultiSongInsights(results) : {};

  return {
    songs: results,
    derived_insights: insights
  };
}

// Load entire Mongo database + insights
export async function getDatabaseWithInsights() {
  // populate primaryArtist and contributors.artistId to recover names
  const songs = await Song.find()
    .populate("primaryArtist")
    .populate("contributors.artistId")
    .lean();

  const formatted = songs.map(s => {
    const contributors = (s.contributors || []).map(c => ({
      name: c.artistId?.name || "Unknown",
      roles: c.role ? [c.role] : []
    }));

    return {
      artist: s.primaryArtist?.name || "Unknown Artist",
      title: s.title,
      genres: s.genres || [],
      label: s.labels?.[0] || null,
      publishers: [], // not stored in Song schema
      contributors,
      spotify_popularity: 0,
      artist_popularity: 0,
      derivatives: {}
    };
  });

  const insights =
    formatted.length > 1
      ? buildMultiSongInsights(formatted)
      : {};

  return {
    songs: formatted,
    derived_insights: insights
  };
}

// keep mergeContributors exported if you want it elsewhere
export { mergeContributors };
