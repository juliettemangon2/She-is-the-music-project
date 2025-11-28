// resolvers/flags.js

// Determine whether roles indicate a writer in Discogs
function isDiscogsWriter(role = "") {
  const r = role.toLowerCase();
  return r.includes("songwriter") || r.includes("lyrics");
}

// Determine whether MB role is a writer
function isMBWriter(role) {
  return ["Composer", "Lyricist", "Writer"].includes(role);
}

export function generateInsightFlags(artist, title, rightsholders, discogsData, musicbrainzData) {
  const flags = [];

  // -------------------------------------------
  // 1. Conflicting contributor information
  // -------------------------------------------
  const discogsWriters = new Set();
  const mbWriters = new Set();

  // Discogs writers
  for (const c of discogsData?.contributors || []) {
    if (isDiscogsWriter(c.role)) {
      discogsWriters.add(c.name);
    }
  }

  // MusicBrainz writers
  for (const c of musicbrainzData?.contributors || []) {
    if (isMBWriter(c.role)) {
      mbWriters.add(c.name);
    }
  }

  if (discogsWriters.size > 0 && mbWriters.size > 0) {
    const discogsList = Array.from(discogsWriters);
    const mbList = Array.from(mbWriters);

    // If sets differ
    const conflict =
      discogsList.length !== mbList.length ||
      discogsList.some((x) => !mbWriters.has(x));

    if (conflict) {
      flags.push({
        type: "conflicting_info",
        message: "Contributor information differs between Discogs and MusicBrainz",
        details: {
          discogs: discogsList,
          musicbrainz: mbList,
        },
      });
    }
  }

  // -------------------------------------------
  // 2. Missing publisher info
  // -------------------------------------------
  const discogsPublishers = discogsData?.publishers || [];
  const mbPublishers =
    musicbrainzData?.publishing?.publishers || []; // may be undefined in your current MB logic

  if (discogsPublishers.length === 0 && mbPublishers.length === 0) {
    flags.push({
      type: "missing_publisher",
      message: "Publisher information missing",
    });
  }

  return {
    artist,
    title,
    flags,
  };
}
