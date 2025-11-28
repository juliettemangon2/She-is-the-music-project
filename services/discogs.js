// services/discogs.js
import "dotenv/config";

const DISCOGS_TOKEN = process.env.DISCOGS_USER_TOKEN;
const BASE_URL = "https://api.discogs.com";

function discogsHeaders() {
  return {
    "User-Agent": "SITMApp/0.1",
    Authorization: `Discogs token=${DISCOGS_TOKEN}`,
    Accept: "application/json",
  };
}

// Helper: avoid duplicates
function contributorKey(c) {
  return `${c.name?.toLowerCase() || ""}-${c.role?.toLowerCase() || ""}`;
}

export async function getDiscogsMetadata(artist, songTitle) {
  if (!DISCOGS_TOKEN) {
    console.error("Missing DISCOGS_USER_TOKEN in environment variables");
    return {};
  }

  // Step 1: search release matching (artist + title)
  const params = new URLSearchParams({
    q: `${artist} ${songTitle}`,
    type: "release",
    per_page: "1",
  });

  let searchResp;
  try {
    searchResp = await fetch(`${BASE_URL}/database/search?${params}`, {
      headers: discogsHeaders(),
    });
  } catch (err) {
    console.error("Discogs search fetch error:", err);
    return {};
  }

  if (!searchResp.ok) {
    console.error("Discogs search error:", searchResp.status);
    return {};
  }

  const searchJson = await searchResp.json();
  const results = searchJson.results || [];
  if (!results.length) return {};

  const releaseId = results[0].id;
  if (!releaseId) return {};

  // Step 2: fetch release details
  const releaseResp = await fetch(`${BASE_URL}/releases/${releaseId}`, {
    headers: discogsHeaders(),
  });

  if (!releaseResp.ok) {
    console.error("Discogs release error:", releaseResp.status);
    return {};
  }

  const release = await releaseResp.json();

  // --------------------------------------------
  // Parse contributors
  // --------------------------------------------
  const contributors = [];
  const seen = new Set();

  // Track-level contributors
  if (Array.isArray(release.tracklist)) {
    for (const track of release.tracklist) {
      const trackTitle = track.title?.toLowerCase() || "";
      if (trackTitle.includes(songTitle.toLowerCase()) && track.extraartists) {
        for (const artistEntry of track.extraartists) {
          const c = {
            name: artistEntry.name?.trim(),
            role: artistEntry.role?.trim(),
            source: "discogs",
            scope: "track",
          };
          const key = contributorKey(c);
          if (!seen.has(key)) {
            seen.add(key);
            contributors.push(c);
          }
        }
      }
    }
  }

  // Fallback: release-level contributors
  if (contributors.length === 0 && Array.isArray(release.extraartists)) {
    for (const artistEntry of release.extraartists) {
      const c = {
        name: artistEntry.name?.trim(),
        role: artistEntry.role?.trim(),
        source: "discogs",
        scope: "album",
      };
      const key = contributorKey(c);
      if (!seen.has(key)) {
        seen.add(key);
        contributors.push(c);
      }
    }
  }

  // --------------------------------------------
  // Album-level info
  // --------------------------------------------
  const albumGenres = release.genres || [];
  const albumStyles = release.styles || [];
  const albumFormats =
    release.formats?.map((fmt) => fmt.name).filter(Boolean) || [];

  // Release info
  let releaseYear = release.year;
  if (!releaseYear && release.released) {
    releaseYear = parseInt(release.released.split("-")[0], 10);
  }

  const releaseCountry = release.country;

  // Labels
  const labels =
    release.labels?.map((lbl) => ({
      name: lbl.name,
      catno: lbl.catno,
    })) || [];

  // Companies
  const companies =
    release.companies?.map((c) => ({
      name: c.name,
      role: c.entity_type_name,
    })) || [];

  // Identifiers
  const identifiers =
    release.identifiers?.map((id) => ({
      type: id.type,
      value: id.value,
    })) || [];

  // Publishers
  const publishers = new Set();
  for (const comp of release.companies || []) {
    if (comp.entity_type_name?.toLowerCase().includes("published by")) {
      publishers.add(comp.name);
    }
  }

  // Legal info
  const copyrights = [];
  const phonographicRights = [];

  for (const comp of release.companies || []) {
    const role = comp.entity_type_name?.toLowerCase() || "";
    if (role.includes("copyright")) {
      copyrights.push(comp.name);
    }
    if (role.includes("phonographic")) {
      phonographicRights.push(comp.name);
    }
  }

  const notes = release.notes || "";

  return {
    contributors,
    album_genres: albumGenres,
    album_styles: albumStyles,
    album_formats: albumFormats,
    release_country: releaseCountry,
    release_year: releaseYear || null,
    labels,
    companies,
    identifiers,
    publishers: Array.from(publishers),
    copyrights,
    phonographic_rights: phonographicRights,
    notes,
  };
}
