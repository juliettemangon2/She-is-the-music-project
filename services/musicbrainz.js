// services/musicbrainz.js
import "dotenv/config";

// MusicBrainz constants
const MB_API_BASE = "https://musicbrainz.org/ws/2";
const USER_AGENT = "SITMApp/0.1 ( juliette.mangon@gmail.com )";
const REQUEST_DELAY = 1100; // ~1.1s to avoid rate limits

// ---- delay helper ----
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ---- wrapper around fetch ----
async function mbFetch(endpoint, params = {}) {
  const url = `${MB_API_BASE}/${endpoint}?${new URLSearchParams({
    fmt: "json",
    ...params,
  })}`;

  await sleep(REQUEST_DELAY);

  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const resp = await fetch(url, {
        headers: {
          "User-Agent": USER_AGENT,
          Accept: "application/json",
        },
      });

      if (resp.ok) return resp.json();

      if ([429, 500, 502, 503, 504].includes(resp.status)) {
        await sleep(500 * attempt);
        continue;
      }

      console.error("MusicBrainz error:", resp.status, await resp.text());
      return null;
    } catch (err) {
      if (attempt === 3) {
        console.error("MusicBrainz fetch failed:", err);
        return null;
      }
      await sleep(500 * attempt);
    }
  }
  return null;
}

// ---- role normalization ----
function normalizeRole(role) {
  return role.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// ----------------------------------------------
// Step 1: Search for recording MBID
// ----------------------------------------------
async function searchRecordingMBID(title, artist) {
  const query = `recording:"${title}" AND artist:"${artist}"`;

  const data = await mbFetch("recording", {
    query,
    limit: "5",
  });

  if (!data || !Array.isArray(data.recordings) || !data.recordings.length) {
    return null;
  }

  return data.recordings[0].id;
}

// ----------------------------------------------
// Step 2: Recording-level contributors
// ----------------------------------------------
async function getRecordingContributors(mbid) {
  const data = await mbFetch(`recording/${mbid}`, {
    inc: "artist-credits+work-rels+recording-rels+artist-rels",
  });

  if (!data) return [];

  const contributors = [];

  for (const rel of data.relations || []) {
    const type = rel.type;
    const valid = [
      "composer",
      "lyricist",
      "writer",
      "arranger",
      "producer",
      "engineer",
    ];

    if (!valid.includes(type)) continue;

    const artistInfo = rel.artist || {};
    const name = artistInfo.name;
    if (!name) continue;

    contributors.push({
      name,
      role: normalizeRole(type),
      scope: "recording",
      source: "musicbrainz",
    });
  }

  return contributors;
}

// ----------------------------------------------
// Step 3: Work metadata (ISWC, writer details)
// ----------------------------------------------
async function getWorkMetadata(title, artist) {
  const query = `work:"${title}" AND artist:"${artist}"`;

  const search = await mbFetch("work", {
    query,
    limit: "1",
  });

  if (!search || !search.works || !search.works.length) {
    return {};
  }

  const work = search.works[0];
  const workId = work.id;
  if (!workId) return {};

  const workData = await mbFetch(`work/${workId}`, {
    inc: "artist-rels+aliases+work-rels",
  });

  if (!workData) return {};

  const iswc = workData.iswc;
  const aliases = (workData.aliases || [])
    .map((a) => a.name)
    .filter(Boolean);

  const contributors = [];

  for (const rel of workData.relations || []) {
    const type = rel.type;
    if (!["composer", "lyricist", "writer"].includes(type)) continue;

    const a = rel.artist || {};
    const name = a.name;
    if (!name) continue;

    contributors.push({
      name,
      role: normalizeRole(type),
      scope: "work",
      source: "musicbrainz",
    });
  }

  const relatedWorks = [];
  for (const rel of workData.relations || []) {
    if (rel.work) {
      relatedWorks.push({
        title: rel.work.title,
        relation_type: rel.type,
        work_id: rel.work.id,
      });
    }
  }

  return {
    iswc,
    aliases,
    contributors,
    related_works: relatedWorks,
  };
}

// ----------------------------------------------
// Main Export
// ----------------------------------------------
export async function getMusicBrainzMetadata(artist, title) {
  const mbid = await searchRecordingMBID(title, artist);
  if (!mbid) return {};

  const recordingContributors = await getRecordingContributors(mbid);
  const workMetadata = await getWorkMetadata(title, artist);

  const contributors = [
    ...recordingContributors,
    ...(workMetadata.contributors || []),
  ];

  return {
    contributors,
    publishing: {
      iswc: workMetadata.iswc,
      aliases: workMetadata.aliases,
      related_works: workMetadata.related_works,
    },
  };
}
