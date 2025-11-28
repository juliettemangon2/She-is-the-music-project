// services/shs.js
import "dotenv/config";

const SHS_API_KEY = process.env.SHS_API_KEY;
const SHS_BASE_URL = "https://api.secondhandsongs.com";

const HEADERS = {
  Accept: "application/json",
  ...(SHS_API_KEY ? { "X-API-Key": SHS_API_KEY } : {}),
};

// -------------------------------
// fetch wrapper with safety
// -------------------------------
async function safeFetch(url, params = {}) {
  try {
    const resp = await fetch(url, {
      ...params,
      headers: {
        ...HEADERS,
      },
    });

    if (!resp.ok) return null;
    return await resp.json();
  } catch (err) {
    console.error("SHS fetch error:", err);
    return null;
  }
}

// -------------------------------
// Search for a work
// -------------------------------
async function searchWork(title, artist) {
  const params = new URLSearchParams({
    title,
    format: "json",
  });

  const data = await safeFetch(`${SHS_BASE_URL}/search/work?${params}`, {
    method: "GET",
  });

  if (!data || !Array.isArray(data.resultPage)) return null;

  for (const work of data.resultPage) {
    const uri = work.uri;
    if (!uri) continue;

    const details = await fetchWorkDetails(uri);
    if (!details) continue;

    const performer = details.original?.performer?.name?.toLowerCase();
    if (performer && performer.includes(artist.toLowerCase())) {
      return details;
    }
  }

  return null;
}

// -------------------------------
// Fetch work details
// -------------------------------
async function fetchWorkDetails(uri) {
  return await safeFetch(uri, { method: "GET" });
}

// -------------------------------
// Search performances
// -------------------------------
async function searchPerformances(title, artist) {
  const params = new URLSearchParams({
    title,
    performer: artist,
    format: "json",
  });

  const data = await safeFetch(
    `${SHS_BASE_URL}/search/performance?${params}`,
    { method: "GET" }
  );

  if (!data || !Array.isArray(data.resultPage)) return [];
  return data.resultPage;
}

// -------------------------------
// Combine all derivatives
// -------------------------------
export async function getAllDerivativesFromSHS(artist, title) {
  const derivatives = [];
  const seen = new Set();

  // ---------------------
  // Work-level data
  // ---------------------
  const workDetails = await searchWork(title, artist);

  if (workDetails) {
    for (const category of ["versions", "derivedWorks"]) {
      for (const item of workDetails[category] || []) {
        const uri = item.uri;
        const artistName = item.performer?.name || "Unknown";

        if (uri && artistName !== "Unknown" && !seen.has(uri)) {
          seen.add(uri);
          derivatives.push({
            title: item.title,
            artist: artistName,
            relation_type: category,
            uri,
          });
        }
      }
    }
  }

  // ---------------------
  // Performances
  // ---------------------
  const performances = await searchPerformances(title, artist);

  for (const perf of performances) {
    const uri = perf.uri;
    const artistName = perf.performer?.name || "Unknown";

    if (uri && artistName !== "Unknown" && !seen.has(uri)) {
      seen.add(uri);
      derivatives.push({
        title: perf.title,
        artist: artistName,
        relation_type: "performance",
        uri,
      });
    }
  }

  return derivatives;
}
